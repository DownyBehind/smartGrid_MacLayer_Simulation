//
// Simple SLAC Node for testing
//

#include <omnetpp.h>

using namespace omnetpp;

class SlacNode : public cSimpleModule
{
protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    
private:
    cMessage *selfMsg;
};

Define_Module(SlacNode);

void SlacNode::initialize()
{
    EV << "SlacNode initialized: " << getFullName() << endl;
    
    // Schedule completion event
    selfMsg = new cMessage("slacComplete");
    double delay = uniform(1.0, 5.0);  // Random completion time
    scheduleAt(simTime() + delay, selfMsg);
}

void SlacNode::handleMessage(cMessage *msg)
{
    if (msg == selfMsg) {
        EV << "SLAC completed for " << getFullName() << " at " << simTime() << endl;
        
        // Emit signal
        simsignal_t signal = registerSignal("slacComplete");
        emit(signal, simTime());
        
        delete msg;
        selfMsg = nullptr;
    }
}
