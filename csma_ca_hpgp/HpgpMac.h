#ifndef __CSMA_CA_HPGP_HPGPMAC_H
#define __CSMA_CA_HPGP_HPGPMAC_H

#include <omnetpp.h>
#include <vector>
#include <map>
#include <queue>

using namespace omnetpp;

/**
 * HomePlug 1.0 MAC Layer
 * Implements Priority Resolution + BPC/DC/BC based CSMA/CA
 * Based on Table I parameters from Jung et al. (2005)
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
    
    enum PriorityGroup {
        CA01 = 0,  // CA0, CA1 (저우선순위 그룹)
        CA23 = 1   // CA2, CA3 (고우선순위 그룹)
    };

  protected:
    // MAC parameters - HomePlug 1.0 standard
    simtime_t cifs;      // 35.84us
    simtime_t rifs;      // 26us
    simtime_t prs0;      // 35.84us
    simtime_t prs1;      // 35.84us
    simtime_t slotTime;  // 35.84us
    int bpcMax;          // 4
    
    // Priority group
    PriorityGroup priorityGroup;
    
    // Table I parameters (BPC -> DC, CW)
    struct TableIParams {
        int dc;
        int cw;
    };
    std::map<int, TableIParams> tableICA01;  // CA0, CA1 group
    std::map<int, TableIParams> tableICA23;  // CA2, CA3 group
    
    // MAC state - HomePlug 1.0 BPC/DC/BC model
    int bpc;             // Backoff Procedure Counter
    int dc;              // Deferral Counter
    int bc;              // Backoff Counter
    int cw;              // Current contention window
    std::queue<cMessage*> txQueue;
    cMessage* slotTimer; // Main slot timer
    
    // Priority Resolution state
    bool inPriorityResolution;
    int priorityResolutionSlot;
    Priority currentPriority;
    cMessage* priorityResolutionTimer;
    
    // Statistics
    simsignal_t txAttemptsSignal;
    simsignal_t txSuccessSignal;
    simsignal_t txCollisionSignal;
    simsignal_t txDropSignal;
    
    // Channel state
    bool channelBusy;
    simtime_t lastChannelActivity;
    bool waitingForChannelResponse;
    cMessage* currentFrame;

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
    
    // Priority Resolution methods
    void startPriorityResolution();
    void processPriorityResolution();
    void onPriorityResolutionComplete();
    
    // HomePlug 1.0 Table I methods
    void setStageByBpc(int newBpc);
    TableIParams getTableIParams(int bpc);
    void initializeTableI();
    
    // Helper methods
    Priority getFramePriority(cMessage* frame);
    simtime_t getFrameDuration(cMessage* frame);
    bool isChannelIdle();
    bool senseChannelBusy();
    bool tryTransmitFrame();
    void updateChannelState(bool busy);
    
    // Statistics
    void emitTxAttempt();
    void emitTxSuccess();
    void emitTxCollision();
    void emitTxDrop();
};

#endif