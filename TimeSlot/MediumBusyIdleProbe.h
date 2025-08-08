#pragma once
#include <omnetpp.h>

// INET 버전별 IRadio.h 경로 대응
#if __has_include("inet/physicallayer/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/contract/packetlevel/IRadio.h"
#elif __has_include("inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h")
  #include "inet/physicallayer/wireless/common/contract/packetlevel/IRadio.h"
#else
  #include "inet/physicallayer/contract/IRadio.h"
#endif

using namespace omnetpp;
using namespace inet;

/** 802.11 채널의 Idle/Busy 슬롯 수를 누적하는 Probe */
class MediumBusyIdleProbe : public cSimpleModule, public cListener
{
  protected:
    std::string targetNodePath;
    int         wlanIndex   = 0;
    double      slotTime    = 0.0;            // 1 slot = 9 μs (INI/NED)

    simsignal_t rxStateSig  = SIMSIGNAL_NULL;
    cModule    *radio       = nullptr;

    inet::physicallayer::IRadio::ReceptionState lastRxState;
    simtime_t  lastChange;
    simtime_t  idleAcc = SIMTIME_ZERO;
    simtime_t  busyAcc = SIMTIME_ZERO;

  protected:
    virtual void initialize() override;
    virtual void finish() override;
    virtual void handleMessage(cMessage *msg) override {}
    virtual void receiveSignal(cComponent *, simsignal_t,
                               long l, cObject *) override;
    void attach();
};
