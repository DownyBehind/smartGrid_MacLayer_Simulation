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
    
    // Initialize channel state
    channelBusy = false;
    lastChannelActivity = 0;
    currentTransmissionEnd = 0;
    
    // Register signals
    collisionSignal = registerSignal("collision");
    channelUtilizationSignal = registerSignal("channelUtilization");
    
    EV << "[" << simTime() << "] ChannelManager initialized with " << par("numNodes") << " nodes" << endl;
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
    EV << "Received transmission request from node " << nodeId << endl;
    
    // Check if nodeId is within valid range
    if (nodeId >= gateSize("nodeOut")) {
        EV << "Error: nodeId " << nodeId << " out of range (max: " << gateSize("nodeOut")-1 << ")" << endl;
        delete frame;
        return;
    }
    
    // Check if channel is idle
    if (!isChannelIdle()) {
        // Channel busy, defer transmission
        EV << "Channel busy, deferring transmission from node " << nodeId << endl;
        // For now, just drop the frame (could implement queuing)
        delete frame;
        return;
    }
    
    // Calculate frame duration
    simtime_t duration = calculateFrameDuration(frame);
    
    // Check for collision with ongoing transmissions
    if (!activeTransmitters.empty()) {
        // Collision detected
        EV << "Collision detected with ongoing transmissions" << endl;
        detectCollision();
        delete frame;
        return;
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
    
    // Broadcast frame to all other nodes
    int numNodes = par("numNodes");
    for (int i = 0; i < numNodes; i++) {
        if (i != nodeId) {
            cMessage* broadcastFrame = frame->dup();
            send(broadcastFrame, "nodeOut", i);
        }
    }
    
    // Send confirmation back to sender
    cMessage* confirm = new cMessage("txConfirm");
    send(confirm, "nodeOut", nodeId);
    
    EV << "Transmission started from node " << nodeId << " for " << duration << "s" << endl;
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
    
    // Emit collision signal
    emit(collisionSignal, 1);
    
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

