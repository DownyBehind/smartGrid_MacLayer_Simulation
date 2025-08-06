// project_smartCharging_macLayer_improvement/TimeSlot/TxOutcomeProbe.cc
#include "TxOutcomeProbe.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/linklayer/base/MacProtocolBase.h"
#include "inet/common/Simsignals.h"   // ★ 전역 시그널 심볼들
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
    ackWait = new cMessage("ackWait");
}

void TxOutcomeProbe::attach() {
    std::string p = targetNodePath;
    if (!p.empty() && p[0] == '.') {
        p = getSimulation()->getSystemModule()->getFullPath() + p;
    }
    cModule *node = getSimulation()->findModuleByPath(p.c_str());
    if (!node)
        throw cRuntimeError("targetNodePath not found: '%s' (resolved: '%s')",
                           targetNodePath.c_str(), p.c_str());
    if (!node) throw cRuntimeError("targetNodePath not found: %s", targetNodePath.c_str());
    cModule *wlan = node->getSubmodule("wlan", wlanIndex);
    if (!wlan) throw cRuntimeError("wlan[%d] not found", wlanIndex);
    radio = wlan->getSubmodule("radio");
    mac   = wlan->getSubmodule("mac");
    if (!radio || !mac) throw cRuntimeError("radio/mac not found");

    // 1) 라디오 TX 상태 구독 → TX 구간 측정
    txStateSig = inet::physicallayer::IRadio::transmissionStateChangedSignal;
    radio->subscribe(txStateSig, this);

    // 2) MAC 하위수신(ACK 프레임 탐지)
    //    전역 심볼: inet/common/Simsignals.h
    rxFromLowerSig = inet::packetReceivedFromLowerSignal;
    mac->subscribe(rxFromLowerSig, this);
}

void TxOutcomeProbe::receiveSignal(cComponent *, simsignal_t id, long l, cObject *) {
    if (id == txStateSig) {
        auto st = static_cast<inet::physicallayer::IRadio::TransmissionState>(l);
        if (st == inet::physicallayer::IRadio::TRANSMISSION_STATE_TRANSMITTING) onTxStart();
        else if (inTx && st == inet::physicallayer::IRadio::TRANSMISSION_STATE_IDLE) onTxEnd();
    }
}

void TxOutcomeProbe::receiveSignal(cComponent *, simsignal_t id, cObject *obj, cObject *) {
    if (id != rxFromLowerSig) return;

    auto pk = dynamic_cast<inet::Packet*>(obj);
    if (!pk) return;

    bool isAck = false;

    // 1) 구버전/일부 버전: Ieee80211MacHeader 존재 시
    #if defined(HAS_IEEE80211_MACHEADER)
    if (!isAck) {
        const auto& mh = pk->peekAtFront<inet::ieee80211::Ieee80211MacHeader>();
        if (mh != nullptr && mh->getType() == inet::ieee80211::ST_ACK)
            isAck = true;
    }
    #endif

    // 2) 현행(네 트리): ieee80211Frame_m.h 사용 시
    #if defined(HAS_IEEE80211_FRAME)
    if (!isAck) {
        const auto& mh2 = pk->peekAtFront<inet::ieee80211::Ieee80211MacHeader>();
        if (mh2 != nullptr && mh2->getType() == inet::ieee80211::ST_ACK)
            isAck = true;
    }
    #endif

    // 3) 태그 기반: ieee80211SubtypeTag_m.h (Ind/Req 중 수신이면 보통 Ind)
    #if defined(HAS_IEEE80211_SUBTYPE_TAG)
    if (!isAck) {
        auto ind = pk->findTag<inet::ieee80211::Ieee80211SubtypeInd>();
        if (ind && ind->getSubtype() == inet::ieee80211::ST_ACK)
            isAck = true;
    }
    #endif

    if (isAck)
        onAckReceived();
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
    // 성공: TX 종료 시각 기준 SIFS + ACK 시간 포함
    succTime += (txEnd - txStart) + sifs + ackTxTime;
    succs++;
    if (ackWait->isScheduled()) cancelEvent(ackWait);
    awaitingAck = false;
}

void TxOutcomeProbe::onAckTimeout() {
    if (!awaitingAck) return;
    // 실패/충돌: TX 종료 시각 기준 CIFS 포함(필요시 값 조정)
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
