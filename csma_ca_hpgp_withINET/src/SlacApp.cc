#include <omnetpp.h>
#include "inet/linklayer/plc/PLCFrame_m.h"

using namespace omnetpp;
using namespace inet;

class SlacApp : public cSimpleModule {
  private:
    std::string role;
    int nodeId;
    int numStartAtten;
    int numMsound;
    int startPriority;
    simtime_t startJitter;
    simtime_t dcPeriod;
    int dcPriority;
    bool enableDcPriorityCycle = false; // legacy name
    bool enablePriorityCycle = false;   // new unified switch
    simtime_t dcRspDelay;
    cMessage* startMsg = nullptr;
    cMessage* dcTick = nullptr;
    cMessage* slacDone = nullptr;
    int seq = 0;
    // stats
    int dcReqSent = 0;
    int dcRspSent = 0;
    int dcRspRecv = 0;
    int dcRspMatch = 0;
    double dcLatSum = 0.0;
    double dcLatMin = 0.0;
    double dcLatMax = 0.0;
    int dcLatCount = 0;
    simsignal_t dcReqSignal;
    simsignal_t dcRspSignal;
    simsignal_t dcLatencySignal;
  protected:
    virtual void initialize() override {
        role = par("role").stdstringValue();
        nodeId = par("nodeId");
        numStartAtten = par("numStartAtten");
        numMsound = par("numMsound");
        startPriority = par("startPriority");
        startJitter = par("startJitter");
        dcPeriod = par("dcPeriod");
        dcPriority = par("dcPriority");
        if (hasPar("enableDcPriorityCycle"))
            enableDcPriorityCycle = par("enableDcPriorityCycle");
        if (hasPar("enablePriorityCycle"))
            enablePriorityCycle = par("enablePriorityCycle");
        if (enablePriorityCycle || enableDcPriorityCycle) {
            EV_WARN << "This is Priority Cycle Mode!!! it is not a charging protocol environment!!" << endl;
            EV_INFO << "This is Priority Cycle Mode!!! it is not a charging protocol environment!!" << endl;
        }
        dcRspDelay = par("dcRspDelay");
        startMsg = new cMessage("start");
        // add small positive offset to avoid t=0 race/alloc issues
        scheduleAt(simTime() + startJitter + 0.0001, startMsg);
        dcReqSignal = registerSignal("dcReqSent");
        dcRspSignal = registerSignal("dcRspRecv");
        dcLatencySignal = registerSignal("dcLatency");
        dcLatMin = 0.0;
        dcLatMax = 0.0;
        dcLatSum = 0.0;
        dcLatCount = 0;
    }
    virtual void handleMessage(cMessage* msg) override {
        if (msg->isSelfMessage()) {
            if (msg == startMsg) {
                if (role == "EV") {
                    // Use PLCFrame directly so MAC can process it
                    auto sendPlc = [&](int prio){
                        auto *f = new PLCFrame("PLC");
                        f->setFrameType(2); // control-like
                        f->setPriority(prio);
                        f->setSrcAddr(nodeId);
                        f->setDestAddr(0);
                        f->setPayloadLength(300);
                        f->setByteLength(300);
                        f->setAckRequired(false);
                        send(f, "out");
                    };
                    // SLAC sequence as burst with configured priority
                    sendPlc(startPriority); // SLAC_PARM_REQ
                    for (int i=0;i<numStartAtten;i++) sendPlc(startPriority);
                    for (int i=0;i<numMsound;i++) sendPlc(startPriority);
                    sendPlc(startPriority); // ATTEN_CHAR_RSP
                    sendPlc(startPriority); // SLAC_MATCH_REQ
                }
                if (!slacDone) slacDone = new cMessage("slacDone");
                scheduleAt(simTime(), slacDone);
                dcTick = new cMessage("dcTick");
                scheduleAt(simTime(), dcTick);
                // consume startMsg
                startMsg = nullptr;
                delete msg;
                return;
            } else if (!strcmp(msg->getName(), "dcTick")) {
                if (role == "EV") {
                    auto *req = new PLCFrame("DC_REQUEST");
                    req->setFrameType(2);
                    req->setPriority((enablePriorityCycle||enableDcPriorityCycle)? dcPriority : 0);
                    req->setSrcAddr(nodeId);
                    req->setDestAddr(0);
                    req->setPayloadLength(300);
                    req->setByteLength(300);
                    req->setAckRequired(false);
                    req->setTimestamp();
                    EV_INFO << "CAP_LOG node=" << getParentModule()->getFullName() << " cap=" << req->getPriority() << " t=" << simTime() << endl;
                    send(req, "out");
                    dcReqSent++;
                    emit(dcReqSignal, dcReqSent);
                    // cycle DC priority after sending if enabled
                    if (enablePriorityCycle || enableDcPriorityCycle) {
                        if (dcPriority > 0) dcPriority -= 1; else dcPriority = 3;
                    }
                }
                scheduleAt(simTime() + dcPeriod, dcTick);
                // do NOT delete dcTick when rescheduling
                return;
            } else if (!strcmp(msg->getName(), "dcRspEnq")) {
                // EVSE delayed response enqueue
                auto *rsp = static_cast<PLCFrame*>(msg->getContextPointer());
                EV_INFO << "CAP_LOG node=" << getParentModule()->getFullName() << " cap=" << rsp->getPriority() << " t=" << simTime() << endl;
                send(rsp, "out");
                dcRspSent++;
                delete msg;
                return;
            }
            delete msg;
        } else {
            // incoming from MAC
            PLCFrame *f = dynamic_cast<PLCFrame*>(msg);
            if (!f) { delete msg; return; }
            if (role == "EVSE" && strcmp(f->getName(), "DC_REQUEST") == 0) {
                // schedule delayed response
                auto *rsp = new PLCFrame("DC_RESPONSE");
                rsp->setFrameType(2);
                // EVSE ACK is fixed at CAP3 for responsiveness per requirement
                rsp->setPriority(3);
                rsp->setSrcAddr(nodeId);
                rsp->setDestAddr(f->getSrcAddr());
                rsp->setPayloadLength(300);
                rsp->setByteLength(300);
                rsp->setAckRequired(false);
                // carry original timestamp to compute latency at EV side
                rsp->setTimestamp(f->getTimestamp());
                cMessage *enq = new cMessage("dcRspEnq");
                enq->setContextPointer(rsp);
                scheduleAt(simTime() + dcRspDelay, enq);
                delete f;
                return;
            }
            if (role == "EV" && strcmp(f->getName(), "DC_RESPONSE") == 0) {
                dcRspRecv++;
                emit(dcRspSignal, dcRspRecv);
                simtime_t lat = simTime() - f->getTimestamp();
                emit(dcLatencySignal, lat.dbl());
                // latency aggregates
                double l = lat.dbl();
                if (dcLatCount == 0) {
                    dcLatMin = l; dcLatMax = l;
                } else {
                    if (l < dcLatMin) dcLatMin = l;
                    if (l > dcLatMax) dcLatMax = l;
                }
                dcLatSum += l;
                dcLatCount++;
                // consider matched if destAddr is this EV and src nonzero
                dcRspMatch++;
                delete f;
                return;
            }
            delete f;
        }
    }
    virtual void finish() override {
        if (startMsg && startMsg->isScheduled()) cancelEvent(startMsg);
        delete startMsg; startMsg=nullptr;
        if (dcTick) {
            if (dcTick->isScheduled()) cancelEvent(dcTick);
            delete dcTick; dcTick=nullptr;
        }
        if (slacDone) {
            if (slacDone->isScheduled()) cancelEvent(slacDone);
            delete slacDone; slacDone=nullptr;
        }
        recordScalar("dcReqSent", dcReqSent);
        recordScalar("dcRspSent", dcRspSent);
        recordScalar("dcRspRecv", dcRspRecv);
        double matchRate = (dcReqSent > 0) ? ((double)dcRspRecv / dcReqSent * 100.0) : 0.0;
        recordScalar("dcMatchRate(%)", matchRate);
        if (dcLatCount > 0) {
            double avg = dcLatSum / dcLatCount;
            recordScalar("dcLatencyAvg(s)", avg);
            recordScalar("dcLatencyMin(s)", dcLatMin);
            recordScalar("dcLatencyMax(s)", dcLatMax);
        } else {
            recordScalar("dcLatencyAvg(s)", 0.0);
            recordScalar("dcLatencyMin(s)", 0.0);
            recordScalar("dcLatencyMax(s)", 0.0);
        }
    }
};

Define_Module(SlacApp);
