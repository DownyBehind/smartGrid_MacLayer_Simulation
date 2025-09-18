#include "HpgpMac.h"

Define_Module(HpgpMac);

void HpgpMac::initialize()
{
    EV << "=== HPGP MAC INITIALIZE ===" << endl;
    EV << "Node ID: " << par("nodeId") << endl;
    EV << "Node Type: " << par("nodeType") << endl;
    
    // Force immediate output
    printf("=== HPGP MAC INITIALIZE ===\n");
    printf("Node ID: %d\n", (int)par("nodeId"));
    printf("Node Type: %s\n", par("nodeType").stringValue());
    fflush(stdout);
    
    // Get HomePlug 1.0 standard parameters
    cifs = par("cifs");        // 35.84us - Contention Inter-Frame Space
    rifs = par("rifs");        // 26us - Response Inter-Frame Space  
    prs0 = par("prs0");        // 35.84us - Priority Resolution Slot 0
    prs1 = par("prs1");        // 35.84us - Priority Resolution Slot 1
    slotTime = par("slotTime"); // 35.84us - Basic slot time
    bpcMax = par("bpcMax");    // 4 - Maximum Backoff Procedure Counter
    
    // Priority group
    std::string groupStr = par("priorityGroup");
    priorityGroup = (groupStr == "CA23") ? CA23 : CA01;
    
    // Initialize Table I parameters
    initializeTableI();
    
    // Initialize state
    bpc = 0;
    dc = 0;
    bc = 0;
    cw = 0;
    channelBusy = false;
    lastChannelActivity = 0;
    waitingForChannelResponse = false;
    currentFrame = nullptr;
    lastTransmittedDcJobId = -1;
    
    // Priority Resolution state
    inPriorityResolution = false;
    priorityResolutionSlot = 0;
    currentPriority = CAP0;
    
    // Create timers
    slotTimer = new cMessage("slotTimer");
    priorityResolutionTimer = new cMessage("priorityResolutionTimer");
    lastTxType = TX_NONE;
    lastTxCtx = nullptr;
    lastTxSeq = -1;
    
    // Initialize with BPC=0
    setStageByBpc(0);
    
    // Register signals
    txAttemptsSignal = registerSignal("txAttempts");
    txSuccessSignal = registerSignal("txSuccess");
    txCollisionSignal = registerSignal("txCollision");
    txDropSignal = registerSignal("txDrop");
    
    // Get logging parameters
    recordTxAttempts = par("recordTxAttempts");
    recordCollisions = par("recordCollisions");
    recordSlacMessages = par("recordSlacMessages");
    recordDcCycles = par("recordDcCycles");
    
    // Get SLAC and DC parameters
    nodeType = par("nodeType").stringValue();
    nodeId = par("nodeId");
    dcLoopEnabled = par("dcLoopEnabled");
    dcPeriod = par("dcPeriod");
    dcDeadline = par("dcDeadline");
    dcRspDelay = par("dcRspDelay");
    dcRspJitter = par("dcRspJitter");
    looseResponseMatching = par("looseResponseMatching");
    
    // Temporary fix: Force enable DC loop for EV nodes to test implementation
    if (nodeType == "EV") {
        dcLoopEnabled = true;
    }
    printf("HpgpMac Node %d (%s): dcLoopEnabled = %d (after override)\n", nodeId, nodeType.c_str(), dcLoopEnabled);
    fflush(stdout);
    
    // Initialize SLAC and DC state
    dcReqSeq = 0;
    dcStarted = false;
    slacStarted = false;
    slacTryId = 0;
    slacStartTime = 0;
    slacTimer = nullptr;
    startSlacMsg = nullptr;
    
    // Initialize DC Job Management System
    dcJobs.clear();
    nextJobId = 0;
    slacCompletionTime = 0;
    jobTimer = nullptr;
    
    // Start with PRS0 + PRS1 delay (actual HPGP values)
    simtime_t actualPrs0 = 5.12e-6; // 5.12 microseconds
    simtime_t actualPrs1 = 5.12e-6; // 5.12 microseconds
    scheduleAt(simTime() + actualPrs0 + actualPrs1, slotTimer);
    
    // Initialize logging for testing
    EV << "HpgpMac Node " << nodeId << " (" << nodeType << "): Initialized" << endl;
    EV << "dcLoopEnabled = " << dcLoopEnabled << endl;
    
    // Start actual SLAC and DC processes
    // Start SLAC based on scenario
    if (strcmp(par("scenario"), "WC_A_Sequential") == 0) {
        // WC-A: Sequential SLAC (each node starts at different time)
        double delay = nodeId * 0.1; // 100ms delay between nodes
        startSlacMsg = new cMessage("startSlac");
        scheduleAt(simTime() + delay, startSlacMsg);
    } else if (strcmp(par("scenario"), "WC_B_Simultaneous") == 0) {
        // WC-B: Simultaneous SLAC (all nodes start at same time)
        startSlacMsg = new cMessage("startSlac");
        scheduleAt(simTime() + 0.1, startSlacMsg);
    } else {
        // Default: Start immediately
        if (nodeType == "EVSE") {
            startSlac();
        } else if (nodeType == "EV") {
            startSlac();
        }
    }
    
    // DC loop will start only after SLAC completion in onSlacDone()
}

