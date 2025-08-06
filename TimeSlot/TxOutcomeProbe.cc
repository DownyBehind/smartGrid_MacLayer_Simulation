// project_smartCharging_macLayer_improvement/TimeSlot/TxOutcomeProbe.cc
#include "TxOutcomeProbe.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/linklayer/base/MacProtocolBase.h"
#include "inet/common/Simsignals.h"   // 전역 시그널 심볼들
#include <cstring>

#if __has_include("inet/physicallayer/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/contract/packetlevel/IRadio.h"
#elif __has_include("inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h"
#elif __has_include("inet/physicallayer/contract/IRadio.h")
  #include "inet/physicallayer/contract/IRadio.h"
#else
  #include "inet/physicallayer/wireless/common/contract/IRadio.h"
#endif

// ── 802.11 헤더/태그: INET 버전에 따라 파일명이 다름 → 순차 체크
#if __has_include("inet/linklayer/ieee80211/mac/Ieee80211MacHeader_m.h")
  #define HAS_IEEE80211_MACHEADER 1
  #include "inet/linklayer/ieee80211/mac/Ieee80211MacHeader_m.h"
#endif
#if __has_include("inet/linklayer/ieee80211/mac/ieee80211Frame_m.h")
  #define HAS_IEEE80211_FRAME 1
  #include "inet/linklayer/ieee80211/mac/ieee80211Frame_m.h"
#endif
#if __has_include("inet/linklayer/ieee80211/mac/ieee80211SubtypeTag_m.h")
  #define HAS_IEEE80211_SUBTYPE_TAG 1
  #include "inet/linklayer/ieee80211/mac/ieee80211SubtypeTag_m.h"
#endif

Define_Module(TxOutcomeProbe);

void TxOutcomeProbe::initialize() {
    targetNodePath = par("targetNodePath").stdstringValue();
    wlanIndex = par("wlanIndex");
    sifs = par("sifs").doubleValue();
    cifs = par("cifs").doubleValue();
    ackTxTime  = par("ackTxTime").doubleValue();
    ackTimeout = par("ackTimeout").doubleValue();
    attach();

    // ★ 소유권 명시 (스케줄 전 take)
    ackWait = new cMessage("ackWait");
    take(ackWait);
}

void TxOutcomeProbe::attach() {
    // targetNodePath가 ".host[0]" 같은 상대경로면 루트에 붙여 절대경로로 만듦
    std::string p = targetNodePath;
    if (!p.empty() && p[0] == '.') {
        p = getSimulation()->getSystemModule()->getFullPath() + p; // "Root.host[0]"
    }
    cModule *node = getSimulation()->findModuleByPath(p.c_str());
    if (!node)
        throw cRuntimeError("targetNodePath not found: '%s' (resolved: '%s')",
                            targetNodePath.c_str(), p.c_str());

    cModule *wlan = node->getSubmodule("wlan", wlanIndex);
    if (!wlan) throw cRuntimeError("wlan[%d] not found", wlanIndex);
    radio = wlan->getSubmodule("radio");
    mac   = wlan->getSubmodule("mac");
    if (!radio || !mac) throw cRuntimeError("radio/mac not found");

    // 1) 라디오 TX 상태 구독 → TX 구간 측정
    txStateSig = inet::physicallayer::IRadio::transmissionStateChangedSignal;
    radio->subscribe(txStateSig, this);

    // 2) MAC 하위수신(ACK 프레임 탐지) — 전역 시그널
    rxFromLowerSig = inet::packetReceivedFromLowerSignal;
    mac->subscribe(rxFromLowerSig, this);

    // 3) 일부 모듈/버전에서 제공하는 "성공" 시그널 이름 (있으면 자동 연결)
    try { mac->subscribe("ackReceived", this); } catch(...) {}
    try { mac->subscribe("txSuccess", this); } catch(...) {}
    try { mac->subscribe("transmissionSuccessful", this); } catch(...) {}
}

