#ifndef __CSMA_CA_HPGP_SLACAPPLICATION_H
#define __CSMA_CA_HPGP_SLACAPPLICATION_H

#include <omnetpp.h>
#include <string>
#include <map>
#include <set>

using namespace omnetpp;

/**
 * SLAC (Signal Level Attenuation Characterization) Application
 * Implements the SLAC protocol for PLC communication
 */
class SlacApplication : public cSimpleModule
{
  public:
    enum SlacMessageType {
        SLAC_PARM_REQ = 1,
        SLAC_PARM_CNF = 2,
        START_ATTEN = 3,
        MNBC_SOUND = 4,
        ATTEN_CHAR_IND = 5,
        ATTEN_CHAR_RSP = 6,
        SLAC_MATCH_REQ = 7,
        SLAC_MATCH_CNF = 8,
        DC_CUR_DEM_REQ = 9,
        DC_CUR_DEM_RSP = 10
    };

  protected:
    // Module parameters
    std::string nodeType;  // "EV" or "EVSE"
    int nodeId;
    simtime_t slacMsgTimeout;
    simtime_t slacProcTimeout;
    int slacMaxRetry;
    simtime_t slacRetryBackoff;
    
    // SLAC state
    bool slacDone;
    bool awaitingResponse;
    SlacMessageType awaitingMessageType;
    int retryCount;
    simtime_t slacStartTime;
    cMessage* processTimeout;
    cMessage* messageTimeout;
    
    // DC loop state
    bool dcLoopEnabled;
    simtime_t dcPeriod;
    simtime_t dcDeadline;
    simtime_t dcRspDelay;
    simtime_t dcRspJitter;
    bool dcStarted;
    int dcReqSeq;
    simtime_t lastReqTime;
    std::map<int, simtime_t> pendingResponses;
    
    // SLAC detailed parameters
    int nStartAtten;
    int nMsound;
    simtime_t gapStart;
    simtime_t gapMsound;
    simtime_t delayEvseRsp;
    simtime_t gapAttn;
    simtime_t gapMatch;
    
    // Statistics
    simsignal_t slacCompleteSignal;
    simsignal_t slacRetriesSignal;
    simsignal_t slacTimeoutSignal;
    simsignal_t dcTimeoutSignal;
    simsignal_t dcGapViolationSignal;
    simsignal_t dcRttSignal;
    
    // Received messages tracking
    std::set<SlacMessageType> receivedMessages;
    
    // Logging parameters
    bool recordSlacMessages;
    bool recordDcCycles;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
    virtual void finish() override;
    
    // SLAC protocol methods
    void startSlac();
    void sendSlacMessage(SlacMessageType type, int bits);
    void handleSlacResponse(SlacMessageType type);
    void onSlacDone(bool success);
    void failAndMaybeRetry(const std::string& reason);
    void resetForRetry();
    
    // DC loop methods
    void startDcLoop();
    void sendDcRequest();
    void handleDcResponse(int seq);
    
    // Logging methods
    void logMacTx(int kind, int bits, simtime_t startTime, simtime_t endTime, bool success, int attempts, int bpc, int bc);
    void logDcCycle(int seq, simtime_t reqTime, simtime_t rspTime, simtime_t rtt, bool missFlag, bool gapViolation, int retries, int segFrames);
    void logSlacAttempt(int tryId, simtime_t startTime, simtime_t endTime, bool success, simtime_t connTime, int msgTimeouts, bool procTimeout, int retries);
    simtime_t getFrameDuration(cMessage* frame);
    
    // Helper methods
    void scheduleMessageTimeout(SlacMessageType expectedType);
    void cancelMessageTimeout();
    void scheduleProcessTimeout();
    void cancelProcessTimeout();
    simtime_t getRandomJitter();
    
    // Statistics
    void emitSlacComplete(simtime_t completionTime);
    void emitSlacRetries(int retryCount);
    void emitSlacTimeout();
    
    // Message priority
    int getMessagePriority(SlacMessageType type);
};

#endif

