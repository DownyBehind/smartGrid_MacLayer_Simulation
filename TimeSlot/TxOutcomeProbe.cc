#include "TxOutcomeProbe.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/common/Simsignals.h"
#include <cstring>

/* ── IEEE-802.11 헤더가 있을 때만 include (INET 버전 호환) ─────────── */
#if __has_include("inet/linklayer/ieee80211/mac/ieee80211SubtypeTag_m.h")
  #define HAS_IEEE_SUBTYPE 1
  #include "inet/linklayer/ieee80211/mac/ieee80211SubtypeTag_m.h"
#else
  #define HAS_IEEE_SUBTYPE 0
#endif
#if __has_include("inet/linklayer/ieee80211/mac/Ieee80211MacHeader_m.h")
  #define HAS_IEEE_MACHEAD 1
  #include "inet/linklayer/ieee80211/mac/Ieee80211MacHeader_m.h"
#else
  #define HAS_IEEE_MACHEAD 0
#endif

Define_Module(TxOutcomeProbe);

/* ---------- 도움 함수: ACK 프레임 판별 ---------- */
static bool isAckPkt(const inet::Packet *pk)
{
#if HAS_IEEE_SUBTYPE
    if (auto ind = pk->findTag<inet::ieee80211::Ieee80211SubtypeInd>())
        return ind->getSubtype() == inet::ieee80211::ST_ACK;
#endif
#if HAS_IEEE_MACHEAD
    auto hdr = pk->peekAtFront<inet::ieee80211::Ieee80211MacHeader>();
    if (hdr && hdr->getType() == inet::ieee80211::ST_ACK) return true;
#endif
    auto has = [](const char *s){ return strstr(s,"Ack")||strstr(s,"ACK")||strstr(s,"ack"); };
    return has(pk->getName()) || has(pk->getClassName());
}

/* ---------- 초기화 ---------- */
void TxOutcomeProbe::initialize()
{
    /* 파라미터 읽기 */
    targetNodePath = par("targetNodePath").stdstringValue();
    wlanIndex      = par("wlanIndex");
    sifs           = par("sifs");
    cifs           = par("cifs");
    ackTxTime      = par("ackTxTime");
    ackTimeout     = par("ackTimeout");
    slotTime       = par("slotTime");          // ★ 추가
    debugSignals   = par("debugSignals").boolValue();
    debugMaxLines  = par("debugMaxLines");

    /* 타이머 생성 */
    ackWait = new cMessage("ackWait"); take(ackWait);

    attach();
}

/* ---------- 대상 wlan → 시그널 subscribe ---------- */
void TxOutcomeProbe::attach()
{
    /* 노드 찾기 */
    cModule *node = (targetNodePath.empty() || targetNodePath=="^")
                    ? getParentModule()
                    : getSimulation()->findModuleByPath(targetNodePath.c_str());
    if (!node)
        throw cRuntimeError("target node not found: %s", targetNodePath.c_str());

    /* wlan[*] 하위 모듈 */
    cModule *wlan = node->getSubmodule("wlan", wlanIndex);
    if (!wlan) throw cRuntimeError("wlan[%d] not found under %s",
                                   wlanIndex, node->getFullPath().c_str());
    mac   = wlan->getSubmodule("mac");
    radio = wlan->getSubmodule("radio");

    /* 시그널 ID */
    rxFromUpperSig = inet::packetReceivedFromUpperSignal;
    rxFromLowerSig = inet::packetReceivedFromLowerSignal;
    txToUpperSig   = inet::packetSentToUpperSignal;

    mac->subscribe(rxFromUpperSig, this);
    mac->subscribe(rxFromLowerSig, this);
    mac->subscribe(txToUpperSig,   this);
}

/* ---------- 시그널 콜백 ---------- */
void TxOutcomeProbe::receiveSignal(cComponent*, simsignal_t id,
                                   cObject *obj, cObject*)
{
    Enter_Method_Silent();      // 컨텍스트 전환 (scheduleAt 안전)

    /* 디버그 로그 (선택) */
    if (debugSignals && debugMaxLines-- > 0)
        EV_WARN << "[sig] " << cComponent::getSignalName(id)
                << " obj=" << (obj?obj->getClassName():"") << " t="<<simTime()<<endl;

    /* ── 1. TX 시작 (upper→MAC) ── */
    if (id == rxFromUpperSig) {
        if (awaitingAck) {              // 직전 시도 미확정 ⇒ 충돌 간주
            collTime += currentDataTxDur + cifs;
            cancelEvent(ackWait);
        }
        attempts++; awaitingAck = true;

        auto pk = check_and_cast<inet::Packet*>(obj);
        currentDataBits   = pk->getTotalLength().get();
        currentDataTxDur  = currentDataBits / 12e6;   // 12 Mbps 기준 (필요시 INI로)
        scheduleAt(simTime() + currentDataTxDur + sifs + ackTimeout, ackWait);

        return;
    }

    /* ── 2. ACK 수신 (radio→MAC) ── */
    if (id == rxFromLowerSig && awaitingAck) {
        auto pk = dynamic_cast<const inet::Packet*>(obj);
        if (pk && isAckPkt(pk)) {
            succs++;
            succTime += currentDataTxDur + sifs + ackTxTime;
            cancelEvent(ackWait); awaitingAck = false;
        }
        return;
    }

    /* ── 3. 무ACK 모드 성공 (MAC→upper) ── */
    if (id == txToUpperSig && !awaitingAck) {
        succs++;
    }
}

/* ---------- 타임아웃 → 충돌 ---------- */
void TxOutcomeProbe::handleMessage(cMessage *msg)
{
    if (msg == ackWait && awaitingAck) {
        collTime += currentDataTxDur + cifs;
        awaitingAck = false;
    }
}

/* ---------- 스칼라 기록 ---------- */
void TxOutcomeProbe::finish()
{
    recordScalar("ts_success_time", succTime.dbl());
    recordScalar("tc_collision_time", collTime.dbl());

    if (slotTime > 0) {
        recordScalar("ns_success_slots", succTime.dbl() / slotTime);
        recordScalar("nc_collision_slots", collTime.dbl() / slotTime);
    }
}

/* ---------- intval_t 시그널 (사용 안함) ---------- */
void TxOutcomeProbe::receiveSignal(cComponent*, simsignal_t, intval_t, cObject*) { }

/* ---------- 소멸자 ---------- */
TxOutcomeProbe::~TxOutcomeProbe()
{
    cancelAndDelete(ackWait);
}
