#ifndef __CSMA_CA_HPGP_HPGPMAC_H
#define __CSMA_CA_HPGP_HPGPMAC_H

#include <omnetpp.h>
#include <vector>
#include <map>

using namespace omnetpp;

/**
 * HomePlug Green PHY (HPGP) MAC Layer
 * Implements CSMA/CA with priority-based access
 */
class HpgpMac : public cSimpleModule
{
  public:
    enum Priority {
        CAP0 = 0,
        CAP1 = 1,
        CAP2 = 2,
        CAP3 = 3
    };

  protected:
    // MAC parameters
    int cwMin;
    int cwMax;
    int maxRetries;
    simtime_t slotTime;
    simtime_t sifs;
    simtime_t difs;
    
    // Priority-specific parameters
    std::map<Priority, int> capCwMin;
    std::map<Priority, int> capCwMax;
    
    // MAC state
    int backoffCounter;
    int deferralCounter;
    int backoffProcedureCounter;
    std::vector<cMessage*> txQueue;
    cMessage* pendingTx;
    cMessage* backoffTimer;
    cMessage* deferralTimer;
    
    // Statistics
    simsignal_t txAttemptsSignal;
    simsignal_t txSuccessSignal;
    simsignal_t txCollisionSignal;
    simsignal_t txDropSignal;
    
    // Channel state
    bool channelBusy;
    simtime_t lastChannelActivity;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
    virtual void finish() override;
    
    // MAC protocol methods
    void enqueueFrame(cMessage* frame);
    void processTxQueue();
    void startBackoff();
    void startDeferral();
    void attemptTransmission();
    void onTransmissionComplete(bool success);
    void onCollision();
    
    // Helper methods
    int getCw(Priority priority);
    Priority getFramePriority(cMessage* frame);
    simtime_t getFrameDuration(cMessage* frame);
    bool isChannelIdle();
    void updateChannelState(bool busy);
    
    // Statistics
    void emitTxAttempt();
    void emitTxSuccess();
    void emitTxCollision();
    void emitTxDrop();
};

#endif
