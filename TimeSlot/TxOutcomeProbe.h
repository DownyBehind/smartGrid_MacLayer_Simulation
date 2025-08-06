// project_smartCharging_macLayer_improvement/TimeSlot/TxOutcomeProbe.h
#pragma once
#include <omnetpp.h>

// INET 버전에 따라 IRadio.h 경로가 다름 → 안전하게 순차 체크
#if __has_include("inet/physicallayer/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/contract/packetlevel/IRadio.h"
#elif __has_include("inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h"
#elif __has_include("inet/physicallayer/contract/IRadio.h")
  #include "inet/physicallayer/contract/IRadio.h"
#else
  #include "inet/physicallayer/wireless/common/contract/IRadio.h"
#endif

using namespace omnetpp;
using namespace inet;

class TxOutcomeProbe : public cSimpleModule, public cListener {
  protected:
    std::string targetNodePath;
    int wlanIndex = 0;
    double sifs=0, cifs=0, ackTxTime=0, ackTimeout=0;

    cModule *radio = nullptr;
    cModule *mac   = nullptr;

    simsignal_t txStateSig = SIMSIGNAL_NULL;
    simsignal_t rxFromLowerSig = SIMSIGNAL_NULL; // MAC 하위수신(ACK 탐지)

    bool inTx = false;
    bool awaitingAck = false;
    simtime_t txStart;
    simtime_t txEnd;      // TX 종료 시간(ACK/CIFS 보정에 사용)

    cMessage *ackWait = nullptr;

    // 누적
    simtime_t succTime = SIMTIME_ZERO;
    simtime_t collTime = SIMTIME_ZERO;
    long attempts = 0;
    long succs = 0;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual void receiveSignal(cComponent *src, simsignal_t id, long l, cObject *details) override;
    virtual void receiveSignal(cComponent *src, simsignal_t id, cObject *obj, cObject *details) override;

    void attach();
    void onTxStart();
    void onTxEnd();
    void onAckReceived();
    void onAckTimeout();

    virtual ~TxOutcomeProbe() override { cancelAndDelete(ackWait); }
};
