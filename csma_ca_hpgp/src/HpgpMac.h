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
    
    // Logging parameters
    bool recordTxAttempts;
    bool recordCollisions;
    bool recordSlacMessages;
    bool recordDcCycles;
    
    // Channel state
    bool channelBusy;
    simtime_t lastChannelActivity;
    bool waitingForChannelResponse;
    cMessage* currentFrame;
    
    // SLAC and DC functionality
    std::string nodeType;
    int nodeId;
    bool dcLoopEnabled;
    simtime_t dcPeriod;
    simtime_t dcDeadline;
    simtime_t dcRspDelay;
    simtime_t dcRspJitter;
    int dcReqSeq;
    bool dcStarted;
    cMessage* dcTimer;
    
    // SLAC state
    bool slacStarted;
    int slacTryId;
    simtime_t slacStartTime;
    cMessage* slacTimer;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
    virtual void finish() override;
    
    // MAC protocol methods
    void enqueueFrame(cMessage* frame);
    
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
    
    // SLAC and DC methods
    void startSlac();
    void startDcLoop();
    void sendSlacMessage(const char* msgType);
    void sendDcRequest();
    void onSlacDone(bool success);
    void onDcTimeout();
    void handleDcRequest(cMessage* msg);
    void handleSlacMessage(cMessage* msg);
    void logMacTx(int kind, int bits, simtime_t startTime, simtime_t endTime, bool success, int attempts, int bpc, int bc);
    void logDcCycle(int seq, simtime_t reqTime, simtime_t rspTime, simtime_t rtt, bool missFlag, bool gapViolation, int retries, int segFrames);
    void logSlacAttempt(int tryId, simtime_t startTime, simtime_t endTime, bool success, simtime_t connTime, int msgTimeouts, bool procTimeout, int retries);
    
    // Actual SLAC Protocol Implementation
    void startSlacSequence();
    void processSlacSequence();
    
    // HPGP MAC Protocol Implementation
    void processMacSlot();
    void startPriorityResolution();
    void processPriorityResolution();
    void onPriorityResolutionComplete();
    void attemptTransmission();
    void onTransmissionComplete(bool success);
    void onCollision();
    void processAck();
};

#endif