void HpgpMac::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        if (msg == slotTimer) {
            // HPGP MAC Main Slot Processing
            processMacSlot();
        }
        else if (msg == priorityResolutionTimer) {
            processPriorityResolution();
        } else if (msg == slacTimer) {
            // SLAC timer expired - continue SLAC sequence (no longer used)
            // processSlacSequence();
        } else if (strcmp(msg->getName(), "DC_RSP_ENQUEUE") == 0) {
            // EVSE에서 지연 후 응답 프레임을 실제 MAC 큐로 투입
            cMessage* rsp = static_cast<cMessage*>(msg->getContextPointer());
            if (rsp) {
                printf("[%.3f] HpgpMac Node %d (%s): Enqueueing delayed DC_RESPONSE into MAC queue\n", simTime().dbl(), nodeId, nodeType.c_str());
                fflush(stdout);
                enqueueFrame(rsp);
            }
            delete msg;
            return;
        } else if (strcmp(msg->getName(), "jobRelease") == 0) {
            // Create job for current k and schedule next release
            int jobId = (int)((simTime() - slacCompletionTime) / dcPeriod);
            createDcJob(jobId, simTime());
            // Immediately attempt to send DC request for this newly created job
            if (!dcJobs.empty() && dcJobs.back().jobId == jobId) {
                processJob(dcJobs.back());
            }
            // schedule deadline for this job
            cMessage* ddl = new cMessage("jobDeadline");
            ddl->setKind(jobId);
            scheduleAt(simTime() + dcDeadline, ddl);
            // schedule next release on exact grid
            scheduleAt(simTime() + dcPeriod, msg);
            return;
        } else if (strcmp(msg->getName(), "jobDeadline") == 0) {
            int jobId = msg->getKind();
            for (auto& job : dcJobs) {
                if (job.jobId != jobId) continue;
                if (job.state == REQ_SENT) { onJobMissed(job, M2_RES_MISS); break; }
                if (job.state == PENDING) {
                    // Distinguish between no attempt vs attempts but no success
                    if (job.reqTxAttempts > 0) onJobMissed(job, M1_REQ_FAIL);
                    else onJobMissed(job, M0_NO_REQ);
                    break;
                }
            }
            delete msg;
            return;
        } else if (strcmp(msg->getName(), "jobTimer") == 0) {
            printf("[%.3f] HpgpMac Node %d (%s): jobTimer received, calling processDcJobs\n", 
                   simTime().dbl(), nodeId, nodeType.c_str());
            fflush(stdout);
            processDcJobs();
        } else if (strcmp(msg->getName(), "startSlac") == 0) {
            // Start SLAC based on scenario
            startSlac();
        } else if (strcmp(msg->getName(), "DC_RESPONSE") == 0) {
            // EVSE가 예약한 DC_RESPONSE 전송 트리거: 응답을 MAC 경로로 송신
            printf("[%.3f] HpgpMac Node %d (%s): Scheduling DC_RESPONSE to transmit via MAC\n", simTime().dbl(), nodeId, nodeType.c_str());
            fflush(stdout);
            enqueueFrame(msg); // msg는 그대로 MAC 큐로 투입되고 여기서 소유권 이전됨
            return; // enqueueFrame이 msg를 삭제하므로 조기 반환
        } else if (strcmp(msg->getName(), "processAck") == 0) {
            // Handle ACK processing
            processAck();
        }
    }
    else {
        // Handle incoming messages from any input gate
        if (strcmp(msg->getName(), "txConfirm") == 0) {
            onTransmissionComplete(true);
            delete msg;
            return;
        }
        else if (strcmp(msg->getName(), "collision") == 0) {
            onTransmissionComplete(false);
            delete msg;
            return;
        }
        else if (strcmp(msg->getName(), "channelIdle") == 0) {
            if (!txQueue.empty() && !slotTimer->isScheduled()) {
                simtime_t actualPrs0 = 5.12e-6; // 5.12 microseconds
                simtime_t actualPrs1 = 5.12e-6; // 5.12 microseconds
                scheduleAt(simTime() + actualPrs0 + actualPrs1, slotTimer);
            }
        }
        else {
            // Handle incoming frames
            if (nodeType == "EVSE") {
                // Debug: log all incoming frame names with CAP on EVSE
                int cap = (int)getFramePriority(msg);
                printf("[%.3f] HpgpMac Node %d (EVSE): Incoming frame: %s (CAP%d)\n", simTime().dbl(), nodeId, msg->getName(), cap);
                fflush(stdout);
                
                // DC_REQUEST 특별 로깅
                if (strcmp(msg->getName(), "DC_REQUEST") == 0) {
                    printf("[%.3f] HpgpMac Node %d (EVSE): *** DC_REQUEST RECEIVED ***\n", simTime().dbl(), nodeId);
                    fflush(stdout);
                }
            }
            // Fallback: On EVSE, treat any non-SLAC CAP0 frame as DC_REQUEST
            if (nodeType == "EVSE" && getFramePriority(msg) == CAP0 && !isSlacMessage(msg->getName()) && strcmp(msg->getName(), "DC_RESPONSE") != 0 && strcmp(msg->getName(), "DC_REQUEST") != 0) {
                printf("[%.3f] HpgpMac Node %d (EVSE): Fallback handling as DC_REQUEST for frame '%s'\n", simTime().dbl(), nodeId, msg->getName());
                fflush(stdout);
                handleDcRequest(msg);
                return;
            }
            if (strcmp(msg->getName(), "DC_REQUEST") == 0) {
                // EVSE만 응답 생성 처리, EV는 폐기
                if (nodeType == "EVSE") {
                    printf("[%.3f] HpgpMac Node %d (EVSE): Received DC_REQUEST for handling\n", simTime().dbl(), nodeId);
                    fflush(stdout);
                    handleDcRequest(msg);
                    return;
                } else {
                    delete msg;
                    return;
                }
            } else if (strcmp(msg->getName(), "DC_RESPONSE") == 0) {
                // 채널을 통해 수신된 DC 응답 처리
                simtime_t now = simTime();
                int seq = msg->getSchedulingPriority();
                int senderNodeId = msg->getKind();
                bool handled = false;
                if (looseResponseMatching) {
                    // 느슨 매칭: 가장 이른 REQ_SENT 잡에 귀속
                    DcJob* target = findEarliestPendingReqSentJob();
                    if (target) {
                        onDcResponseReceived(*target, now);
                        handled = true;
                    }
                } else {
                    // 엄격 매칭: 동일 seq의 REQ_SENT 잡에만 매칭
                    for (auto &j : dcJobs) {
                        if (j.seq == seq && j.state == REQ_SENT) {
                            onDcResponseReceived(j, now);
                            handled = true;
                            break;
                        }
                    }
                }
                if (!handled) {
                    printf("[%.3f] HpgpMac Node %d (%s): DC_RESPONSE(seq %d, from node %d) unmatched\n", 
                           now.dbl(), nodeId, nodeType.c_str(), seq, senderNodeId);
                    fflush(stdout);
                }
                delete msg;
                return;
            } else if (strcmp(msg->getName(), "SLAC_PARM_REQ") == 0 ||
                      strcmp(msg->getName(), "SLAC_PARM_CNF") == 0 ||
                      strcmp(msg->getName(), "START_ATTEN_1") == 0 ||
                      strcmp(msg->getName(), "START_ATTEN_2") == 0 ||
                      strcmp(msg->getName(), "START_ATTEN_3") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_1") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_2") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_3") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_4") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_5") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_6") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_7") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_8") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_9") == 0 ||
                      strcmp(msg->getName(), "MNBC_SOUND_10") == 0 ||
                      strcmp(msg->getName(), "ATTEN_CHAR_RSP") == 0 ||
                      strcmp(msg->getName(), "ATTEN_CHAR_IND") == 0 ||
                      strcmp(msg->getName(), "SLAC_MATCH_REQ") == 0 ||
                      strcmp(msg->getName(), "SLAC_MATCH_CNF") == 0) {
                // SLAC messages should also go through MAC queue for proper contention
                enqueueFrame(msg);
            } else {
                enqueueFrame(msg);
            }
        }
    }
}

