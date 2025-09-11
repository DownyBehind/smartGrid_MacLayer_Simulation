#include "ChannelManager.h"
#include <algorithm>

Define_Module(ChannelManager);

void ChannelManager::initialize()
{
    // Get parameters
    slotTime = par("slotTime");
    sifs = par("sifs");
    difs = par("difs");
    bitrate = par("bitrate");
    
    // Channel model parameters
    per = par("per");
    impulseNoiseEnabled = par("impulseNoiseEnabled");
    ispBusyEnabled = par("ispBusyEnabled");
    impulseDuration = par("impulseDuration");
    ispBusyProbability = par("ispBusyProbability");
    ispBusyMeanDuration = par("ispBusyMeanDuration");
    
    // Initialize channel state
    channelBusy = false;
    lastChannelActivity = 0;
    currentTransmissionEnd = 0;
    ispBusy = false;
    impulseNoiseActive = false;
    
    // Register signals
    collisionSignal = registerSignal("collision");
    channelUtilizationSignal = registerSignal("channelUtilization");
    mediumBusySignal = registerSignal("mediumBusy");
    collisionCountSignal = registerSignal("collisionCount");
    
    // Initialize statistics
    collisionCount = 0;
    
    EV << "[" << simTime() << "] ChannelManager initialized with " << par("numNodes") << " nodes" << endl;
    EV << "Channel model: PER=" << per << ", Impulse=" << impulseNoiseEnabled << ", ISP=" << ispBusyEnabled << endl;
}

void ChannelManager::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        // Handle transmission end events
        int nodeId = msg->getKind();
        processTransmissionEnd(nodeId);
        delete msg;
    }
    else {
        // Handle transmission requests from nodes
        int gateIndex = msg->getArrivalGate()->getIndex();
        processTransmissionRequest(gateIndex, msg);
    }
}

void ChannelManager::processTransmissionRequest(int nodeId, cMessage* frame)
{
    EV << "[" << simTime() << "] ChannelManager: Received transmission request from node " << nodeId << endl;
    printf("[%.3f] ChannelManager: Received transmission request from node %d\n", simTime().dbl(), nodeId);
    
    // Check if nodeId is within valid range
    if (nodeId >= gateSize("nodeOut")) {
        EV << "Error: nodeId " << nodeId << " out of range (max: " << gateSize("nodeOut")-1 << ")" << endl;
        delete frame;
        return;
    }
    
    // Check for ISP busy state
    if (ispBusyEnabled && ispBusy) {
        EV << "[" << simTime() << "] ChannelManager: ISP busy, deferring transmission from node " << nodeId << endl;
        delete frame;
        return;
    }
    
    // Check for impulse noise
    if (impulseNoiseEnabled && impulseNoiseActive) {
        EV << "[" << simTime() << "] ChannelManager: Impulse noise active, deferring transmission from node " << nodeId << endl;
        delete frame;
        return;
    }
    
    // Calculate frame duration
    simtime_t duration = calculateFrameDuration(frame);
    
    // Check for collision with ongoing transmissions
    if (!activeTransmitters.empty()) {
        // Collision detected - multiple nodes trying to transmit simultaneously
        EV << "[" << simTime() << "] ChannelManager: Collision detected! Node " << nodeId << " collided with ongoing transmissions" << endl;
        printf("[%.3f] ChannelManager: Collision detected! Node %d collided with ongoing transmissions\n", simTime().dbl(), nodeId);
        detectCollision();
        delete frame;
        return;
    }
    
    // Check if channel is idle (DIFS period)
    if (!isChannelIdle()) {
        // Channel busy, defer transmission
        EV << "[" << simTime() << "] ChannelManager: Channel busy, deferring transmission from node " << nodeId << endl;
        printf("[%.3f] ChannelManager: Channel busy, deferring transmission from node %d\n", simTime().dbl(), nodeId);
        delete frame;
        return;
    }
    
    // Simulate packet error rate (PER)
    bool frameError = false;
    if (per > 0 && uniform(0, 1) < per) {
        frameError = true;
        EV << "[" << simTime() << "] ChannelManager: Frame error due to PER=" << per << endl;
    }
    
    // Start transmission
    activeTransmitters.push_back(nodeId);
    channelBusy = true;
    currentTransmissionEnd = simTime() + duration;
    lastChannelActivity = simTime();
    
    // Schedule transmission end
    cMessage* endTx = new cMessage("endTx");
    endTx->setKind(nodeId);
    transmissionEndEvents[nodeId] = endTx;
    scheduleAt(simTime() + duration, endTx);
    
    // Broadcast frame to all other nodes (only if no error)
    if (!frameError) {
        int numNodes = par("numNodes");
        for (int i = 0; i < numNodes; i++) {
            if (i != nodeId) {
                cMessage* broadcastFrame = frame->dup();
                send(broadcastFrame, "nodeOut", i);
            }
        }
    }
    
    // Send confirmation back to sender
    cMessage* confirm = new cMessage("txConfirm");
    send(confirm, "nodeOut", nodeId);
    
    // Update statistics
    emit(mediumBusySignal, 1.0);
    
    EV << "[" << simTime() << "] ChannelManager: Transmission started from node " << nodeId << " for " << duration << "s" << endl;
    printf("[%.3f] ChannelManager: Transmission started from node %d for %.6fs\n", simTime().dbl(), nodeId, duration.dbl());
}