void TxOutcomeProbe::receiveSignal(cComponent *, simsignal_t id, long l, cObject *) {
    // ★ 모듈 컨텍스트 진입 (필수)
    Enter_Method_Silent();

    if (id == txStateSig) {
        auto st = static_cast<inet::physicallayer::IRadio::TransmissionState>(l);
        if (st == inet::physicallayer::IRadio::TRANSMISSION_STATE_TRANSMITTING) onTxStart();
        else if (inTx && st == inet::physicallayer::IRadio::TRANSMISSION_STATE_IDLE) onTxEnd();
    }
}


void TxOutcomeProbe::receiveSignal(cComponent *src, simsignal_t id, cObject *obj, cObject *) {
    // ★ 모듈 컨텍스트 진입 (필수)
    Enter_Method_Silent();

    // 이름 기반 성공 시그널이 들어오면 즉시 성공 처리
    if (src == mac) {
        const char* sigName = cComponent::getSignalName(id);
        if (sigName && (std::strcmp(sigName,"ackReceived")==0 ||
                        std::strcmp(sigName,"txSuccess")==0 ||
                        std::strcmp(sigName,"transmissionSuccessful")==0)) {
            onAckReceived();
            return;
        }
    }

    if (id != rxFromLowerSig) return;

    auto pk = dynamic_cast<inet::Packet*>(obj);
    if (!pk) return;

    bool isAck = false;

    // 1) 태그 기반
    #if defined(HAS_IEEE80211_SUBTYPE_TAG)
    if (auto ind = pk->findTag<inet::ieee80211::Ieee80211SubtypeInd>())
        if (ind->getSubtype() == inet::ieee80211::ST_ACK)
            isAck = true;
    #endif

    // 2) 헤더 기반
    #if defined(HAS_IEEE80211_MACHEADER)
    if (!isAck) {
        const auto& mh = pk->peekAtFront<inet::ieee80211::Ieee80211MacHeader>();
        if (mh != nullptr && mh->getType() == inet::ieee80211::ST_ACK)
            isAck = true;
    }
    #endif
    #if defined(HAS_IEEE80211_FRAME)
    if (!isAck) {
        const auto& mh2 = pk->peekAtFront<inet::ieee80211::Ieee80211MacHeader>();
        if (mh2 != nullptr && mh2->getType() == inet::ieee80211::ST_ACK)
            isAck = true;
    }
    #endif

    // 3) 클래스/패킷명 Fallback
    if (!isAck) {
        std::string cn = pk->getClassName();
        std::string nm = pk->getName();
        auto hasAck = [](const std::string& s){
            return s.find("Ack")!=std::string::npos || s.find("ACK")!=std::string::npos;
        };
        if (hasAck(cn) || hasAck(nm)) isAck = true;
    }

    if (isAck) onAckReceived();
}


void TxOutcomeProbe::onTxStart() {
    if (!inTx) {
        inTx = true;
        awaitingAck = false;
        txStart = simTime();
        attempts++;
    }
}

void TxOutcomeProbe::onTxEnd() {
    if (!inTx) return;
    inTx = false;
    txEnd = simTime();

    // ACK 대기 시작
    simtime_t wait = (ackTimeout > 0) ? ackTimeout : (sifs + ackTxTime);
    if (!ackWait->isScheduled()) {
        awaitingAck = true;
        scheduleAt(txEnd + wait, ackWait);
    }
}

void TxOutcomeProbe::onAckReceived() {
    if (!awaitingAck) return;
    // 성공: TX 종료 시각 기준 SIFS + ACK 시간 포함 (논문 T_S 근사)
    succTime += (txEnd - txStart) + sifs + ackTxTime;
    succs++;
    if (ackWait->isScheduled()) cancelEvent(ackWait);
    awaitingAck = false;
}

void TxOutcomeProbe::onAckTimeout() {
    if (!awaitingAck) return;
    // 실패/충돌: TX 종료 시각 기준 CIFS 포함 (논문 T_C 근사)
    collTime += (txEnd - txStart) + cifs;
    awaitingAck = false;
}

void TxOutcomeProbe::handleMessage(cMessage *msg) {
    if (msg == ackWait) onAckTimeout();
}

void TxOutcomeProbe::finish() {
    recordScalar("ts_success_time", succTime.dbl());
    recordScalar("tc_collision_time", collTime.dbl());
    recordScalar("tx_attempts", attempts);
    recordScalar("succ_pkts",   succs);
}
