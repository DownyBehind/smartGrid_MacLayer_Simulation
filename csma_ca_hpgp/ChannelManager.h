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
    
    // Parameters
    double slotTime;
    double sifs;
    double difs;
    double bitrate;
    
    // Statistics
    simsignal_t collisionSignal;
    simsignal_t channelUtilizationSignal;
    
protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
    virtual void finish() override;
    
    // Channel management
    void processTransmissionRequest(int nodeId, cMessage* frame);
    void processTransmissionEnd(int nodeId);
    void detectCollision();
    void updateChannelState();
    
    // Utility functions
    simtime_t calculateFrameDuration(cMessage* frame);
    bool isChannelIdle();
    void notifyAllNodes(cMessage* msg);
};

#endif // CHANNELMANAGER_H

