// project_smartCharging_macLayer_improvement/TimeSlot/MediumBusyIdleProbe.h
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

class MediumBusyIdleProbe : public cSimpleModule, public cListener {
  protected:
    std::string targetNodePath;
    int wlanIndex = 0;
    simsignal_t rxStateSig = SIMSIGNAL_NULL;
    cModule *radio = nullptr;

    inet::physicallayer::IRadio::ReceptionState lastRxState;
    simtime_t lastChange;
    double slotTime = 0.0;

    simtime_t idleAcc = SIMTIME_ZERO;
    simtime_t busyAcc = SIMTIME_ZERO;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override {}
    virtual void finish() override;

    virtual void receiveSignal(cComponent *src, simsignal_t id, long l, cObject *details) override;
    void attach();
};
