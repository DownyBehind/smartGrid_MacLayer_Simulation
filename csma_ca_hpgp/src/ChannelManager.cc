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
    // New timing/overhead params
    prs0Param = par("prs0");
    prs1Param = par("prs1");
    beaconPeriodParam = par("beaconPeriod");
    beaconDutyPctParam = par("beaconDutyPct");
    
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
    EV << "PRS0/1: " << prs0Param << "/" << prs1Param << ", Beacon: period=" << beaconPeriodParam << ", duty=" << beaconDutyPctParam << endl;

    // Init arbitration and beacon timers
    arbitrationTimer = new cMessage("arbitrationTimer");
    beaconStartMsg = new cMessage("beaconStart");
    beaconEndMsg = new cMessage("beaconEnd");
    if (beaconPeriodParam > 0 && beaconDutyPctParam > 0) {
        scheduleAt(simTime() + beaconPeriodParam, beaconStartMsg);
    }
    
    // Note: RNG desynchronization will be handled by individual nodes
    // Each node will use its own nodeId as a seed offset for randomization
}

void ChannelManager::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        if (msg == arbitrationTimer) {
            runArbitration();
        } else if (msg == beaconStartMsg) {
            beaconActive = true;
            simtime_t dur = beaconPeriodParam * beaconDutyPctParam;
            // Log beacon busy window
            FILE* f = fopen("results/medium_windows.log", "a");
            if (f) { fprintf(f, "%d,%.6f,%.6f\n", 2, simTime().dbl(), (simTime()+dur).dbl()); fclose(f);} // type=2 beacon
            scheduleAt(simTime() + dur, beaconEndMsg);
        } else if (msg == beaconEndMsg) {
            beaconActive = false;
            scheduleAt(simTime() + (beaconPeriodParam * (1.0 - beaconDutyPctParam)), beaconStartMsg);
        } else {
            // transmission end
            int nodeId = msg->getKind();
            processTransmissionEnd(nodeId);
            delete msg;
        }
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
    
    // Beacon busy blocks all data
    if (beaconActive) {
        cMessage* collisionNotify = new cMessage("collision");
        send(collisionNotify, "nodeOut", nodeId);
        delete frame; return;
    }

    // Check for ISP busy state
    if (ispBusyEnabled && ispBusy) {
        EV << "[" << simTime() << "] ChannelManager: ISP busy, rejecting transmission from node " << nodeId << endl;
        // 즉시 송신자에게 충돌 통지로 재시도를 유도
        cMessage* collisionNotify = new cMessage("collision");
        send(collisionNotify, "nodeOut", nodeId);
        delete frame;
        return;
    }
    
    // Check for impulse noise
    if (impulseNoiseEnabled && impulseNoiseActive) {
        EV << "[" << simTime() << "] ChannelManager: Impulse noise active, rejecting transmission from node " << nodeId << endl;
        cMessage* collisionNotify = new cMessage("collision");
        send(collisionNotify, "nodeOut", nodeId);
        delete frame;
        return;
    }
    
    // Calculate frame duration
    simtime_t duration = calculateFrameDuration(frame);
    
    // Global arbitration: collect requests within PRS window and pick highest CAP
    pendingRequests.push_back({nodeId, frame});
    startArbitrationIfNeeded();
    return;
    
    // (removed) channel idle immediate check; handled by arbitration
    
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

    // Log medium window: data busy interval
    FILE* f = fopen("results/medium_windows.log", "a");
    if (f) {
        // type=1(data), start, end
        fprintf(f, "%d,%.6f,%.6f\n", 1, simTime().dbl(), (simTime()+duration).dbl());
        fclose(f);
    }
    
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
                // Debug: log DC_REQUEST broadcast target
                if (strcmp(broadcastFrame->getName(), "DC_REQUEST") == 0) {
                    printf("[%.3f] ChannelManager: Broadcasting DC_REQUEST from %d to %d\n", simTime().dbl(), nodeId, i);
                    fflush(stdout);
                }
                send(broadcastFrame, "nodeOut", i);
            }
        }
    }
    
    // Confirmation will be sent at transmission end (in processTransmissionEnd)
    
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
    
    // Send confirmation back to sender (txConfirm at end of tx)
    cMessage* confirm = new cMessage("txConfirm");
    send(confirm, "nodeOut", nodeId);

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

    // Log collision instant as a window (type=3) with zero duration for traceability
    FILE* f = fopen("results/medium_windows.log", "a");
    if (f) {
        fprintf(f, "%d,%.6f,%.6f\n", 3, simTime().dbl(), simTime().dbl());
        fclose(f);
    }
    
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

void ChannelManager::startArbitrationIfNeeded()
{
    if (!arbitrationTimer->isScheduled())
        scheduleAt(simTime() + prs0Param + prs1Param, arbitrationTimer);
}

static int frameCap(cMessage* frame) {
    return frame->getKind(); // 0..3 (CAP0..3)
}