void ChannelManager::processTransmissionEnd(int nodeId)
{
    EV << "Transmission ended from node " << nodeId << endl;
    
    // Remove from active transmitters
    auto it = std::find(activeTransmitters.begin(), activeTransmitters.end(), nodeId);
    if (it != activeTransmitters.end()) {
        activeTransmitters.erase(it);
    }
    
    // Remove from transmission events
    transmissionEndEvents.erase(nodeId);
    
    // Update channel state
    updateChannelState();
    
    // Notify all nodes that channel is idle
    if (activeTransmitters.empty()) {
        cMessage* idleNotify = new cMessage("channelIdle");
        notifyAllNodes(idleNotify);
    }
}

void ChannelManager::detectCollision()
{
    EV << "Collision detected!" << endl;
    
    // Update collision statistics
    collisionCount++;
    emit(collisionSignal, 1);
    emit(collisionCountSignal, collisionCount);
    
    // Notify all nodes about collision
    cMessage* collisionNotify = new cMessage("collision");
    notifyAllNodes(collisionNotify);
    
    // Clear all active transmissions
    for (auto& pair : transmissionEndEvents) {
        cancelEvent(pair.second);
        delete pair.second;
    }
    transmissionEndEvents.clear();
    activeTransmitters.clear();
    
    // Update channel state
    updateChannelState();
}

void ChannelManager::updateChannelState()
{
    channelBusy = !activeTransmitters.empty();
    if (!channelBusy) {
        currentTransmissionEnd = 0;
    }
    
    // Emit channel utilization
    double utilization = channelBusy ? 1.0 : 0.0;
    emit(channelUtilizationSignal, utilization);
}

simtime_t ChannelManager::calculateFrameDuration(cMessage* frame)
{
    int bits = 1000; // Default frame size
    if (cPacket* packet = dynamic_cast<cPacket*>(frame)) {
        bits = packet->getBitLength();
    }
    return (double)bits / bitrate;
}

bool ChannelManager::isChannelIdle()
{
    return !channelBusy && (simTime() - lastChannelActivity) >= difs;
}

void ChannelManager::notifyAllNodes(cMessage* msg)
{
    // Only send to connected nodes (use numNodes parameter)
    int numNodes = par("numNodes");
    for (int i = 0; i < numNodes; i++) {
        cMessage* notify = msg->dup();
        send(notify, "nodeOut", i);
    }
    delete msg;
}

void ChannelManager::finish()
{
    // Clean up any remaining events
    for (auto& pair : transmissionEndEvents) {
        if (pair.second->isScheduled()) {
            cancelEvent(pair.second);
        }
        delete pair.second;
    }
}

