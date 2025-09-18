#ifndef CHANNELMANAGER_H
#define CHANNELMANAGER_H

#include <omnetpp.h>
#include <vector>
#include <map>

using namespace omnetpp;

class ChannelManager : public cSimpleModule
{
private:
    // Channel state
    bool channelBusy;
    simtime_t lastChannelActivity;
    simtime_t currentTransmissionEnd;
    
    // Active transmissions
    std::vector<int> activeTransmitters;
    std::map<int, cMessage*> transmissionEndEvents;
    
    // Arbitration window (global PRS)
    struct PendingReq { int nodeId; cMessage* frame; };
    std::vector<PendingReq> pendingRequests;
    cMessage* arbitrationTimer = nullptr;
    simtime_t prsWindow = 0;
    
    // Parameters
    double slotTime;
    double sifs;
    double difs;
    double bitrate;
    double prs0Param = 0;
    double prs1Param = 0;
    
    // Beacon parameters/state
    simtime_t beaconPeriodParam = 0;
    double beaconDutyPctParam = 0;
    bool beaconActive = false;
    cMessage* beaconStartMsg = nullptr;
    cMessage* beaconEndMsg = nullptr;
    
    // Channel model parameters
    double per;
    bool impulseNoiseEnabled;
    bool ispBusyEnabled;
    simtime_t impulseDuration;
    double ispBusyProbability;
    simtime_t ispBusyMeanDuration;
    
    // Channel state
    bool ispBusy;
    bool impulseNoiseActive;
    
    // Statistics
    simsignal_t collisionSignal;
    simsignal_t channelUtilizationSignal;
    simsignal_t mediumBusySignal;
    simsignal_t collisionCountSignal;
    int collisionCount;
    
protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
    virtual void finish() override;
    
    // Channel management
    void processTransmissionRequest(int nodeId, cMessage* frame);
    void processTransmissionEnd(int nodeId);
    void detectCollision();
    void updateChannelState();
    void startArbitrationIfNeeded();
    void runArbitration();
    
    // Utility functions
    simtime_t calculateFrameDuration(cMessage* frame);
    bool isChannelIdle();
    void notifyAllNodes(cMessage* msg);
};

#endif // CHANNELMANAGER_H