void HpgpMac::enqueueFrame(cMessage* frame)
{
    // Create a copy of the frame for the queue
    cMessage* frameCopy = frame->dup();
    txQueue.push(frameCopy);
    
    // Delete the original frame
    delete frame;
    
    EV << "Enqueued frame, queue size: " << txQueue.size() << endl;
    
    if (!slotTimer->isScheduled()) {
        simtime_t actualPrs0 = 5.12e-6; // 5.12 microseconds
        simtime_t actualPrs1 = 5.12e-6; // 5.12 microseconds
        scheduleAt(simTime() + actualPrs0 + actualPrs1, slotTimer);
    }
}

// Removed duplicate functions - now using the new HPGP MAC implementation above

void HpgpMac::initializeTableI()
{
    // Table I parameters for CA0, CA1 (저우선순위 그룹)
    tableICA01[0] = {0, 7};   // BPC=0 → DC=0, W0=7
    tableICA01[1] = {1, 15};  // BPC=1 → DC=1, W1=15
    tableICA01[2] = {3, 31};  // BPC=2 → DC=3, W2=31
    tableICA01[3] = {15, 63}; // BPC>2 → DC=15, W3+=63
    
    // Table I parameters for CA2, CA3 (고우선순위 그룹)
    tableICA23[0] = {0, 7};   // BPC=0 → DC=0, W0=7
    tableICA23[1] = {1, 15};  // BPC=1 → DC=1, W1=15
    tableICA23[2] = {3, 15};  // BPC=2 → DC=3, W2=15
    tableICA23[3] = {15, 31}; // BPC>2 → DC=15, W3+=31
}

void HpgpMac::setStageByBpc(int newBpc)
{
    bpc = std::min(newBpc, bpcMax);
    TableIParams params = getTableIParams(bpc);
    dc = params.dc;
    cw = params.cw;
    bc = intuniform(0, cw); // [0, W] random
    
    EV << "[" << simTime() << "] HpgpMac: BPC=" << bpc << ", DC=" << dc << ", CW=" << cw << ", BC=" << bc << endl;
}

HpgpMac::TableIParams HpgpMac::getTableIParams(int bpc)
{
    if (priorityGroup == CA23) {
        return tableICA23[bpc];
    } else {
        return tableICA01[bpc];
    }
}

bool HpgpMac::senseChannelBusy()
{
    // Simple channel sensing - can be enhanced with actual channel state
    return channelBusy;
}

bool HpgpMac::tryTransmitFrame()
{
    if (txQueue.empty()) {
        return false;
    }
    
    cMessage* frame = txQueue.front();
    txQueue.pop();
    
    emitTxAttempt();
    if (strcmp(frame->getName(), "DC_REQUEST") == 0) {
        // Find current pending job and increment attempts
        for (auto &j : dcJobs) {
            if (j.state == PENDING) {
                j.reqTxAttempts++;
                break; // Only increment for the current pending job
            }
        }
    }
    
    // Send frame to Channel Manager
    cMessage* frameCopy = frame->dup();
    currentFrame = frameCopy;
    waitingForChannelResponse = true;
    // track last tx info
    if (strcmp(frame->getName(), "DC_REQUEST") == 0) {
        lastTxType = TX_DC_REQ;
        lastTxCtx = frame->getContextPointer();
        lastTxSeq = frame->getSchedulingPriority();
    } else if (strcmp(frame->getName(), "DC_RESPONSE") == 0) {
        lastTxType = TX_DC_RSP;
        lastTxCtx = nullptr; // do not carry EV job pointer across nodes
        lastTxSeq = frame->getSchedulingPriority();
    } else {
        lastTxType = TX_NONE;
        lastTxCtx = nullptr;
        lastTxSeq = -1;
    }
    
    // Record transmission start time for DC requests
    if (strcmp(frame->getName(), "DC_REQUEST") == 0) {
        DcJob* job = static_cast<DcJob*>(frame->getContextPointer());
        if (job) {
            job->txStart_req = simTime();
            printf("[%.3f] HpgpMac Node %d (%s): DC request transmission started for job %d\n", 
                   simTime().dbl(), nodeId, nodeType.c_str(), job->jobId);
            fflush(stdout);
            
            // Store the job ID for transmission completion tracking
            lastTransmittedDcJobId = job->jobId;
        }
    }
    
    send(frameCopy, "out");
    delete frame;
    
    EV << "[" << simTime() << "] HpgpMac: Attempting transmission" << endl;
    printf("[%.3f] HpgpMac: Attempting transmission\n", simTime().dbl());
    
    return true; // Assume success for now
}

HpgpMac::Priority HpgpMac::getFramePriority(cMessage* frame)
{
    // Get priority from frame's kind field
    int priority = frame->getKind();
    
    // Map to Priority enum
    switch (priority) {
        case 0: return CAP0;
        case 1: return CAP1;
        case 2: return CAP2;
        case 3: return CAP3;
        default: return CAP0;
    }
}

simtime_t HpgpMac::getFrameDuration(cMessage* frame)
{
    // Calculate duration based on frame size and bitrate
    double bitrate = 14e6; // 14 Mbps
    int bits = 1000; // Default frame size
    if (cPacket* packet = dynamic_cast<cPacket*>(frame)) {
        bits = packet->getBitLength();
    }
    return (double)bits / bitrate;
}

bool HpgpMac::isChannelIdle()
{
    return !channelBusy && (simTime() - lastChannelActivity) >= cifs;
}

void HpgpMac::updateChannelState(bool busy)
{
    channelBusy = busy;
    if (busy) {
        lastChannelActivity = simTime();
    }
}

void HpgpMac::emitTxAttempt()
{
    emit(txAttemptsSignal, 1);
}

void HpgpMac::emitTxSuccess()
{
    emit(txSuccessSignal, 1);
}

void HpgpMac::emitTxCollision()
{
    emit(txCollisionSignal, 1);
}

void HpgpMac::emitTxDrop()
{
    emit(txDropSignal, 1);
}

