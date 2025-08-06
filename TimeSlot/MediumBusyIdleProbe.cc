// project_smartCharging_macLayer_improvement/TimeSlot/MediumBusyIdleProbe.cc
#include "MediumBusyIdleProbe.h"
#include "inet/common/ModuleAccess.h"

Define_Module(MediumBusyIdleProbe);

void MediumBusyIdleProbe::initialize() {
    targetNodePath = par("targetNodePath").stdstringValue();
    wlanIndex = par("wlanIndex");
    slotTime  = par("slotTime").doubleValue();
    attach();
    lastChange = simTime();
}

void MediumBusyIdleProbe::attach() {
    // targetNodePath가 ".host[0]" 같은 상대경로면 루트에 붙여 절대경로로 만듦
    std::string p = targetNodePath;
    if (!p.empty() && p[0] == '.') {
        p = getSimulation()->getSystemModule()->getFullPath() + p; // "Root.host[0]"
    }
    cModule *node = getSimulation()->findModuleByPath(p.c_str());
    if (!node)
        throw cRuntimeError("targetNodePath not found: '%s' (resolved: '%s')",
                            targetNodePath.c_str(), p.c_str());

    cModule *wlan = node->getSubmodule("wlan", wlanIndex);
    if (!wlan) throw cRuntimeError("wlan[%d] not found", wlanIndex);
    radio = wlan->getSubmodule("radio");
    if (!radio) throw cRuntimeError("radio not found");

    // Subscribe radio reception state
    rxStateSig = inet::physicallayer::IRadio::receptionStateChangedSignal;
    radio->subscribe(rxStateSig, this);

    // init current state
    auto r = check_and_cast<inet::physicallayer::IRadio*>(radio);
    lastRxState = r->getReceptionState();
}

void MediumBusyIdleProbe::receiveSignal(cComponent *, simsignal_t id, long l, cObject *) {
    // ★ scheduleAt/cancelEvent/recordScalar 등 안전하게 호출하려면 컨텍스트 진입
    Enter_Method_Silent();

    if (id != rxStateSig) return;
    auto newState = static_cast<inet::physicallayer::IRadio::ReceptionState>(l);
    simtime_t now = simTime();
    bool wasIdle = (lastRxState == inet::physicallayer::IRadio::RECEPTION_STATE_IDLE);
    if (wasIdle) idleAcc += (now - lastChange);
    else         busyAcc += (now - lastChange);
    lastRxState = newState;
    lastChange = now;
}


void MediumBusyIdleProbe::finish() {
    // close last interval
    simtime_t now = simTime();
    bool isIdle = (lastRxState == inet::physicallayer::IRadio::RECEPTION_STATE_IDLE);
    if (isIdle) idleAcc += (now - lastChange);
    else        busyAcc += (now - lastChange);

    recordScalar("ti_idle_time", idleAcc.dbl());   // seconds
    recordScalar("busy_time",    busyAcc.dbl());
    if (slotTime > 0)
        recordScalar("idle_slots", (idleAcc.dbl() / slotTime));
}
