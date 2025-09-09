#include "HpgpMac.h"

Define_Module(HpgpMac);

void HpgpMac::initialize()
{
    // Get parameters
    cwMin = par("cwMin");
    cwMax = par("cwMax");
    maxRetries = par("maxRetries");
    slotTime = par("slotTime");
    sifs = par("sifs");
    difs = par("difs");
    
    // Initialize priority-specific parameters
    capCwMin[CAP0] = par("cap0CwMin");
    capCwMin[CAP1] = par("cap1CwMin");
    capCwMin[CAP2] = par("cap2CwMin");
    capCwMin[CAP3] = par("cap3CwMin");
    
    capCwMax[CAP0] = par("cap0CwMax");
    capCwMax[CAP1] = par("cap1CwMax");
    capCwMax[CAP2] = par("cap2CwMax");
    capCwMax[CAP3] = par("cap3CwMax");
    
    // Initialize state
    backoffCounter = 0;
    deferralCounter = 0;
    backoffProcedureCounter = 0;
    channelBusy = false;
    lastChannelActivity = 0;
    waitingForChannelResponse = false;
    currentFrame = nullptr;
    
    // Create timers
    backoffTimer = new cMessage("backoffTimer");
    deferralTimer = new cMessage("deferralTimer");
    
    // Register signals
    txAttemptsSignal = registerSignal("txAttempts");
    txSuccessSignal = registerSignal("txSuccess");
    txCollisionSignal = registerSignal("txCollision");
    txDropSignal = registerSignal("txDrop");
}

void HpgpMac::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        if (msg == backoffTimer) {
            attemptTransmission();
        }
        else if (msg == deferralTimer) {
            processTxQueue();
        }
    }
    else {
        // Handle incoming messages
        if (strcmp(msg->getName(), "txConfirm") == 0) {
            // Transmission confirmed by channel manager
            onTransmissionComplete(true);
        }
        else if (strcmp(msg->getName(), "collision") == 0) {
            // Collision detected by channel manager
            onTransmissionComplete(false);
        }
        else if (strcmp(msg->getName(), "channelIdle") == 0) {
            // Channel became idle
            if (!txQueue.empty() && !backoffTimer->isScheduled() && !deferralTimer->isScheduled()) {
                processTxQueue();
            }
        }
        else {
            // Handle incoming frame
            enqueueFrame(msg);
            // Don't delete msg here - enqueueFrame will handle it
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
    
    if (!backoffTimer->isScheduled() && !deferralTimer->isScheduled()) {
        processTxQueue();
    }
}

void HpgpMac::processTxQueue()
{
    if (txQueue.empty()) {
        return;
    }
    
    if (isChannelIdle()) {
        startBackoff();
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
    int cw = getCw(priority);
    backoffCounter = intuniform(0, cw - 1);
    
    EV << "Starting backoff with counter: " << backoffCounter << endl;
    
    if (backoffCounter == 0) {
        attemptTransmission();
    }
    else {
        scheduleAt(simTime() + slotTime, backoffTimer);
    }
}

void HpgpMac::startDeferral()
{
    if (txQueue.empty()) {
        return;
    }
    
    // Defer transmission until channel is idle
    scheduleAt(simTime() + slotTime, deferralTimer);
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
        backoffProcedureCounter = 0;
        deferralCounter = 0;
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
    backoffProcedureCounter++;
    
    if (backoffProcedureCounter >= maxRetries) {
        emitTxDrop();
        EV << "Max retries exceeded, dropping frame" << endl;
    }
    else {
        // Re-queue frame and retry
        cMessage* frame = txQueue.front();
        txQueue.pop();
        txQueue.push(frame);
        
        // Start new backoff
        startBackoff();
    }
}

int HpgpMac::getCw(Priority priority)
{
    int cw = capCwMin[priority] * (1 << backoffProcedureCounter);
    return std::min(cw, capCwMax[priority]);
}

HpgpMac::Priority HpgpMac::getFramePriority(cMessage* frame)
{
    // Default to CAP0, could be enhanced to read from frame
    return CAP0;
}

simtime_t HpgpMac::getFrameDuration(cMessage* frame)
{
    // Calculate duration based on frame size and bitrate
    double bitrate = par("bitrate");
    int bits = 1000; // Default frame size
    if (cPacket* packet = dynamic_cast<cPacket*>(frame)) {
        bits = packet->getBitLength();
    }
    return (double)bits / bitrate;
}

bool HpgpMac::isChannelIdle()
{
    return !channelBusy && (simTime() - lastChannelActivity) >= difs;
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
