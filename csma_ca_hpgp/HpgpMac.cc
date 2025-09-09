#include "HpgpMac.h"

Define_Module(HpgpMac);

void HpgpMac::initialize()
{
    // Get HomePlug 1.0 standard parameters
    cifs = par("cifs");
    rifs = par("rifs");
    prs0 = par("prs0");
    prs1 = par("prs1");
    slotTime = par("slotTime");
    bpcMax = par("bpcMax");
    
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
    
    // Start with PRS0 + PRS1 delay
    scheduleAt(simTime() + prs0 + prs1, slotTimer);
}

void HpgpMac::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        if (msg == slotTimer) {
            // Main slot processing
            bool busy = senseChannelBusy();
            
            if (busy) {
                if (bc > 0) bc--;
                if (dc > 0) dc--;
                if (dc == 0 && busy) {
                    setStageByBpc(bpc + 1); // Congestion estimation
                }
            } else {
                if (bc > 0) bc--;
            }
            
            if (bc == 0) {
                bool success = tryTransmitFrame();
                if (success) {
                    setStageByBpc(0); // Reset on success
                    // PRS + RIFS + CIFS delay before next competition
                    scheduleAt(simTime() + rifs + cifs + prs0 + prs1, slotTimer);
                    return;
                } else {
                    setStageByBpc(bpc + 1); // Collision - increase BPC
                }
            }
            
            scheduleAt(simTime() + slotTime, slotTimer);
        }
        else if (msg == priorityResolutionTimer) {
            processPriorityResolution();
        }
    }
    else {
        // Handle incoming messages
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
            enqueueFrame(msg);
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

void HpgpMac::processTxQueue()
{
    if (txQueue.empty()) {
        return;
    }
    
    if (isChannelIdle()) {
        startPriorityResolution();
    }
    else {
        startDeferral();
    }
}

void HpgpMac::startBackoff()
{
    if (txQueue.empty()) {
        return;
    }
    
    cMessage* frame = txQueue.front();
    Priority priority = getFramePriority(frame);
    
    // Calculate backoff counter
    int cw = getTableIParams(bpc).cw;
    bc = intuniform(0, cw - 1);
    
    EV << "Starting backoff with counter: " << bc << endl;
    
    if (bc == 0) {
        attemptTransmission();
    }
    else {
        scheduleAt(simTime() + slotTime, slotTimer);
    }
}

void HpgpMac::startDeferral()
{
    if (txQueue.empty()) {
        return;
    }
    
    // Defer transmission until channel is idle
    scheduleAt(simTime() + slotTime, slotTimer);
}

void HpgpMac::attemptTransmission()
{
    if (txQueue.empty()) {
        return;
    }
    
    if (waitingForChannelResponse) {
        // Already waiting for channel response
        return;
    }
    
    cMessage* frame = txQueue.front();
    txQueue.pop();
    
    if (frame == nullptr) {
        EV << "Error: frame is nullptr" << endl;
        return;
    }
    
    emitTxAttempt();
    
    // Send frame to Channel Manager (duplicate to avoid ownership issues)
    cMessage* frameCopy = frame->dup();
    if (frameCopy == nullptr) {
        EV << "Error: frameCopy is nullptr" << endl;
        delete frame;
        return;
    }
    
    currentFrame = frameCopy;
    waitingForChannelResponse = true;
    
    send(frameCopy, "out");
    
    // Delete original frame
    delete frame;
    
    EV << "[" << simTime() << "] HpgpMac: Sent frame to Channel Manager for transmission" << endl;
}

void HpgpMac::onTransmissionComplete(bool success)
{
    waitingForChannelResponse = false;
    currentFrame = nullptr;
    
    if (success) {
        emitTxSuccess();
        EV << "Transmission successful" << endl;
        
        // Reset backoff procedure
        setStageByBpc(0);
    }
    else {
        onCollision();
    }
}

void HpgpMac::onCollision()
{
    emitTxCollision();
    EV << "Transmission collision" << endl;
    
    // Increase backoff procedure counter
    setStageByBpc(bpc + 1);
}

void HpgpMac::startPriorityResolution()
{
    if (txQueue.empty()) {
        return;
    }
    
    cMessage* frame = txQueue.front();
    currentPriority = getFramePriority(frame);
    
    inPriorityResolution = true;
    priorityResolutionSlot = 0;
    
    EV << "[" << simTime() << "] HpgpMac: Starting Priority Resolution for priority " << currentPriority << endl;
    printf("[%.3f] HpgpMac: Starting Priority Resolution for priority %d\n", simTime().dbl(), currentPriority);
    
    // Schedule first priority resolution slot
    scheduleAt(simTime() + slotTime, priorityResolutionTimer);
}

void HpgpMac::processPriorityResolution()
{
    if (!inPriorityResolution) {
        return;
    }
    
    priorityResolutionSlot++;
    
    EV << "[" << simTime() << "] HpgpMac: Processing Priority Resolution slot " << priorityResolutionSlot << endl;
    printf("[%.3f] HpgpMac: Processing Priority Resolution slot %d\n", simTime().dbl(), priorityResolutionSlot);
    
    if (priorityResolutionSlot >= 2) {
        // Priority resolution complete
        onPriorityResolutionComplete();
    }
    else {
        // Continue to next slot
        scheduleAt(simTime() + slotTime, priorityResolutionTimer);
    }
}

void HpgpMac::onPriorityResolutionComplete()
{
    inPriorityResolution = false;
    priorityResolutionSlot = 0;
    
    EV << "[" << simTime() << "] HpgpMac: Priority Resolution complete, starting backoff" << endl;
    printf("[%.3f] HpgpMac: Priority Resolution complete, starting backoff\n", simTime().dbl());
    
    // Now start the actual backoff procedure
    startBackoff();
}

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
    printf("[%.3f] HpgpMac: BPC=%d, DC=%d, CW=%d, BC=%d\n", simTime().dbl(), bpc, dc, cw, bc);
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

void HpgpMac::finish()
{
    // Don't delete messages in finish() to avoid segmentation fault
    // OMNeT++ will handle cleanup automatically
}