// SLAC and DC methods
void HpgpMac::startSlac()
{
    if (slacStarted) return;
    
    slacStarted = true;
    slacTryId++;
    slacStartTime = simTime();
    
    printf("[%.3f] HpgpMac Node %d (%s): Starting SLAC sequence\n", simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Start actual SLAC protocol sequence
    if (nodeType == "EV") {
        // EV starts SLAC sequence (9 message types)
        startSlacSequence();
    } else if (nodeType == "EVSE") {
        // EVSE waits for SLAC messages and responds
        // Responses will be handled in handleSlacMessage()
    }
}

void HpgpMac::startDcLoop()
{
    if (dcStarted) {
        printf("[%.3f] HpgpMac Node %d (%s): DC loop already started, skipping\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        return;
    }
    
    dcStarted = true;
    dcReqSeq = 0;
    
    printf("[%.3f] HpgpMac Node %d (%s): Starting DC job management system\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Schedule first job release on exact 100ms grid from SLAC completion
    jobTimer = nullptr; // disable 1ms polling
    simtime_t firstRelease = slacCompletionTime; // k=0
    cMessage* rel = new cMessage("jobRelease");
    rel->setKind(0);
    scheduleAt(firstRelease, rel);
}

void HpgpMac::sendSlacMessage(const char* msgType)
{
    // Create SLAC message as cPacket for proper bit length handling
    cPacket* slacMsg = new cPacket(msgType);
    slacMsg->setKind(3); // CAP3 priority
    slacMsg->setTimestamp(simTime());
    
    // Set bit length for SLAC message
    slacMsg->setBitLength(2400);
    
    // Log MAC transmission
    if (recordSlacMessages) {
        logMacTx(3, 2400, simTime(), simTime() + 0.000171, true, 1, bpc, bc);
    }
    
    printf("[%.3f] HpgpMac Node %d (%s): Enqueuing SLAC message: %s (bits: 2400, priority: 3)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), msgType);
    fflush(stdout);
    
    // Enqueue SLAC message to MAC queue for proper contention
    enqueueFrame(slacMsg);
}

// sendDcRequest() is now replaced by sendDcRequestForJob() in the job management system

void HpgpMac::onSlacDone(bool success)
{
    if (!slacStarted) return;
    
    slacStarted = false;
    simtime_t completionTime = simTime() - slacStartTime;
    
    printf("[%.3f] HpgpMac Node %d (%s): SLAC completed %s in %.3f ms\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), 
           success ? "successfully" : "with failure", completionTime.dbl() * 1000);
    fflush(stdout);
    
    // Log SLAC attempt
    if (recordSlacMessages) {
        logSlacAttempt(slacTryId, slacStartTime, simTime(), success, completionTime, 0, false, 0);
    }
    
    // Debug: Check conditions
    printf("[%.3f] HpgpMac Node %d (%s): SLAC completed, success=%d, dcLoopEnabled=%d\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), success, dcLoopEnabled);
    fflush(stdout);
    
    // Start DC loop if SLAC succeeded (EV만 DC 잡 생성)
    if (success && dcLoopEnabled && nodeType == "EV") {
        printf("[%.3f] HpgpMac Node %d (%s): Starting DC loop after SLAC completion\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        
        // Store SLAC completion time for job scheduling
        slacCompletionTime = simTime();
        
        // Start DC job management system
        startDcLoop();
    } else {
        printf("[%.3f] HpgpMac Node %d (%s): DC loop not started - success=%d, dcLoopEnabled=%d, nodeType=%s\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), success, dcLoopEnabled, nodeType.c_str());
        fflush(stdout);
    }
}

// onDcTimeout removed; deadline handled in jobDeadline self-message

void HpgpMac::logMacTx(int kind, int bits, simtime_t startTime, simtime_t endTime, bool success, int attempts, int bpc, int bc)
{
    FILE* logFile = fopen("results/mac_tx.log", "a");
    if (logFile) {
        fprintf(logFile, "%d,%d,%d,%d,%.6f,%.6f,%d,%d,%d,%d\n",
                nodeId, 0, kind, bits, startTime.dbl(), endTime.dbl(), 
                success ? 1 : 0, attempts, bpc, bc);
        fclose(logFile);
    }
}

void HpgpMac::logDcCycle(int seq, simtime_t reqTime, simtime_t rspTime, simtime_t rtt, bool missFlag, bool gapViolation, int retries, int segFrames)
{
    FILE* logFile = fopen("results/dc_cycle.log", "a");
    if (logFile) {
        fprintf(logFile, "%d,%d,%.6f,%.6f,%.6f,%d,%d,%d,%d\n",
                nodeId, seq, reqTime.dbl(), rspTime.dbl(), rtt.dbl(),
                missFlag ? 1 : 0, gapViolation ? 1 : 0, retries, segFrames);
        fclose(logFile);
    }
}

void HpgpMac::logSlacAttempt(int tryId, simtime_t startTime, simtime_t endTime, bool success, simtime_t connTime, int msgTimeouts, bool procTimeout, int retries)
{
    FILE* logFile = fopen("results/slac_attempt.log", "a");
    if (logFile) {
        fprintf(logFile, "%d,%d,%.6f,%.6f,%d,%.6f,%d,%d,%d\n",
                nodeId, tryId, startTime.dbl(), endTime.dbl(), success ? 1 : 0,
                connTime.dbl(), msgTimeouts, procTimeout ? 1 : 0, retries);
        fclose(logFile);
    }
}

void HpgpMac::handleDcRequest(cMessage* msg)
{
    if (nodeType == "EVSE") {
        // EVSE responds to DC request with proper delay
        simtime_t reqTime = msg->getTimestamp();
        simtime_t now = simTime();
        int seq = msg->getSchedulingPriority(); // Get seq number from request
        
        // Record response enqueue time (응답 큐 투입 시각)
        DcJob* job = static_cast<DcJob*>(msg->getContextPointer());
        if (job) {
            job->enq_rsp = now;
        }
        
        printf("[%.3f] HpgpMac Node %d (%s): Received DC request (seq %d), responding in %.3f ms\n", 
               now.dbl(), nodeId, nodeType.c_str(), seq, dcRspDelay.dbl() * 1000);
        fflush(stdout);
        
        // Schedule response with proper delay (응답도 MAC 경합을 거치도록 큐로 투입)
        cPacket* dcRsp = new cPacket("DC_RESPONSE");
        dcRsp->setKind(0); // CAP0 priority
        int rspBits = par("dcRspBits");
        int seg = par("dcSegFrames");
        if (seg < 1) seg = 1;
        dcRsp->setBitLength((long long)rspBits * seg);
        dcRsp->setTimestamp(now);
        dcRsp->setContextPointer(msg->getContextPointer()); // Forward job reference
        dcRsp->setSchedulingPriority(seq); // Include seq number in response
        // keep kind as CAP priority; do not overwrite with nodeId
        
        // After delay, feed into our own MAC queue for transmission on shared medium
        cMessage* delayedEnqueue = new cMessage("DC_RSP_ENQUEUE");
        delayedEnqueue->setContextPointer(dcRsp);
        scheduleAt(now + dcRspDelay, delayedEnqueue);
    }
    
    delete msg;
}

void HpgpMac::handleSlacMessage(cMessage* msg)
{
    printf("[%.3f] HpgpMac Node %d (%s): Received SLAC message: %s\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), msg->getName());
    fflush(stdout);
    
    // Handle different SLAC message types
    if (strcmp(msg->getName(), "SLAC_PARM_REQ") == 0) {
        // Respond with SLAC_PARM_CNF
        sendSlacMessage("SLAC_PARM_CNF");
    } else if (strcmp(msg->getName(), "START_ATTEN_1") == 0 || 
               strcmp(msg->getName(), "START_ATTEN_2") == 0 || 
               strcmp(msg->getName(), "START_ATTEN_3") == 0) {
        // Acknowledge START_ATTEN messages
        printf("[%.3f] HpgpMac Node %d (%s): Acknowledged %s\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), msg->getName());
        fflush(stdout);
    } else if (strcmp(msg->getName(), "MNBC_SOUND_1") == 0 || 
               strcmp(msg->getName(), "MNBC_SOUND_2") == 0 || 
               strcmp(msg->getName(), "MNBC_SOUND_3") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_4") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_5") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_6") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_7") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_8") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_9") == 0 ||
               strcmp(msg->getName(), "MNBC_SOUND_10") == 0) {
        // Acknowledge MNBC_SOUND messages
        printf("[%.3f] HpgpMac Node %d (%s): Acknowledged %s\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), msg->getName());
        fflush(stdout);
    } else if (strcmp(msg->getName(), "ATTEN_CHAR_RSP") == 0) {
        // Respond with ATTEN_CHAR_IND
        sendSlacMessage("ATTEN_CHAR_IND");
    } else if (strcmp(msg->getName(), "SLAC_MATCH_REQ") == 0) {
        // Respond with SLAC_MATCH_CNF and complete SLAC
        sendSlacMessage("SLAC_MATCH_CNF");
        onSlacDone(true);
    }
    
    delete msg;
}

// Actual SLAC Protocol Implementation (9 message types)
void HpgpMac::startSlacSequence()
{
    printf("[%.3f] HpgpMac Node %d (%s): Starting SLAC sequence (event-driven)\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Initialize SLAC state
    slacStep = 0;
    slacCompleted = false;
    
    // 1. SLAC_PARM_REQ (CAP3 priority) - start with first message
    sendSlacMessage("SLAC_PARM_REQ");
}

bool HpgpMac::isSlacMessage(const char* msgName)
{
    return (strcmp(msgName, "SLAC_PARM_REQ") == 0 ||
            strcmp(msgName, "SLAC_PARM_CNF") == 0 ||
            strcmp(msgName, "START_ATTEN_1") == 0 ||
            strcmp(msgName, "START_ATTEN_2") == 0 ||
            strcmp(msgName, "START_ATTEN_3") == 0 ||
            strcmp(msgName, "MNBC_SOUND_1") == 0 ||
            strcmp(msgName, "MNBC_SOUND_2") == 0 ||
            strcmp(msgName, "MNBC_SOUND_3") == 0 ||
            strcmp(msgName, "MNBC_SOUND_4") == 0 ||
            strcmp(msgName, "MNBC_SOUND_5") == 0 ||
            strcmp(msgName, "MNBC_SOUND_6") == 0 ||
            strcmp(msgName, "MNBC_SOUND_7") == 0 ||
            strcmp(msgName, "MNBC_SOUND_8") == 0 ||
            strcmp(msgName, "MNBC_SOUND_9") == 0 ||
            strcmp(msgName, "MNBC_SOUND_10") == 0 ||
            strcmp(msgName, "ATTEN_CHAR_RSP") == 0 ||
            strcmp(msgName, "ATTEN_CHAR_IND") == 0 ||
            strcmp(msgName, "SLAC_MATCH_REQ") == 0 ||
            strcmp(msgName, "SLAC_MATCH_CNF") == 0);
}

void HpgpMac::processSlacSequence()
{
    if (nodeType != "EV" || slacCompleted) return;
    
    // Continue SLAC sequence based on current state
    switch (slacStep) {
        case 0: // After SLAC_PARM_REQ
            // 2. START_ATTEN_CHAR (multiple messages)
            for (int i = 0; i < 3; i++) {
                char msgName[50];
                sprintf(msgName, "START_ATTEN_%d", i+1);
                sendSlacMessage(msgName);
            }
            slacStep++;
            // No timer - wait for successful transmission
            break;
            
        case 1: // After START_ATTEN_CHAR
            // 3. MNBC_SOUND (multiple messages)
            for (int i = 0; i < 10; i++) {
                char msgName[50];
                sprintf(msgName, "MNBC_SOUND_%d", i+1);
                sendSlacMessage(msgName);
            }
            slacStep++;
            // No timer - wait for successful transmission
            break;
            
        case 2: // After MNBC_SOUND
            // 4. ATTEN_CHAR_RSP
            sendSlacMessage("ATTEN_CHAR_RSP");
            slacStep++;
            // No timer - wait for successful transmission
            break;
            
        case 3: // After ATTEN_CHAR_RSP
            // 5. SLAC_MATCH_REQ
            sendSlacMessage("SLAC_MATCH_REQ");
            slacStep++;
            // No timer - wait for successful transmission
            break;
            
        case 4: // After SLAC_MATCH_REQ
            // SLAC sequence complete
            slacCompleted = true;
            onSlacDone(true);
            return;
    }
}

// HPGP MAC Main Slot Processing - Complete HPGP Medium Structure
void HpgpMac::processMacSlot()
{
    // 1. Check if we have frames to transmit
    if (txQueue.empty()) {
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
        }
        return;
    }
    
    // 2. Check channel state
    bool channelBusy = senseChannelBusy();
    
    if (channelBusy) {
        // Channel is busy - update deferral counter
        if (dc > 0) {
            dc--;
        }
        
        // If DC reaches 0 while channel is busy, increase BPC stage
        if (dc == 0) {
            setStageByBpc(bpc + 1);
        }
        
        // Continue monitoring
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
        }
        return;
    }
    
    // 3. Channel is idle - check CIFS period
    simtime_t idleTime = simTime() - lastChannelActivity;
    if (idleTime < cifs) {
        // CIFS period not yet completed
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + (cifs - idleTime), slotTimer);
        }
        return;
    }
    
    // 4. CIFS completed - process backoff
    if (bc > 0) {
        bc--;
        if (!slotTimer->isScheduled()) {
            // HPGP MAC slot time: 35.84 μs (actual HPGP specification)
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
        }
        return;
    }
    
    // 5. Backoff counter reached 0 - start Priority Resolution
    if (bc == 0) {
        // Start Priority Resolution (PRS0 + PRS1) for CAP3/CAP0 contention
        startPriorityResolution();
    }
}

// HPGP Priority Resolution (CAP3 vs CAP0)
void HpgpMac::startPriorityResolution()
{
    if (inPriorityResolution) {
        // Already in PRS, avoid double scheduling
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            // Add node-specific jitter to avoid lockstep collisions
            double jitter = (nodeId % 10) * 1e-6; // 0-9 microseconds jitter based on nodeId
            scheduleAt(simTime() + actualSlotTime + jitter, slotTimer);
        }
        return;
    }
    if (txQueue.empty()) {
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            // Add node-specific jitter to avoid lockstep collisions
            double jitter = (nodeId % 10) * 1e-6; // 0-9 microseconds jitter based on nodeId
            scheduleAt(simTime() + actualSlotTime + jitter, slotTimer);
        }
        return;
    }
    
    cMessage* frame = txQueue.front();
    currentPriority = getFramePriority(frame);
    
    inPriorityResolution = true;
    priorityResolutionSlot = 0;
    
    printf("[%.3f] HpgpMac Node %d (%s): Starting Priority Resolution for CAP%d\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), currentPriority);
    fflush(stdout);
    
    // Schedule first PRS slot with actual HPGP MAC timing
    // PRS0: 5.12 μs, PRS1: 5.12 μs (HPGP specification)
    simtime_t actualPrs0 = 5.12e-6; // 5.12 microseconds
    scheduleAt(simTime() + actualPrs0, priorityResolutionTimer);
}

// Process Priority Resolution Slots
void HpgpMac::processPriorityResolution()
{
    if (!inPriorityResolution) {
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
        }
        return;
    }
    
    priorityResolutionSlot++;
    
    printf("[%.3f] HpgpMac Node %d (%s): PRS Slot %d, Priority CAP%d\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), priorityResolutionSlot, currentPriority);
    fflush(stdout);
    
    if (priorityResolutionSlot >= 2) {
        // Priority Resolution complete
        onPriorityResolutionComplete();
    } else {
        // Continue to next PRS slot with actual HPGP MAC timing
        simtime_t actualPrs1 = 5.12e-6; // 5.12 microseconds
        scheduleAt(simTime() + actualPrs1, priorityResolutionTimer);
    }
}

// Priority Resolution Complete
void HpgpMac::onPriorityResolutionComplete()
{
    inPriorityResolution = false;
    priorityResolutionSlot = 0;
    
    printf("[%.3f] HpgpMac Node %d (%s): Priority Resolution complete, attempting transmission\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Attempt transmission
    attemptTransmission();
}

// Attempt Frame Transmission
void HpgpMac::attemptTransmission()
{
    if (txQueue.empty()) {
        if (!slotTimer->isScheduled()) {
            simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
        }
        return;
    }
    
    cMessage* frame = txQueue.front();
    txQueue.pop();
    
    emitTxAttempt();
    
    // Count transmission attempts for DC_REQUEST frames
    if (strcmp(frame->getName(), "DC_REQUEST") == 0) {
        // Find current pending job and increment attempts
        for (auto &j : dcJobs) {
            if (j.state == PENDING) {
                j.reqTxAttempts++;
                break; // Only increment for the current pending job
            }
        }
    }
    
    printf("[%.3f] HpgpMac Node %d (%s): Attempting transmission of %s (CAP%d)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), frame->getName(), getFramePriority(frame));
    fflush(stdout);
    
    // Send frame to ChannelManager
    cMessage* frameCopy = frame->dup();
    currentFrame = frameCopy;
    waitingForChannelResponse = true;
    
    // Store frame info for transmission completion tracking
    if (strcmp(frame->getName(), "DC_REQUEST") == 0) {
        DcJob* job = static_cast<DcJob*>(frame->getContextPointer());
        if (job) {
            job->txStart_req = simTime();
            printf("[%.3f] HpgpMac Node %d (%s): DC request transmission started for job %d\n", 
                   simTime().dbl(), nodeId, nodeType.c_str(), job->jobId);
            fflush(stdout);
            
            // Store the job ID for transmission completion tracking
            lastTransmittedDcJobId = job->jobId;
        }
    }
    
    send(frameCopy, "out");
    delete frame;
    
    // Schedule next slot after transmission (only if not already scheduled)
    if (!slotTimer->isScheduled()) {
        simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
    }
}

// On Transmission Complete (Success/Failure)
void HpgpMac::onTransmissionComplete(bool success)
{
    waitingForChannelResponse = false;
    
    printf("[%.3f] HpgpMac Node %d (%s): onTransmissionComplete called, success=%d\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), success);
    fflush(stdout);
    
    if (success) {
        // Handle SLAC message transmission success
        if (currentFrame && isSlacMessage(currentFrame->getName())) {
            printf("[%.3f] HpgpMac Node %d (%s): SLAC message transmission successful: %s\n", 
                   simTime().dbl(), nodeId, nodeType.c_str(), currentFrame->getName());
            fflush(stdout);
            
            // Continue SLAC sequence to next step (event-driven)
            processSlacSequence();
        }
        // Record transmission end time for DC requests (전송 종료 시각)
        else if (lastTransmittedDcJobId >= 0) {
            // Find the DC job that was just transmitted
            for (auto& job : dcJobs) {
                if (job.jobId == lastTransmittedDcJobId) {
                    job.txEnd_req = simTime();
                    printf("[%.3f] HpgpMac Node %d (%s): DC request transmission completed for job %d\n", 
                           simTime().dbl(), nodeId, nodeType.c_str(), job.jobId);
                    fflush(stdout);
                    // 성공 송신 확인: 이제 REQ_SENT 전이 및 reqTime 설정(와이어 기준)
                    job.state = REQ_SENT;
                    job.reqTime = job.txEnd_req;
                    logJobEvent(job, "DC_REQ_TX_OK");
                    break;
                }
            }
            lastTransmittedDcJobId = -1; // Reset
        }
        
        printf("[%.3f] HpgpMac Node %d (%s): Transmission successful\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        
        currentFrame = nullptr;
        
        emitTxSuccess();
        printf("[%.3f] HpgpMac Node %d (%s): Transmission successful\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        
        // Reset BPC on success
        setStageByBpc(0);
        // clear lastTx
        lastTxType = TX_NONE;
        lastTxCtx = nullptr;
        lastTxSeq = -1;
        
        // Schedule RIFS + ACK processing
        scheduleAt(simTime() + rifs, new cMessage("processAck"));
    } else {
        // 충돌 처리 전에 현재 프레임 정보를 사용해야 하므로 null 처리보다 먼저 호출
        onCollision();
        currentFrame = nullptr;
    }
}

// Process ACK after RIFS
void HpgpMac::processAck()
{
    printf("[%.3f] HpgpMac Node %d (%s): Processing ACK after RIFS\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Update channel activity time
    lastChannelActivity = simTime();
    
    // Continue with next slot
    if (!slotTimer->isScheduled()) {
        simtime_t actualSlotTime = 35.84e-6; // 35.84 microseconds
            scheduleAt(simTime() + actualSlotTime, slotTimer);
    }
}

// On Collision
void HpgpMac::onCollision()
{
    emitTxCollision();
    printf("[%.3f] HpgpMac Node %d (%s): Transmission collision\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Increase BPC stage on collision
    setStageByBpc(bpc + 1);
    
    // Add collision recovery delay (JAM signal + EIFS)
    simtime_t jamTime = 32e-6; // 32 μs JAM signal
    simtime_t eifs = 88e-6;    // 88 μs EIFS (Extended Inter-Frame Space)
    simtime_t collisionDelay = jamTime + eifs;
    
    // Schedule retry after collision recovery
    if (!slotTimer->isScheduled()) {
        scheduleAt(simTime() + collisionDelay, slotTimer);
    }

    // Re-enqueue collided frame for retry (REQ 또는 RSP) using lastTx snapshot
    if (lastTxType == TX_DC_REQ) {
        DcJob* job = static_cast<DcJob*>(lastTxCtx);
        if (job) {
            cMessage* retry = new cMessage("DC_REQUEST");
            retry->setKind(0);
            retry->setTimestamp(simTime());
            retry->setContextPointer(job);
            retry->setSchedulingPriority(job->seq);
            enqueueFrame(retry);
            printf("[%.3f] HpgpMac Node %d (%s): Re-enqueued DC_REQUEST for job %d (seq %d) after collision\n",
                   simTime().dbl(), nodeId, nodeType.c_str(), job->jobId, job->seq);
            fflush(stdout);
        }
    } else if (lastTxType == TX_DC_RSP) {
        DcJob* job = static_cast<DcJob*>(lastTxCtx);
        int seq = lastTxSeq;
        cPacket* retry = new cPacket("DC_RESPONSE");
        retry->setKind(0);
        int rspBits = par("dcRspBits");
        int seg = par("dcSegFrames");
        if (seg < 1) seg = 1;
        retry->setBitLength((long long)rspBits * seg);
        retry->setTimestamp(simTime());
        retry->setContextPointer(job);
        retry->setSchedulingPriority(seq);
        enqueueFrame(retry);
        printf("[%.3f] HpgpMac Node %d (%s): Re-enqueued DC_RESPONSE (seq %d) after collision\n",
               simTime().dbl(), nodeId, nodeType.c_str(), seq);
        fflush(stdout);
    }
}

void HpgpMac::finish()
{
    // Clean up self-messages to avoid undisposed warnings
    if (slotTimer && slotTimer->isScheduled()) cancelEvent(slotTimer);
    delete slotTimer; slotTimer = nullptr;
    if (priorityResolutionTimer && priorityResolutionTimer->isScheduled()) cancelEvent(priorityResolutionTimer);
    delete priorityResolutionTimer; priorityResolutionTimer = nullptr;
    // dcTimer 제거: jobDeadline 기반으로만 데드라인 체크
    if (slacTimer && slacTimer->isScheduled()) cancelEvent(slacTimer);
    delete slacTimer; slacTimer = nullptr;
    if (startSlacMsg && startSlacMsg->isScheduled()) cancelEvent(startSlacMsg);
    delete startSlacMsg; startSlacMsg = nullptr;
    if (jobTimer && jobTimer->isScheduled()) cancelEvent(jobTimer);
    delete jobTimer; jobTimer = nullptr;
    // Clear tx queue
    while (!txQueue.empty()) { auto* m = txQueue.front(); txQueue.pop(); delete m; }
}

// DC Job Management System Implementation
void HpgpMac::createDcJob(int jobId, simtime_t releaseTime)
{
    DcJob job;
    job.jobId = jobId;
    job.releaseTime = releaseTime;
    job.windowStart = releaseTime;
    job.windowEnd = releaseTime + dcPeriod;
    job.deadline = releaseTime + dcDeadline;
    job.state = PENDING;
    job.seq = 0;
    job.reqTime = 0;
    job.resTime = 0;
    job.missType = M0_NO_REQ;
    job.tardiness = 0;
    
    // Initialize measurement points
    job.enq_req = 0;
    job.txStart_req = 0;
    job.txEnd_req = 0;
    job.rxStart_rsp = 0;
    job.rxEnd_rsp = 0;
    job.enq_rsp = 0;
    job.reqTxAttempts = 0;
    
    dcJobs.push_back(job);
    
    printf("[%.3f] HpgpMac Node %d (%s): Created DC job %d at %.3f\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), jobId, releaseTime.dbl());
    fflush(stdout);
    
    // Log job creation
    logJobEvent(job, "DC_RELEASE");
}

void HpgpMac::processDcJobs()
{
    if (!dcStarted) {
        printf("[%.3f] HpgpMac Node %d (%s): processDcJobs called but dcStarted=false\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        return;
    }
    
    simtime_t now = simTime();
    printf("[%.3f] HpgpMac Node %d (%s): processDcJobs called, now=%.3f, slacCompletionTime=%.3f\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), now.dbl(), slacCompletionTime.dbl());
    fflush(stdout);
    
    // Create new jobs for the next 100ms period
    int currentJobId = (int)((now - slacCompletionTime) / dcPeriod);
    printf("[%.3f] HpgpMac Node %d (%s): currentJobId=%d, dcPeriod=%.3f\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), currentJobId, dcPeriod.dbl());
    fflush(stdout);
    
    if (currentJobId >= 0 && currentJobId < 1200) { // 120s / 100ms = 1200 jobs
        simtime_t releaseTime = slacCompletionTime + currentJobId * dcPeriod;
        printf("[%.3f] HpgpMac Node %d (%s): Creating job %d at releaseTime=%.3f\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), currentJobId, releaseTime.dbl());
        fflush(stdout);
        
        // Check if job already exists
        bool jobExists = false;
        for (const auto& job : dcJobs) {
            if (job.jobId == currentJobId) {
                jobExists = true;
                break;
            }
        }
        
        printf("[%.3f] HpgpMac Node %d (%s): jobExists=%d, dcJobs.size()=%zu\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), jobExists, dcJobs.size());
        fflush(stdout);
        
        if (!jobExists) {
            printf("[%.3f] HpgpMac Node %d (%s): Creating new job %d\n", 
                   simTime().dbl(), nodeId, nodeType.c_str(), currentJobId);
            fflush(stdout);
            createDcJob(currentJobId, releaseTime);
        } else {
            printf("[%.3f] HpgpMac Node %d (%s): Job %d already exists, skipping\n", 
                   simTime().dbl(), nodeId, nodeType.c_str(), currentJobId);
            fflush(stdout);
        }
    }
    
    // Process existing jobs
    for (auto& job : dcJobs) {
        if (job.state == PENDING && now >= job.windowStart) {
            processJob(job);
        } else if (job.state == PENDING && now >= job.windowEnd) {
            // Window ended without successful request
            if (job.reqTxAttempts > 0) {
                onJobMissed(job, M1_REQ_FAIL); // 시도는 있었으나 성공 송신 없음
            } else {
                onJobMissed(job, M0_NO_REQ);   // 시도 자체가 없음
            }
        } else if (job.state == REQ_SENT && now >= job.deadline) {
            // Deadline reached after successful request, but no response
            onJobMissed(job, M2_RES_MISS);
        }
    }
    
    // Schedule next job processing
    if (dcStarted) {
        scheduleAt(now + 0.001, jobTimer);
    }
}

void HpgpMac::processJob(DcJob& job)
{
    if (job.state != PENDING) return;
    // Immediately try to enqueue the request; window checks are handled by deadline
    sendDcRequestForJob(job);
}

void HpgpMac::sendDcRequestForJob(DcJob& job)
{
    // Record enqueue time (큐 투입 시각)
    job.enq_req = simTime();
    
    // Create DC request packet with param bit length and segmentation
    cPacket* dcMsg = new cPacket("DC_REQUEST");
    dcMsg->setKind(0); // CAP0 priority
    dcMsg->setSchedulingPriority(nodeId); // Store nodeId for response matching
    int reqBits = par("dcReqBits");
    int seg = par("dcSegFrames");
    if (seg < 1) seg = 1;
    dcMsg->setBitLength((long long)reqBits * seg);
    dcMsg->setTimestamp(simTime());
    dcMsg->setContextPointer(&job); // Store job reference
    
    // Record transmission start time (전송 시작 시각)
    job.txStart_req = simTime();
    
    // Update sequence only (성공 송신 확인 후 REQ_SENT 전이)
    job.seq = ++dcReqSeq;
    
    // Store seq number in message for matching
    dcMsg->setSchedulingPriority(job.seq);
    
    printf("[%.3f] HpgpMac Node %d (%s): Sending DC request for job %d (seq %d)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), job.jobId, job.seq);
    fflush(stdout);
    
    // 성공 송신 시 onTransmissionComplete에서 로깅
    
    // Enqueue into MAC for contention-based transmission
    enqueueFrame(dcMsg);
    // Timeout은 jobDeadline self-message로 처리 (별도 dcTimer 미사용)
}

void HpgpMac::onDcRequestSent(DcJob& job)
{
    job.state = REQ_SENT;
    job.reqTime = simTime();
    
    printf("[%.3f] HpgpMac Node %d (%s): DC request sent for job %d\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), job.jobId);
    fflush(stdout);
}

void HpgpMac::onDcResponseReceived(DcJob& job, simtime_t responseTime)
{
    if (job.state == RES_RECEIVED || job.state == MISSED) return; // idempotent
    // Record response reception times (응답 수신 시각)
    job.rxStart_rsp = responseTime; // Assume reception start = reception end for simplicity
    job.rxEnd_rsp = responseTime;
    
    job.state = RES_RECEIVED;
    job.resTime = responseTime;
    
    // Calculate RTT using wire time (와이어 시각 기준 RTT 계산)
    // Use txEnd_req if available, otherwise fall back to txStart_req
    simtime_t txEndTime = (job.txEnd_req > 0) ? job.txEnd_req : job.txStart_req;
    simtime_t rtt = job.rxEnd_rsp - txEndTime;
    bool missed = (rtt > dcDeadline);
    
    printf("[%.3f] HpgpMac Node %d (%s): RTT calculation - txEnd_req=%.6f, txStart_req=%.6f, rxEnd_rsp=%.6f, rtt=%.6f\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), 
           job.txEnd_req.dbl(), job.txStart_req.dbl(), job.rxEnd_rsp.dbl(), rtt.dbl());
    fflush(stdout);
    
    if (missed) {
        job.missType = M3_RES_LATE;
        job.tardiness = rtt - dcDeadline;
        printf("[%.3f] HpgpMac Node %d (%s): DC job %d MISSED (M3_RES_LATE), RTT=%.6f > deadline=%.6f, tardiness=%.6f\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), job.jobId, rtt.dbl(), dcDeadline.dbl(), job.tardiness.dbl());
        fflush(stdout);
        onJobMissed(job, M3_RES_LATE);
    } else {
        printf("[%.3f] HpgpMac Node %d (%s): DC job %d completed successfully, RTT=%.6f <= deadline=%.6f\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), job.jobId, rtt.dbl(), dcDeadline.dbl());
        fflush(stdout);
        
        // Log successful response
        logJobEvent(job, "DC_RES_RX_OK");
    }
}

void HpgpMac::onJobMissed(DcJob& job, MissType missType)
{
    if (job.state == MISSED || job.state == RES_RECEIVED) return; // idempotent
    job.state = MISSED;
    job.missType = missType;
    
    const char* missTypeStr = "UNKNOWN";
    switch (missType) {
        case M0_NO_REQ: missTypeStr = "M0_NO_REQ"; break;
        case M1_REQ_FAIL: missTypeStr = "M1_REQ_FAIL"; break;
        case M2_RES_MISS: missTypeStr = "M2_RES_MISS"; break;
        case M3_RES_LATE: missTypeStr = "M3_RES_LATE"; break;
    }
    
    printf("[%.3f] HpgpMac Node %d (%s): DC job %d missed (%s)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), job.jobId, missTypeStr);
    fflush(stdout);
    
    // Log deadline reached
    logJobEvent(job, "DC_DEADLINE");
    
    // Log miss details
    logJobMiss(job, missType);
}

void HpgpMac::logJobEvent(const DcJob& job, const char* event)
{
    FILE* logFile = fopen("results/dc_jobs.log", "a");
    if (logFile) {
        fprintf(logFile, "%d,%d,%.6f,%.6f,%.6f,%.6f,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%s\n",
                nodeId, job.jobId, job.releaseTime.dbl(), job.windowStart.dbl(),
                job.windowEnd.dbl(), job.deadline.dbl(), job.state, job.seq,
                job.reqTime.dbl(), job.resTime.dbl(), 
                job.enq_req.dbl(), job.txStart_req.dbl(), job.txEnd_req.dbl(),
                job.enq_rsp.dbl(), job.rxStart_rsp.dbl(), job.rxEnd_rsp.dbl(), event);
        fclose(logFile);
    }
}

void HpgpMac::logJobMiss(const DcJob& job, MissType missType)
{
    FILE* logFile = fopen("results/dc_misses.log", "a");
    if (logFile) {
        fprintf(logFile, "%d,%d,%.6f,%.6f,%.6f,%.6f,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
                nodeId, job.jobId, job.releaseTime.dbl(), job.windowStart.dbl(),
                job.windowEnd.dbl(), job.deadline.dbl(), job.state, missType,
                job.reqTime.dbl(), job.tardiness.dbl(),
                job.enq_req.dbl(), job.txStart_req.dbl(), job.txEnd_req.dbl(),
                job.enq_rsp.dbl(), job.rxStart_rsp.dbl(), job.rxEnd_rsp.dbl());
        fclose(logFile);
    }
}

HpgpMac::DcJob* HpgpMac::findEarliestPendingReqSentJob()
{
    DcJob* candidate = nullptr;
    for (auto &j : dcJobs) {
        if (j.state == REQ_SENT) {
            if (!candidate || j.reqTime < candidate->reqTime) {
                candidate = const_cast<DcJob*>(&j);
            }
        }
    }
    return candidate;
}