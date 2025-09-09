#include "SlacApplication.h"

Define_Module(SlacApplication);

void SlacApplication::initialize()
{
    // Get parameters
    nodeType = par("nodeType").stringValue();
    nodeId = par("nodeId");
    slacMsgTimeout = par("slacMsgTimeout");
    slacProcTimeout = par("slacProcTimeout");
    slacMaxRetry = par("slacMaxRetry");
    slacRetryBackoff = par("slacRetryBackoff");
    
    // DC loop parameters
    dcLoopEnabled = par("dcLoopEnabled");
    dcPeriod = par("dcPeriod");
    dcDeadline = par("dcDeadline");
    dcRspDelay = par("dcRspDelay");
    dcRspJitter = par("dcRspJitter");
    
    // SLAC detailed parameters
    nStartAtten = par("nStartAtten");
    nMsound = par("nMsound");
    gapStart = par("gapStart");
    gapMsound = par("gapMsound");
    delayEvseRsp = par("delayEvseRsp");
    gapAttn = par("gapAttn");
    gapMatch = par("gapMatch");
    
    // Initialize state
    slacDone = false;
    awaitingResponse = false;
    awaitingMessageType = SLAC_PARM_REQ;
    retryCount = 0;
    dcStarted = false;
    dcReqSeq = 0;
    
    // Create timeout messages
    processTimeout = new cMessage("processTimeout");
    messageTimeout = new cMessage("messageTimeout");
    
    // Register signals
    slacCompleteSignal = registerSignal("slacComplete");
    slacRetriesSignal = registerSignal("slacRetries");
    slacTimeoutSignal = registerSignal("slacTimeout");
    
    // Start SLAC if this is an EV
    if (nodeType == "EV") {
        scheduleAt(simTime() + uniform(0, 0.001), new cMessage("startSlac"));
    }
}

void SlacApplication::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        if (msg == processTimeout) {
            if (!slacDone) {
                EV << "SLAC process timeout" << endl;
                failAndMaybeRetry("process_timeout");
            }
        }
        else if (msg == messageTimeout) {
            if (!slacDone && awaitingResponse) {
                EV << "SLAC message timeout" << endl;
                failAndMaybeRetry("message_timeout");
            }
        }
        else if (strcmp(msg->getName(), "startSlac") == 0) {
            startSlac();
        }
        else if (strcmp(msg->getName(), "dcTick") == 0) {
            sendDcRequest();
        }
        delete msg;
    }
        else {
            // Handle incoming SLAC message
            if (cPacket* slacMsg = dynamic_cast<cPacket*>(msg)) {
                // Broadcast to all other nodes (simulate shared bus)
                cPacket* broadcastMsg = slacMsg->dup();
                send(broadcastMsg, "out");
                
                // For now, assume message type 1 (SLAC_PARM_CNF)
                handleSlacResponse(SLAC_PARM_CNF);
            }
            delete msg;
        }
}

void SlacApplication::startSlac()
{
    EV << "[" << simTime() << "] Node " << nodeId << " (" << nodeType << "): Starting SLAC sequence" << endl;
    printf("[%.3f] Node %d (%s): Starting SLAC sequence\n", simTime().dbl(), nodeId, nodeType.c_str());
    
    slacStartTime = simTime();
    retryCount = 0;
    resetForRetry();
    
    // Schedule process timeout
    scheduleProcessTimeout();
    
    // Start SLAC sequence
    // 1. Send SLAC_PARM_REQ
    sendSlacMessage(SLAC_PARM_REQ, 300 * 8);
    scheduleMessageTimeout(SLAC_PARM_CNF);
    
    // 2. Schedule START_ATTEN messages
    simtime_t currentTime = simTime();
    for (int i = 0; i < nStartAtten; i++) {
        simtime_t delay = (i == 0) ? gapAttn : gapStart;
        scheduleAt(currentTime + delay, new cMessage("startAtten"));
        currentTime += delay;
    }
    
    // 3. Schedule MNBC_SOUND messages
    for (int i = 0; i < nMsound; i++) {
        currentTime += gapMsound;
        scheduleAt(currentTime, new cMessage("mnbcSound"));
    }
    
    // 4. Schedule ATTEN_CHAR_IND
    currentTime += gapAttn;
    scheduleAt(currentTime, new cMessage("attenCharInd"));
    
    // 5. Schedule SLAC_MATCH_REQ
    currentTime += delayEvseRsp + gapAttn;
    scheduleAt(currentTime, new cMessage("slacMatchReq"));
}

void SlacApplication::sendSlacMessage(SlacMessageType type, int bits)
{
    cPacket* msg = new cPacket("slacMsg");
    msg->setBitLength(bits);
    
    // Set priority based on message type
    int priority = getMessagePriority(type);
    msg->setKind(priority); // Use kind field to store priority
    
    EV << "[" << simTime() << "] Node " << nodeId << " (" << nodeType << "): Sending SLAC message type " << type << " (bits: " << bits << ", priority: " << priority << ")" << endl;
    printf("[%.3f] Node %d (%s): Sending SLAC message type %d (bits: %d, priority: %d)\n", simTime().dbl(), nodeId, nodeType.c_str(), type, bits, priority);
    
    // 파일 로그 출력
    FILE* logFile = fopen("results/slac_messages.log", "a");
    if (logFile) {
        fprintf(logFile, "%.3f,Node_%d_%s,SLAC_MSG_TYPE_%d,%d,PRIORITY_%d\n", 
                simTime().dbl(), nodeId, nodeType.c_str(), type, bits, priority);
        fclose(logFile);
    }
    
    // 통계 수집
    emit(slacCompleteSignal, simTime());
    
    // Send to lower layer (would be connected to MAC layer)
    send(msg, "out");
}