void ChannelManager::runArbitration()
{
    if (pendingRequests.empty()) return;
    // Pick highest CAP; policy for equals can be toggled via parameter
    auto bestIt = pendingRequests.begin();
    int bestCap = frameCap(bestIt->frame);
    for (auto it = pendingRequests.begin()+1; it != pendingRequests.end(); ++it) {
        int cap = frameCap(it->frame);
        if (cap > bestCap) { bestCap = cap; bestIt = it; }
    }
    bool equalCapAllCollide = par("equalCapAllCollide");
    int nodeId = bestIt->nodeId;
    cMessage* frame = bestIt->frame;
    if (equalCapAllCollide) {
        // If any other contender has the same CAP as the best, collide all
        bool sameCapExists = false;
        for (auto& pr : pendingRequests) {
            if (&pr == &(*bestIt)) continue;
            if (frameCap(pr.frame) == bestCap) { sameCapExists = true; break; }
        }
        if (sameCapExists) {
            // Notify collision to all contenders
            for (auto& pr : pendingRequests) {
                cMessage* collisionNotify = new cMessage("collision");
                send(collisionNotify, "nodeOut", pr.nodeId);
                delete pr.frame;
            }
            pendingRequests.clear();
            return; // No winner this round
        }
    }
    pendingRequests.erase(bestIt);
    // Reject others as collision so they retry
    for (auto& pr : pendingRequests) {
        cMessage* collisionNotify = new cMessage("collision");
        send(collisionNotify, "nodeOut", pr.nodeId);
        delete pr.frame;
    }
    pendingRequests.clear();
    
    // Allow transmission if channel is not busy (PRS 기반: DIFS 요건은 MAC에서 처리하므로 here에서는 busy만 본다)
    if (channelBusy || beaconActive || !activeTransmitters.empty()) {
        // Only reject if channel is truly busy, not just during PRS
        if (channelBusy || beaconActive) {
            cMessage* collisionNotify = new cMessage("collision");
            send(collisionNotify, "nodeOut", nodeId);
            delete frame;
            return;
        }
        // If only activeTransmitters is not empty but channel is idle, allow transmission
    }
    
    // Proceed with transmission start for the winner
    simtime_t duration = calculateFrameDuration(frame);
    activeTransmitters.push_back(nodeId);
    channelBusy = true;
    currentTransmissionEnd = simTime() + duration;
    lastChannelActivity = simTime();
    FILE* f = fopen("results/medium_windows.log", "a");
    if (f) { fprintf(f, "%d,%.6f,%.6f\n", 1, simTime().dbl(), (simTime()+duration).dbl()); fclose(f);} // data
    cMessage* endTx = new cMessage("endTx");
    endTx->setKind(nodeId);
    transmissionEndEvents[nodeId] = endTx;
    scheduleAt(simTime() + duration, endTx);
    // Broadcast to others (error-free here; PER handled earlier)
    if (!(per > 0 && uniform(0,1) < per)) {
        int numNodes = par("numNodes");
        for (int i=0;i<numNodes;i++) if (i!=nodeId) {
            cMessage* dup = frame->dup();
            if (strcmp(dup->getName(), "DC_REQUEST") == 0) {
                printf("[%.3f] ChannelManager: Broadcasting DC_REQUEST from %d to %d\n", simTime().dbl(), nodeId, i);
                fflush(stdout);
            }
            // EVSE(노드 0)로 전송하는 DC_REQUEST 특별 로깅
            if (i == 0 && strcmp(frame->getName(), "DC_REQUEST") == 0) {
                printf("[%.3f] ChannelManager: Sending DC_REQUEST to EVSE (node 0) via nodeOut[0]\n", simTime().dbl());
                fflush(stdout);
            }
            send(dup, "nodeOut", i);
        }
    }
    // Confirm to sender
    cMessage* confirm = new cMessage("txConfirm");
    send(confirm, "nodeOut", nodeId);
    delete frame;
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
        
        // EVSE(노드 0)로 전송하는 CAP0 프레임 특별 로깅
        if (i == 0 && msg->getKind() == 0) {
            printf("[%.3f] ChannelManager: Sending CAP0 frame '%s' to EVSE (node 0)\n", 
                   simTime().dbl(), msg->getName());
            fflush(stdout);
        }
        
        send(notify, "nodeOut", i);
    }
    delete msg;
}

void ChannelManager::finish()
{
    // Clean up timers and any remaining events
    if (arbitrationTimer && arbitrationTimer->isScheduled()) cancelEvent(arbitrationTimer);
    delete arbitrationTimer; arbitrationTimer = nullptr;
    if (beaconStartMsg && beaconStartMsg->isScheduled()) cancelEvent(beaconStartMsg);
    delete beaconStartMsg; beaconStartMsg = nullptr;
    if (beaconEndMsg && beaconEndMsg->isScheduled()) cancelEvent(beaconEndMsg);
    delete beaconEndMsg; beaconEndMsg = nullptr;
    for (auto& pair : transmissionEndEvents) {
        if (pair.second->isScheduled()) cancelEvent(pair.second);
        delete pair.second;
    }
    transmissionEndEvents.clear();
    for (auto& pr : pendingRequests) delete pr.frame;
    pendingRequests.clear();
}

