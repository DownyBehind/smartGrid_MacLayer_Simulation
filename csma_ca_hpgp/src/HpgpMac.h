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
    
    // DC job tracking for transmission completion
    int lastTransmittedDcJobId;
    bool waitingForChannelResponse;
    cMessage* currentFrame;
    enum LastTxType { TX_NONE = 0, TX_DC_REQ = 1, TX_DC_RSP = 2 };
    LastTxType lastTxType;
    void* lastTxCtx;   // For REQ: DcJob* (this module); For RSP: DcJob* (EV side) carried through
    int lastTxSeq;
    
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
    bool looseResponseMatching; // INI 토글: 느슨한 응답 매칭
    
    // SLAC state management
    int slacStep;
    bool slacCompleted;
    // cMessage* dcTimer; // removed; deadlines handled via jobDeadline messages
    
    // DC Job Management System
    enum JobState {
        PENDING = 0,      // Job released but not yet transmitted
        REQ_SENT = 1,     // Request transmitted successfully
        RES_RECEIVED = 2, // Response received
        MISSED = 3        // Job missed deadline
    };
    
    enum MissType {
        M0_NO_REQ = 0,    // No request sent in window
        M1_REQ_FAIL = 1,  // Request transmission failed
        M2_RES_MISS = 2,  // Response missed
        M3_RES_LATE = 3   // Response late
    };
    
    struct DcJob {
        int jobId;                    // Job sequence number
        simtime_t releaseTime;        // R_k^i = T_SLAC^i + k·100ms
        simtime_t windowStart;        // Window start time
        simtime_t windowEnd;          // Window end time
        simtime_t deadline;           // Deadline time
        JobState state;               // Current job state
        int seq;                      // Request sequence number
        simtime_t reqTime;            // Request transmission time
        simtime_t resTime;            // Response reception time
        MissType missType;            // Miss type if missed
        simtime_t tardiness;          // Tardiness if late
        
        // MAC 경쟁 지연 반영을 위한 계측 포인트
        simtime_t enq_req;            // Request enqueue time (큐 투입 시각)
        simtime_t txStart_req;        // Request transmission start time (전송 시작 시각)
        simtime_t txEnd_req;          // Request transmission end time (전송 종료 시각)
        simtime_t rxStart_rsp;        // Response reception start time (수신 시작 시각)
        simtime_t rxEnd_rsp;          // Response reception end time (수신 종료 시각)
        simtime_t enq_rsp;            // Response enqueue time (응답 큐 투입 시각, 진단용)
        int reqTxAttempts;            // 송신 시도 횟수 (성공/실패 포함)
    };
    
    std::vector<DcJob> dcJobs;       // Job queue
    int nextJobId;                   // Next job ID
    simtime_t slacCompletionTime;    // T_SLAC^i
    cMessage* jobTimer;              // Job processing timer
    
    // SLAC state
    bool slacStarted;
    int slacTryId;
    simtime_t slacStartTime;
    cMessage* slacTimer;
    cMessage* startSlacMsg;

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
    // void onDcTimeout(); // removed: deadlines handled by jobDeadline
    void handleDcRequest(cMessage* msg);
    void handleSlacMessage(cMessage* msg);
    void logMacTx(int kind, int bits, simtime_t startTime, simtime_t endTime, bool success, int attempts, int bpc, int bc);
    void logDcCycle(int seq, simtime_t reqTime, simtime_t rspTime, simtime_t rtt, bool missFlag, bool gapViolation, int retries, int segFrames);
    void logSlacAttempt(int tryId, simtime_t startTime, simtime_t endTime, bool success, simtime_t connTime, int msgTimeouts, bool procTimeout, int retries);
    
    // DC Job Management System
    void createDcJob(int jobId, simtime_t releaseTime);
    void processDcJobs();
    void processJob(DcJob& job);
    void sendDcRequestForJob(DcJob& job);
    void onDcRequestSent(DcJob& job);
    void onDcResponseReceived(DcJob& job, simtime_t responseTime);
    DcJob* findEarliestPendingReqSentJob();
    void onJobMissed(DcJob& job, MissType missType);
    void logJobEvent(const DcJob& job, const char* event);
    void logJobMiss(const DcJob& job, MissType missType);
    
    // Actual SLAC Protocol Implementation
    void startSlacSequence();
    void processSlacSequence();
    bool isSlacMessage(const char* msgName);
    
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