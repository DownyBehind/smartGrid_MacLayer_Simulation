//
// Simple SLAC Application for testing
// Minimal implementation for demonstration
//

#include "inet/common/ModuleAccess.h"

namespace csma_ca_hpgp {

class SlacApplication : public cSimpleModule
{
  protected:
    // Parameters
    std::string nodeType;
    int nodeId;
    simtime_t slacMsgTimeout;
    simtime_t slacProcTimeout;
    
    // State
    enum SlacState { IDLE, RUNNING, COMPLETED, FAILED };
    SlacState currentState;
    
    // Timers
    cMessage *startTimer;
    cMessage *timeoutTimer;
    
    simtime_t slacStartTime;
    
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void startSlacProcedure();
    virtual void completeSlacProcedure(bool success);
    virtual void finish() override;
};

Define_Module(SlacApplication);

void SlacApplication::initialize()
{
    nodeType = par("nodeType").stdstringValue();
    nodeId = par("nodeId").intValue();
    slacMsgTimeout = par("slacMsgTimeout");
    slacProcTimeout = par("slacProcTimeout");
    
    currentState = IDLE;
    
    startTimer = new cMessage("startSlac");
    timeoutTimer = new cMessage("timeout");
    
    EV_INFO << "SLAC Application initialized for " << nodeType << " node " << nodeId << endl;
    
    // Schedule SLAC start with small delay
    scheduleAt(simTime() + uniform(0, 0.1), startTimer);
}

void SlacApplication::handleMessage(cMessage *msg)
{
    if (msg == startTimer) {
        startSlacProcedure();
    }
    else if (msg == timeoutTimer) {
        EV_WARN << "SLAC procedure timeout" << endl;
        completeSlacProcedure(false);
    }
    else {
        delete msg;
    }
}

void SlacApplication::startSlacProcedure()
{
    EV_INFO << "Starting SLAC procedure for " << nodeType << " node " << nodeId << endl;
    
    currentState = RUNNING;
    slacStartTime = simTime();
    
    // Schedule procedure timeout
    scheduleAt(simTime() + slacProcTimeout, timeoutTimer);
    
    // Simulate SLAC procedure duration based on node type
    simtime_t slacDuration;
    if (nodeType == "EVSE") {
        slacDuration = uniform(1.0, 3.0);  // EVSE takes 1-3 seconds
    } else {
        slacDuration = uniform(2.0, 5.0);  // EV takes 2-5 seconds  
    }
    
    scheduleAt(simTime() + slacDuration, new cMessage("slacComplete"));
    
    EV_INFO << "SLAC will complete in " << slacDuration << "s" << endl;
}

void SlacApplication::completeSlacProcedure(bool success)
{
    cancelEvent(timeoutTimer);
    
    simtime_t completionTime = simTime() - slacStartTime;
    
    if (success) {
        EV_INFO << "SLAC completed successfully in " << completionTime << "s" << endl;
        currentState = COMPLETED;
    } else {
        EV_ERROR << "SLAC failed after " << completionTime << "s" << endl;
        currentState = FAILED;
    }
    
    // Record statistics
    recordScalar("slacCompletionTime", completionTime);
    recordScalar("slacSuccess", success ? 1 : 0);
}

void SlacApplication::finish()
{
    cSimpleModule::finish();
    
    if (currentState == COMPLETED) {
        EV_INFO << "Node " << nodeId << " (" << nodeType << ") SLAC successful" << endl;
    } else {
        EV_INFO << "Node " << nodeId << " (" << nodeType << ") SLAC failed" << endl;
    }
}

} // namespace

using namespace csma_ca_hpgp;