void SlacApplication::handleSlacResponse(SlacMessageType type)
{
    if (slacDone) return;
    
    receivedMessages.insert(type);
    
    if (awaitingResponse && awaitingMessageType == type) {
        awaitingResponse = false;
        cancelMessageTimeout();
        
        EV << "Received expected SLAC response: " << type << endl;
        
        // Check if we have all required responses
        std::set<SlacMessageType> required = {SLAC_PARM_CNF, ATTEN_CHAR_IND, SLAC_MATCH_CNF};
        bool allReceived = true;
        for (auto req : required) {
            if (receivedMessages.find(req) == receivedMessages.end()) {
                allReceived = false;
                break;
            }
        }
        
        if (allReceived) {
            onSlacDone(true);
        }
    }
}

void SlacApplication::onSlacDone(bool success)
{
    if (slacDone) return;
    
    slacDone = true;
    cancelProcessTimeout();
    cancelMessageTimeout();
    
    simtime_t completionTime = simTime() - slacStartTime;
    
    EV << "SLAC completed: " << (success ? "success" : "failure") 
       << " in " << completionTime << "s" << endl;
    
    if (success) {
        emitSlacComplete(completionTime);
        
        // Start DC loop if enabled
        if (dcLoopEnabled && nodeType == "EV") {
            startDcLoop();
        }
    }
    else {
        emitSlacTimeout();
    }
}

void SlacApplication::failAndMaybeRetry(const std::string& reason)
{
    if (slacDone) return;
    
    slacDone = true;
    cancelProcessTimeout();
    cancelMessageTimeout();
    
    EV << "SLAC failed: " << reason << endl;
    
    if (retryCount < slacMaxRetry) {
        retryCount++;
        emitSlacRetries(retryCount);
        
        EV << "Retrying SLAC in " << slacRetryBackoff << "s" << endl;
        scheduleAt(simTime() + slacRetryBackoff, new cMessage("startSlac"));
    }
    else {
        emitSlacTimeout();
    }
}

void SlacApplication::resetForRetry()
{
    slacDone = false;
    awaitingResponse = false;
    receivedMessages.clear();
}

void SlacApplication::startDcLoop()
{
    if (dcStarted) return;
    
    dcStarted = true;
    EV << "Starting DC loop" << endl;
    
    // Schedule first DC request
    scheduleAt(simTime(), new cMessage("dcTick"));
}

void SlacApplication::sendDcRequest()
{
    dcReqSeq++;
    simtime_t now = simTime();
    
    // Check for period violation
    bool gapViolation = false;
    if (lastReqTime != 0 && (now - lastReqTime) > dcPeriod) {
        gapViolation = true;
    }
    lastReqTime = now;
    
    // Send DC request
    sendSlacMessage(DC_CUR_DEM_REQ, 300 * 8);
    
    // Schedule next DC request
    scheduleAt(simTime() + dcPeriod, new cMessage("dcTick"));
    
    EV << "Sent DC request #" << dcReqSeq << " (gap violation: " << gapViolation << ")" << endl;
}

void SlacApplication::scheduleMessageTimeout(SlacMessageType expectedType)
{
    awaitingResponse = true;
    awaitingMessageType = expectedType;
    cancelMessageTimeout(); // Cancel any existing timeout
    scheduleAt(simTime() + slacMsgTimeout, messageTimeout);
}

void SlacApplication::cancelMessageTimeout()
{
    if (messageTimeout->isScheduled()) {
        cancelEvent(messageTimeout);
    }
    awaitingResponse = false;
}

void SlacApplication::scheduleProcessTimeout()
{
    cancelProcessTimeout(); // Cancel any existing timeout
    scheduleAt(simTime() + slacProcTimeout, processTimeout);
}

void SlacApplication::cancelProcessTimeout()
{
    if (processTimeout->isScheduled()) {
        cancelEvent(processTimeout);
    }
}

simtime_t SlacApplication::getRandomJitter()
{
    return uniform(-dcRspJitter.dbl(), dcRspJitter.dbl());
}

void SlacApplication::emitSlacComplete(simtime_t completionTime)
{
    emit(slacCompleteSignal, completionTime);
}

void SlacApplication::emitSlacRetries(int retryCount)
{
    emit(slacRetriesSignal, retryCount);
}

void SlacApplication::emitSlacTimeout()
{
    emit(slacTimeoutSignal, 1);
}

int SlacApplication::getMessagePriority(SlacMessageType type)
{
    // Assign CAP based on message type and urgency
    switch (type) {
        case SLAC_PARM_REQ:
        case SLAC_PARM_CNF:
            return 3; // CAP3 - Highest priority for parameter negotiation
            
        case START_ATTEN:
        case MNBC_SOUND:
        case ATTEN_CHAR_IND:
            return 2; // CAP2 - High priority for attenuation characterization
            
        case SLAC_MATCH_REQ:
        case SLAC_MATCH_CNF:
            return 1; // CAP1 - Medium priority for matching
            
        case DC_CUR_DEM_REQ:
        case DC_CUR_DEM_RSP:
            return 0; // CAP0 - Lowest priority for DC loop
            
        default:
            return 0; // Default to CAP0
    }
}

void SlacApplication::finish()
{
    // Don't delete messages in finish() to avoid segmentation fault
    // OMNeT++ will handle cleanup automatically
}
