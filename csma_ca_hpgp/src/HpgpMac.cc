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
    
    // Priority Resolution state
    inPriorityResolution = false;
    priorityResolutionSlot = 0;
    currentPriority = CAP0;
    
    // Create timers
    slotTimer = new cMessage("slotTimer");
    priorityResolutionTimer = new cMessage("priorityResolutionTimer");
    
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
    
    // Force DC loop enabled for testing
    dcLoopEnabled = true;
    printf("HpgpMac Node %d (%s): Forced dcLoopEnabled = true\n", nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Initialize SLAC and DC state
    dcReqSeq = 0;
    dcStarted = false;
    dcTimer = nullptr;
    slacStarted = false;
    slacTryId = 0;
    slacStartTime = 0;
    slacTimer = nullptr;
    
    // Start with PRS0 + PRS1 delay
    scheduleAt(simTime() + prs0 + prs1, slotTimer);
    
    // Initialize logging for testing
    EV << "HpgpMac Node " << nodeId << " (" << nodeType << "): Initialized" << endl;
    EV << "dcLoopEnabled = " << dcLoopEnabled << endl;
    
    // Start DC loop immediately for DC command analysis
    if (dcLoopEnabled) {
        EV << "Starting DC loop immediately for DC command analysis" << endl;
        startDcLoop();
    } else {
        EV << "DC loop disabled" << endl;
    }
    
    // Start actual SLAC and DC processes
    // Start SLAC based on scenario
    if (strcmp(par("scenario"), "WC_A_Sequential") == 0) {
        // WC-A: Sequential SLAC (each node starts at different time)
        double delay = nodeId * 0.1; // 100ms delay between nodes
        scheduleAt(simTime() + delay, new cMessage("startSlac"));
    } else if (strcmp(par("scenario"), "WC_B_Simultaneous") == 0) {
        // WC-B: Simultaneous SLAC (all nodes start at same time)
        scheduleAt(simTime() + 0.1, new cMessage("startSlac"));
    } else {
        // Default: Start immediately
        if (nodeType == "EVSE") {
            startSlac();
        } else if (nodeType == "EV") {
            startSlac();
        }
    }
    
    // Start DC loop after SLAC completion
    if (dcLoopEnabled) {
        // Schedule DC start after SLAC (immediate start for testing)
        scheduleAt(simTime() + 0.5, new cMessage("startDcAfterSlac"));
    }
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
        } else if (msg == dcTimer) {
            onDcTimeout();
        } else if (msg == slacTimer) {
            // SLAC timer expired - continue SLAC sequence
            processSlacSequence();
        } else if (strcmp(msg->getName(), "dcNext") == 0) {
            sendDcRequest();
        } else if (strcmp(msg->getName(), "startSlac") == 0) {
            // Start SLAC based on scenario
            startSlac();
        } else if (strcmp(msg->getName(), "startDcAfterSlac") == 0) {
            if (!dcStarted) {
                startDcLoop();
            }
        } else if (strcmp(msg->getName(), "DC_RESPONSE") == 0) {
            // Handle DC response
            simtime_t reqTime = msg->getTimestamp();
            simtime_t now = simTime();
            simtime_t rtt = now - reqTime;
            
            printf("[%.3f] HpgpMac Node %d (%s): Received DC response, RTT: %.3f ms\n", 
                   now.dbl(), nodeId, nodeType.c_str(), rtt.dbl() * 1000);
            fflush(stdout);
            
            // Check if deadline was missed
            bool missFlag = (rtt > dcDeadline);
            
            // Log DC cycle
            if (recordDcCycles) {
                logDcCycle(dcReqSeq, reqTime, now, rtt, missFlag, false, 0, 3);
            }
        } else if (strcmp(msg->getName(), "processAck") == 0) {
            // Handle ACK processing
            processAck();
        }
    }
    else {
        // Handle incoming messages from any input gate
        if (strcmp(msg->getName(), "txConfirm") == 0) {
            onTransmissionComplete(true);
        }
        else if (strcmp(msg->getName(), "collision") == 0) {
            onTransmissionComplete(false);
        }
        else if (strcmp(msg->getName(), "channelIdle") == 0) {
            if (!txQueue.empty() && !slotTimer->isScheduled()) {
                scheduleAt(simTime() + prs0 + prs1, slotTimer);
            }
        }
        else {
            // Handle incoming frames
            if (strcmp(msg->getName(), "DC_REQUEST") == 0) {
                handleDcRequest(msg);
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
                handleSlacMessage(msg);
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
        scheduleAt(simTime() + prs0 + prs1, slotTimer);
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
    
    // Send frame to Channel Manager
    cMessage* frameCopy = frame->dup();
    currentFrame = frameCopy;
    waitingForChannelResponse = true;
    
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
    
    printf("[%.3f] HpgpMac Node %d (%s): Starting DC loop for testing\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // Start first DC request
    sendDcRequest();
}

void HpgpMac::sendSlacMessage(const char* msgType)
{
    // Create SLAC message
    cMessage* slacMsg = new cMessage(msgType);
    slacMsg->setKind(3); // CAP3 priority
    slacMsg->setTimestamp(simTime());
    
    // Log MAC transmission
    if (recordSlacMessages) {
        logMacTx(3, 2400, simTime(), simTime() + 0.000171, true, 1, bpc, bc);
    }
    
    printf("[%.3f] HpgpMac Node %d (%s): Sending SLAC message: %s (bits: 2400, priority: 3)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), msgType);
    fflush(stdout);
    
    // Send to connected node
    send(slacMsg, "out");
}

void HpgpMac::sendDcRequest()
{
    dcReqSeq++;
    simtime_t now = simTime();
    
    EV << "Sending DC request #" << dcReqSeq << endl;
    printf("[%.3f] HpgpMac Node %d (%s): Sending DC request #%d\n", now.dbl(), nodeId, nodeType.c_str(), dcReqSeq);
    fflush(stdout);
    
    // Create DC request message with actual content
    cMessage* dcMsg = new cMessage("DC_REQUEST");
    dcMsg->setKind(0); // CAP0 priority
    dcMsg->setTimestamp(now); // Store request time
    
    // Send to connected node
    send(dcMsg, "out");
    
    // Schedule DC timeout
    dcTimer = new cMessage("dcTimer");
    scheduleAt(now + dcDeadline, dcTimer);
    
    // Schedule next DC request
    if (dcStarted) {
        scheduleAt(now + dcPeriod, new cMessage("dcNext"));
    }
}

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
    
    // Start DC loop if SLAC succeeded
    if (success && dcLoopEnabled) {
        printf("[%.3f] HpgpMac Node %d (%s): Starting DC loop after SLAC completion\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        // Reset DC state to allow restart
        dcStarted = false;
        startDcLoop();
    } else {
        printf("[%.3f] HpgpMac Node %d (%s): DC loop not started - success=%d, dcLoopEnabled=%d\n", 
               simTime().dbl(), nodeId, nodeType.c_str(), success, dcLoopEnabled);
        fflush(stdout);
    }
}

void HpgpMac::onDcTimeout()
{
    printf("[%.3f] HpgpMac Node %d (%s): DC request #%d timeout\n", simTime().dbl(), nodeId, nodeType.c_str(), dcReqSeq);
    fflush(stdout);
    
    // Log DC cycle with timeout (deadline missed)
    if (recordDcCycles) {
        logDcCycle(dcReqSeq, simTime() - dcDeadline, simTime(), dcDeadline, true, false, 0, 1);
    }
    
    // Continue with next DC request
    if (dcStarted) {
        scheduleAt(simTime() + dcPeriod, new cMessage("dcNext"));
    }
}

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
        
        printf("[%.3f] HpgpMac Node %d (%s): Received DC request, responding in %.3f ms\n", 
               now.dbl(), nodeId, nodeType.c_str(), dcRspDelay.dbl() * 1000);
        fflush(stdout);
        
        // Schedule response with proper delay
        cMessage* dcRsp = new cMessage("DC_RESPONSE");
        dcRsp->setKind(0); // CAP0 priority
        dcRsp->setTimestamp(now);
        
        // Send response after delay
        scheduleAt(now + dcRspDelay, dcRsp);
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
    printf("[%.3f] HpgpMac Node %d (%s): Starting SLAC sequence (9 message types)\n", 
           simTime().dbl(), nodeId, nodeType.c_str());
    fflush(stdout);
    
    // 1. SLAC_PARM_REQ (CAP3 priority)
    sendSlacMessage("SLAC_PARM_REQ");
    
    // Schedule next message after response
    slacTimer = new cMessage("slacTimer");
    scheduleAt(simTime() + 0.1, slacTimer);
}

void HpgpMac::processSlacSequence()
{
    if (nodeType != "EV") return;
    
    // Continue SLAC sequence based on current state
    static int slacStep = 0;
    
    switch (slacStep) {
        case 0: // After SLAC_PARM_REQ
            // 2. START_ATTEN_CHAR (multiple messages)
            for (int i = 0; i < 3; i++) {
                char msgName[50];
                sprintf(msgName, "START_ATTEN_%d", i+1);
                sendSlacMessage(msgName);
            }
            slacStep++;
            break;
            
        case 1: // After START_ATTEN_CHAR
            // 3. MNBC_SOUND (multiple messages)
            for (int i = 0; i < 10; i++) {
                char msgName[50];
                sprintf(msgName, "MNBC_SOUND_%d", i+1);
                sendSlacMessage(msgName);
            }
            slacStep++;
            break;
            
        case 2: // After MNBC_SOUND
            // 4. ATTEN_CHAR_RSP
            sendSlacMessage("ATTEN_CHAR_RSP");
            slacStep++;
            break;
            
        case 3: // After ATTEN_CHAR_RSP
            // 5. SLAC_MATCH_REQ
            sendSlacMessage("SLAC_MATCH_REQ");
            slacStep++;
            break;
            
        case 4: // After SLAC_MATCH_REQ
            // SLAC sequence complete
            onSlacDone(true);
            return;
    }
    
    // Schedule next step
    slacTimer = new cMessage("slacTimer");
    scheduleAt(simTime() + 0.1, slacTimer);
}

// HPGP MAC Main Slot Processing - Complete HPGP Medium Structure
void HpgpMac::processMacSlot()
{
    // 1. Check if we have frames to transmit
    if (txQueue.empty()) {
        if (!slotTimer->isScheduled()) {
            scheduleAt(simTime() + slotTime, slotTimer);
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
            scheduleAt(simTime() + slotTime, slotTimer);
        }
        return;
    }
    
    // 3. Channel is idle - check CIFS period
    simtime_t idleTime = simTime() - lastChannelActivity;
    if (idleTime < cifs) {
        // CIFS period not yet completed
        if (!slotTimer->isScheduled()) {
            scheduleAt(simTime() + (cifs - idleTime), slotTimer);
        }
        return;
    }
    
    // 4. CIFS completed - process backoff
    if (bc > 0) {
        bc--;
        if (!slotTimer->isScheduled()) {
            scheduleAt(simTime() + slotTime, slotTimer);
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
    if (txQueue.empty()) {
        if (!slotTimer->isScheduled()) {
            scheduleAt(simTime() + slotTime, slotTimer);
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
    
    // Schedule first PRS slot
    scheduleAt(simTime() + prs0, priorityResolutionTimer);
}

// Process Priority Resolution Slots
void HpgpMac::processPriorityResolution()
{
    if (!inPriorityResolution) {
        if (!slotTimer->isScheduled()) {
            scheduleAt(simTime() + slotTime, slotTimer);
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
        // Continue to next PRS slot
        scheduleAt(simTime() + prs1, priorityResolutionTimer);
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
            scheduleAt(simTime() + slotTime, slotTimer);
        }
        return;
    }
    
    cMessage* frame = txQueue.front();
    txQueue.pop();
    
    emitTxAttempt();
    
    printf("[%.3f] HpgpMac Node %d (%s): Attempting transmission of %s (CAP%d)\n", 
           simTime().dbl(), nodeId, nodeType.c_str(), frame->getName(), getFramePriority(frame));
    fflush(stdout);
    
    // Send frame to ChannelManager
    cMessage* frameCopy = frame->dup();
    currentFrame = frameCopy;
    waitingForChannelResponse = true;
    
    send(frameCopy, "out");
    delete frame;
    
    // Schedule next slot after transmission (only if not already scheduled)
    if (!slotTimer->isScheduled()) {
        scheduleAt(simTime() + slotTime, slotTimer);
    }
}

// On Transmission Complete (Success/Failure)
void HpgpMac::onTransmissionComplete(bool success)
{
    waitingForChannelResponse = false;
    currentFrame = nullptr;
    
    if (success) {
        emitTxSuccess();
        printf("[%.3f] HpgpMac Node %d (%s): Transmission successful\n", 
               simTime().dbl(), nodeId, nodeType.c_str());
        fflush(stdout);
        
        // Reset BPC on success
        setStageByBpc(0);
        
        // Schedule RIFS + ACK processing
        scheduleAt(simTime() + rifs, new cMessage("processAck"));
    } else {
        onCollision();
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
        scheduleAt(simTime() + slotTime, slotTimer);
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
}

void HpgpMac::finish()
{
    // Don't delete messages in finish() to avoid segmentation fault
    // OMNeT++ will handle cleanup automatically
}