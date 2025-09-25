#include <omnetpp.h>
#include "inet/linklayer/plc/PLCFrame_m.h"
#include <vector>
#include <algorithm>
#include <map>
#include <string>

using namespace omnetpp;
using namespace inet;
#include <set>

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
    bool simulateNoEvse = false;        // observer-only switch
    bool testJamOnMatchCnf = false;     // test-only: emulate jamming at match CNF
    int msoundDropEveryK = 0;           // test-only: drop every K-th M_SOUND if >0
    bool testInjectPostSlacMsgs = false; // test-only: emit CAP1-3 probes after SLAC
    bool testAllowPreSlacSweep = false;  // test-only: allow CAP sweep before SLAC completion
    cMessage* postSlacSweep = nullptr;
    simtime_t testPostSlacPeriod = SIMTIME_ZERO;
    bool testSyncStart = false;        // test-only: align START/PRS across nodes
    bool testDisableDc = false;       // test-only: suppress DC_REQUEST generation
    bool testForceCap0Only = false;  // test-only: force all DC traffic to CAP0
    bool testCycleCap123 = false;    // test-only: rotate CAP1/2/3 probes
    int capCycleIndex = 0;
    cMessage* startMsg = nullptr;
    cMessage* dcTick = nullptr;
    cMessage* slacDone = nullptr;
    cMessage* heartbeat = nullptr; // periodic scalar heartbeat
    bool slacCompleted = false;
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
    std::vector<double> dcLatSamples;
    // airtime / deadline metrics (observer-only, no behavior change)
    simtime_t lastDcReqSentTime = SIMTIME_ZERO;
    bool hasLastDcReq = false;
    int dcDeadlineMissCount = 0; // airtime > 100ms
    int dcReqIntervalCount = 0;  // number of intervals after SLAC_DONE
    int dcReqIntervalDelayedCount = 0; // intervals > 100ms
    // robust request/response matching by sequence id
    int dcReqSeq = 0;
    std::map<int, simtime_t> dcReqSendTimesBySeq;
    // EVSE: track which EV IDs have already received SLAC_MATCH_CNF to avoid redundant emits
    std::set<int> cnfSentTo;
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
        if (hasPar("simulateNoEvse"))
            simulateNoEvse = par("simulateNoEvse");
        if (hasPar("testJamOnMatchCnf"))
            testJamOnMatchCnf = par("testJamOnMatchCnf");
        if (hasPar("msoundDropEveryK"))
            msoundDropEveryK = par("msoundDropEveryK");
        if (hasPar("testInjectPostSlacMsgs"))
            testInjectPostSlacMsgs = par("testInjectPostSlacMsgs");
        if (hasPar("testAllowPreSlacSweep"))
            testAllowPreSlacSweep = par("testAllowPreSlacSweep");
        if (hasPar("testSyncStart"))
            testSyncStart = par("testSyncStart");
        if (hasPar("testDisableDc"))
            testDisableDc = par("testDisableDc");
        if (hasPar("testForceCap0Only"))
            testForceCap0Only = par("testForceCap0Only");
        if (hasPar("testCycleCap123"))
            testCycleCap123 = par("testCycleCap123");
        if (hasPar("testPostSlacPeriod"))
            testPostSlacPeriod = par("testPostSlacPeriod");
        if (enablePriorityCycle || enableDcPriorityCycle) {
            EV_WARN << "This is Priority Cycle Mode!!! it is not a charging protocol environment!!" << endl;
            EV_INFO << "This is Priority Cycle Mode!!! it is not a charging protocol environment!!" << endl;
        }
        dcRspDelay = par("dcRspDelay");
        startMsg = new cMessage("start");
        take(startMsg);
        // add small positive offset; optionally align with test sync flag
        simtime_t launchOffset = startJitter + 0.0001;
        if (testSyncStart)
            launchOffset = 0.0001; // ignore per-node jitter for synchronized tests
        scheduleAt(simTime() + launchOffset, startMsg);
        if (testInjectPostSlacMsgs) {
            postSlacSweep = new cMessage("postSlacSweep");
            take(postSlacSweep);
            // If explicitly allowed, start CAP sweep even before SLAC completion
            if (testAllowPreSlacSweep)
                scheduleAt(simTime() + 0.001, postSlacSweep);
        }
        // Schedule periodic heartbeat scalar for recording pipeline verification (observer-only)
        heartbeat = new cMessage("heartbeat");
        take(heartbeat);
        scheduleAt(simTime() + 0.5, heartbeat);
        dcReqSignal = registerSignal("dcReqSent");
        dcRspSignal = registerSignal("dcRspRecv");
        dcLatencySignal = registerSignal("dcLatency");
        dcLatMin = 0.0;
        dcLatMax = 0.0;
        dcLatSum = 0.0;
        dcLatCount = 0;
        slacCompleted = false;

        // Debug: verify gate connectivity at startup
        cGate *outg = hasGate("out") ? gate("out") : nullptr;
        if (!outg) {
            EV_ERROR << "[UL_DBG] SlacApp has no 'out' gate" << endl;
        } else {
            if (!outg->isConnected()) {
                EV_ERROR << "[UL_DBG] SlacApp.out NOT connected" << endl;
            } else {
                cGate *endg = outg->getPathEndGate();
                EV_INFO << "[UL_DBG] SlacApp.out -> "
                        << (endg ? endg->getOwnerModule()->getFullPath() : std::string("(null)"))
                        << "." << (endg ? endg->getName() : "") << endl;
            }
        }
    }
    virtual void handleMessage(cMessage* msg) override {
        if (msg->isSelfMessage()) {
            if (msg == startMsg) {
                if (role == "EV") {
                    // Use PLCFrame directly so MAC can process it
                    auto sendPlc = [&](int /*prio*/){
                        auto *f = new PLCFrame("PLC");
                        f->setFrameType(2); // control-like
                        // SLAC-related messages: force CA3
                        f->setPriority(3);
                        f->setSrcAddr(nodeId);
                        f->setDestAddr(0);
                        f->setPayloadLength(300);
                        f->setByteLength(300);
                        f->setAckRequired(false);
                        EV_INFO << "[UL_TX] SlacApp.send gate=out msgClass=" << f->getClassName()
                                << " name=" << f->getName() << " t=" << simTime() << endl;
                        send(f, "out");
                    };
                    // SLAC sequence as burst with configured priority
                    EV_INFO << "SLAC_LOG stage=START_ATTEN node=" << getParentModule()->getFullName() << " cap=3 t=" << simTime() << endl;
                    sendPlc(3); // SLAC_PARM_REQ (START_ATTEN)
                    for (int i=0;i<numStartAtten;i++) {
                        EV_INFO << "SLAC_LOG stage=START_ATTEN node=" << getParentModule()->getFullName() << " cap=3 t=" << simTime() << endl;
                        sendPlc(3);
                    }
                    for (int i=0;i<numMsound;i++) {
                        int idx = i+1;
                        bool drop = (msoundDropEveryK>0 && (idx % msoundDropEveryK)==0);
                        EV_INFO << "SLAC_LOG stage=M_SOUND node=" << getParentModule()->getFullName() << " idx=" << idx << " cap=3 t=" << simTime() << (drop?" DROPPED":"") << endl;
                        if (!drop) sendPlc(3);
                    }
                    EV_INFO << "SLAC_LOG stage=ATTEN_CHAR node=" << getParentModule()->getFullName() << " cap=3 t=" << simTime() << endl;
                    sendPlc(3); // ATTEN_CHAR_RSP
                    EV_INFO << "SLAC_LOG stage=VALIDATE node=" << getParentModule()->getFullName() << " cap=3 t=" << simTime() << endl;
                    sendPlc(3); // SLAC_MATCH_REQ (VALIDATE)
                }
                // NOTE: dcTick will be scheduled after SLAC completion (SLAC_MATCH_CNF)
                // consume startMsg
                startMsg = nullptr;
                delete msg;
                return;
            } else if (!strcmp(msg->getName(), "heartbeat")) {
                // Observer-only heartbeat scalar for result pipeline verification
                recordScalar("heartbeat", 1);
                scheduleAt(simTime() + 0.5, heartbeat);
                return;
            } else if (!strcmp(msg->getName(), "dcTick")) {
                if (role == "EV") {
                    if (!slacCompleted) { // gate DC until SLAC is complete
                        scheduleAt(simTime() + 0.01, dcTick);
                        return;
                    }
                    if (testDisableDc) {
                        return; // stop DC generation entirely
                    }
                    // generate sequence id and encode in name for robust matching
                    dcReqSeq += 1;
                    char reqName[64];
                    sprintf(reqName, "DC_REQUEST:%d", dcReqSeq);
                    auto *req = new PLCFrame(reqName);
                    req->setFrameType(2);
                    // DC commands: force CA0 unless overridden
                    int dcPrio = testForceCap0Only ? 0 : dcPriority;
                    req->setPriority(dcPrio);
                    req->setSrcAddr(nodeId);
                    // Diagnostic: optionally force unicast to EVSE to verify reception path
                    int dest = 0;
                    if (hasPar("testUnicastEvse") && (bool)par("testUnicastEvse")) {
                        dest = hasPar("testTargetNodeId") ? (int)par("testTargetNodeId") : 1;
                    }
                    req->setDestAddr(dest);
                    req->setPayloadLength(300);
                    req->setByteLength(300);
                    req->setAckRequired(false);
                    req->setTimestamp();
                    // Measure EV-side request pacing intervals
                    if (hasLastDcReq) {
                        simtime_t delta = simTime() - lastDcReqSentTime;
                        dcReqIntervalCount++;
                        if (delta > 0.1) dcReqIntervalDelayedCount++;
                    }
                    lastDcReqSentTime = simTime();
                    hasLastDcReq = true;
                    EV_INFO << "CAP_LOG node=" << getParentModule()->getFullName() << " cap=" << req->getPriority() << " t=" << simTime() << endl;
                    EV_INFO << "OBS EV_TX_DC_REQUEST node=" << getParentModule()->getFullName() << " dest=" << req->getDestAddr() << " t=" << simTime() << endl;
                    // store per-seq send time
                    dcReqSendTimesBySeq[dcReqSeq] = simTime();
                    EV_INFO << "[UL_TX] SlacApp.send gate=out msgClass=" << req->getClassName()
                            << " name=" << req->getName() << " t=" << simTime() << endl;
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
                // EVSE delayed response enqueue: construct response now to avoid contextPointer ownership issues
                int dest = (intptr_t)msg->getContextPointer();
                // echo seq id back if available
                int reqSeq = msg->getKind();
                char rspName[64];
                if (reqSeq > 0) sprintf(rspName, "DC_RESPONSE:%d", reqSeq); else sprintf(rspName, "DC_RESPONSE");
                auto *rsp = new PLCFrame(rspName);
                rsp->setFrameType(2);
                rsp->setPriority(0);
                rsp->setSrcAddr(nodeId);
                rsp->setDestAddr(dest);
                rsp->setPayloadLength(300);
                rsp->setByteLength(300);
                rsp->setAckRequired(false);
                EV_INFO << "OBS EVSE_TX_DC_RESPONSE node=" << getParentModule()->getFullName()
                        << " dest=" << rsp->getDestAddr() << " t=" << simTime() << endl;
                EV_INFO << "CAP_LOG node=" << getParentModule()->getFullName() << " cap=" << rsp->getPriority() << " t=" << simTime() << endl;
                EV_INFO << "[UL_TX] SlacApp.send gate=out msgClass=" << rsp->getClassName()
                        << " name=" << rsp->getName() << " t=" << simTime() << endl;
                send(rsp, "out");
                dcRspSent++;
                delete msg;
                return;
            } else if (!strcmp(msg->getName(), "postSlacSweep")) {
                if (!slacCompleted && !testAllowPreSlacSweep) {
                    scheduleAt(simTime() + 0.001, msg);
                    return;
                }
                emitCapSweep();
                if (testPostSlacPeriod <= SIMTIME_ZERO)
                    scheduleAt(simTime() + dcPeriod, msg);
                else
                    scheduleAt(simTime() + testPostSlacPeriod, msg);
                return;
            } else if (!strcmp(msg->getName(), "slacDone")) {
                // One-shot marker; do nothing and keep message for possible future checks
                return;
            }
            delete msg;
        } else {
            // incoming from MAC
            PLCFrame *f = dynamic_cast<PLCFrame*>(msg);
            if (!f) { delete msg; return; }
            if (role == "EVSE" && strncmp(f->getName(), "DC_REQUEST", 10) == 0) {
                EV_INFO << "OBS EVSE_RCV_DC_REQUEST node=" << getParentModule()->getFullName()
                        << " src=" << f->getSrcAddr() << " t=" << simTime() << endl;
                // schedule delayed response with echoed seq via kind
                cMessage *enq = new cMessage("dcRspEnq");
                take(enq);
                // extract seq from request name if present (format: DC_REQUEST:<seq>)
                int reqSeq = 0;
                {
                    std::string nm = f->getName();
                    auto p = nm.find(':');
                    if (p != std::string::npos) {
                        try { reqSeq = std::stoi(nm.substr(p+1)); } catch (...) { reqSeq = 0; }
                    }
                }
                enq->setContextPointer((void*)(intptr_t)f->getSrcAddr());
                enq->setKind(reqSeq);
                scheduleAt(simTime() + dcRspDelay, enq);
                delete f;
                return;
            }
            // EVSE: respond to SLAC end with match CNF unless simulateNoEvse
            if (role == "EVSE") {
                if (!simulateNoEvse) {
                    int evId = f->getSrcAddr();
                    if (cnfSentTo.find(evId) == cnfSentTo.end()) {
                        cnfSentTo.insert(evId);
                        auto *cnf = new PLCFrame("SLAC_MATCH_CNF");
                        cnf->setFrameType(2);
                        cnf->setPriority(3);
                        cnf->setSrcAddr(nodeId);
                        cnf->setDestAddr(evId);
                        cnf->setPayloadLength(100);
                        cnf->setByteLength(100);
                        cnf->setAckRequired(false);
                        send(cnf, "out");
                    }
                }
                delete f;
                return;
            }
            if (role == "EV" && strncmp(f->getName(), "DC_RESPONSE", 11) == 0) {
                // Count only responses addressed to this EV (ignore broadcast copies to others)
                if (f->getDestAddr() == nodeId) {
                    // parse seq id
                    int rspSeq = 0; {
                        std::string nm = f->getName();
                        auto p = nm.find(':');
                        if (p != std::string::npos) { try { rspSeq = std::stoi(nm.substr(p+1)); } catch (...) { rspSeq = 0; } }
                    }
                    // match send time by seq; fallback to last send
                    simtime_t sendT = hasLastDcReq ? lastDcReqSentTime : SIMTIME_ZERO;
                    if (rspSeq > 0) {
                        auto it = dcReqSendTimesBySeq.find(rspSeq);
                        if (it != dcReqSendTimesBySeq.end()) {
                            sendT = it->second;
                            dcReqSendTimesBySeq.erase(it);
                        }
                    }
                    dcRspRecv++;
                    emit(dcRspSignal, dcRspRecv);
                    simtime_t lat = (sendT == SIMTIME_ZERO) ? SIMTIME_ZERO : (simTime() - sendT);
                    emit(dcLatencySignal, lat.dbl());
                    // latency aggregates
                    double l = lat.dbl();
                    dcLatSamples.push_back(l);
                    if (dcLatCount == 0) {
                        dcLatMin = l; dcLatMax = l;
                    } else {
                        if (l < dcLatMin) dcLatMin = l;
                        if (l > dcLatMax) dcLatMax = l;
                    }
                    dcLatSum += l;
                    dcLatCount++;
                    if (lat > 0.1) dcDeadlineMissCount++;
                    // matched response
                    dcRspMatch++;
                }
                delete f;
                return;
            }
            // EV: SLAC complete ONLY when CNF addressed to this EV
            if (role == "EV" && strcmp(f->getName(), "SLAC_MATCH_CNF") == 0) {
                if (slacCompleted) { delete f; return; }
                // If test jam switch is on, drop this CNF to emulate timed noise
                if (testJamOnMatchCnf) {
                    EV_WARN << "SLAC_LOG drop=SLAC_MATCH_CNF node=" << getParentModule()->getFullName() << " t=" << simTime() << endl;
                    delete f;
                    return;
                }
                // sanity log to confirm upper delivery path
                EV_INFO << "OBS EV_RCV_MATCH_CNF node=" << getParentModule()->getFullName() << " src=" << f->getSrcAddr() << " t=" << simTime() << endl;
                if (f->getDestAddr() == nodeId) {
                    if (!slacDone) { slacDone = new cMessage("slacDone"); take(slacDone); }
                    if (slacDone->isScheduled()) cancelEvent(slacDone);
                    scheduleAt(simTime(), slacDone);
                    slacCompleted = true; // mark completion
                    recordScalar("slacDoneTime(s)", simTime().dbl());
                    // start DC ticking only after SLAC completed
                    if (!dcTick) { dcTick = new cMessage("dcTick"); take(dcTick); }
                    if (!dcTick->isScheduled()) scheduleAt(simTime(), dcTick);
                    if (testInjectPostSlacMsgs && postSlacSweep && !postSlacSweep->isScheduled())
                        emitCapSweep(), startPeriodicCapSweep();
                    EV_INFO << "SLAC_LOG stage=SLAC_DONE node=" << getParentModule()->getFullName() << " t=" << simTime() << endl;
                    delete f;
                    return;
                } else {
                    delete f;
                    return;
                }
            }
            delete f;
        }
    }
    virtual void finish() override {
        EV_INFO << "SlacApp::finish() called at t=" << simTime() << " node=" << getParentModule()->getFullName() << endl;
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
        if (postSlacSweep) {
            if (postSlacSweep->isScheduled()) cancelEvent(postSlacSweep);
            delete postSlacSweep;
            postSlacSweep=nullptr;
        }
        recordScalar("finished", 1);
        recordScalar("dcReqSent", dcReqSent);
        recordScalar("dcRspSent", dcRspSent);
        recordScalar("dcRspRecv", dcRspRecv);
        // Derived counters for summary
        recordScalar("DcReqCnt", dcReqSent);
        recordScalar("DcResCnt", dcRspRecv);
        recordScalar("DcDeadlineMissCount", dcDeadlineMissCount);
        double reqDelayRate = (dcReqIntervalCount > 0) ? ((double)dcReqIntervalDelayedCount / dcReqIntervalCount) : 0.0;
        recordScalar("dcReqDelayRate", reqDelayRate);
        double matchRate = (dcReqSent > 0) ? ((double)dcRspRecv / dcReqSent * 100.0) : 0.0;
        recordScalar("dcMatchRate(%)", matchRate);
        if (dcLatCount > 0) {
            double avg = dcLatSum / dcLatCount;
            recordScalar("DcAirtimeAvg(s)", avg);
            recordScalar("dcLatencyMin(s)", dcLatMin);
            recordScalar("dcLatencyMax(s)", dcLatMax);
            // Compute P95 non-parametrically (no protocol behavior change)
            std::vector<double> tmp = dcLatSamples;
            std::sort(tmp.begin(), tmp.end());
            size_t idx = (size_t)std::floor(0.95 * (tmp.size() - 1));
            double p95 = tmp.empty() ? 0.0 : tmp[idx];
            recordScalar("DcAirtimeP95(s)", p95);
            double missRate = (dcReqSent > 0) ? ((double)dcDeadlineMissCount / dcReqSent) : 0.0;
            recordScalar("DcDeadlineMissRate", missRate);
        } else {
            recordScalar("DcAirtimeAvg(s)", 0.0);
            recordScalar("dcLatencyMin(s)", 0.0);
            recordScalar("dcLatencyMax(s)", 0.0);
            recordScalar("DcAirtimeP95(s)", 0.0);
            recordScalar("DcDeadlineMissRate", 0.0);
        }
    }

    void scheduleNextDcTick(simtime_t delay) {
        if (!dcTick) { dcTick = new cMessage("dcTick"); take(dcTick); }
        if (!dcTick->isScheduled()) scheduleAt(simTime() + delay, dcTick);
    }

    void emitCapSweep() {
        static const int caps[] = {1, 2, 3};
        static const char* names[] = {"TST_MSG_CAP1", "TST_MSG_CAP2", "TST_MSG_CAP3"};
        if (testCycleCap123) {
            int idx = capCycleIndex % 3;
            auto *probe = new PLCFrame(names[idx]);
            probe->setFrameType(2);
            probe->setPriority(caps[idx]);
            probe->setSrcAddr(nodeId);
            probe->setDestAddr(0);
            probe->setPayloadLength(64);
            probe->setByteLength(64);
            probe->setAckRequired(false);
            EV_INFO << "OBS POST_SLAC_PROBE node=" << getParentModule()->getFullName()
                    << " cap=CA" << probe->getPriority() << " t=" << simTime() << endl;
            EV_INFO << "[UL_TX] SlacApp.send gate=out msgClass=" << probe->getClassName()
                    << " name=" << probe->getName() << " t=" << simTime() << endl;
            send(probe, "out");
            capCycleIndex++;
        } else {
            for (int i = 0; i < 3; ++i) {
                auto *probe = new PLCFrame(names[i]);
                probe->setFrameType(2);
                probe->setPriority(caps[i]);
                probe->setSrcAddr(nodeId);
                probe->setDestAddr(0);
                probe->setPayloadLength(64);
                probe->setByteLength(64);
                probe->setAckRequired(false);
                EV_INFO << "OBS POST_SLAC_PROBE node=" << getParentModule()->getFullName()
                        << " cap=CA" << probe->getPriority() << " t=" << simTime() << endl;
                EV_INFO << "[UL_TX] SlacApp.send gate=out msgClass=" << probe->getClassName()
                        << " name=" << probe->getName() << " t=" << simTime() << endl;
                send(probe, "out");
            }
        }
    }

    void startPeriodicCapSweep() {
        if (!postSlacSweep) return;
        simtime_t period = (testPostSlacPeriod <= SIMTIME_ZERO) ? dcPeriod : testPostSlacPeriod;
        if (period <= SIMTIME_ZERO) return;
        if (!postSlacSweep->isScheduled())
            scheduleAt(simTime() + period, postSlacSweep);
    }
};

Define_Module(SlacApp);
