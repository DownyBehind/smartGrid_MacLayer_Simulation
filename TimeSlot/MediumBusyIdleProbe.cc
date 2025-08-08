// project_smartCharging_macLayer_improvement/TimeSlot/MediumBusyIdleProbe.cc
#include "MediumBusyIdleProbe.h"
#include "inet/common/ModuleAccess.h"

Define_Module(MediumBusyIdleProbe);

/*** INITIALIZE *************************************************************/
void MediumBusyIdleProbe::initialize()
{
    /* 1) 파라미터 */
    std::string path = par("targetNodePath").stdstringValue();
    wlanIndex  = par("wlanIndex");
    slotTime   = par("slotTime");

    /* 2) 상대경로("^","."), 빈 문자열 처리 */
    cModule *tgt = nullptr;
    if (path.empty() || path == "^" || path == ".")
        tgt = getParentModule();
    else
        tgt = getSimulation()->getModuleByPath(path.c_str());

    if (!tgt)
        throw cRuntimeError("Cannot resolve targetNodePath='%s'", path.c_str());

    targetNodePath = path;
    lastChange = simTime();

    attach();          // Radio 포인터 + 시그널 구독
}

/*** attach(): 노드->radio 연결 *********************************************/
void MediumBusyIdleProbe::attach()
{
    std::string p = targetNodePath;
    if (p.empty() || p == "^" || p == ".")
        p = getParentModule()->getFullPath();
    else if (p[0] == '.')
        p = getSimulation()->getSystemModule()->getFullPath() + p;

    cModule *node = getSimulation()->findModuleByPath(p.c_str());
    if (!node)  throw cRuntimeError("target '%s' not found", p.c_str());

    cModule *wlan = node->getSubmodule("wlan", wlanIndex);
    if (!wlan)   throw cRuntimeError("wlan[%d] not found in %s",
                                     wlanIndex, node->getFullPath().c_str());

    radio = wlan->getSubmodule("radio");
    if (!radio)  throw cRuntimeError("radio not found");

    rxStateSig =
        inet::physicallayer::IRadio::receptionStateChangedSignal;
    radio->subscribe(rxStateSig, this);

    lastRxState =
        check_and_cast<inet::physicallayer::IRadio*>(radio)->getReceptionState();
}

/*** 시그널 처리 ************************************************************/
void MediumBusyIdleProbe::receiveSignal(cComponent *, simsignal_t id,
                                        long value, cObject*)
{
    if (id != rxStateSig) return;
    Enter_Method_Silent();

    simtime_t now = simTime();
    bool wasIdle =
        (lastRxState == inet::physicallayer::IRadio::RECEPTION_STATE_IDLE);
    if (wasIdle) idleAcc += (now - lastChange);
    else         busyAcc += (now - lastChange);

    lastRxState = static_cast<inet::physicallayer::IRadio::ReceptionState>(value);
    lastChange  = now;
}

/*** finish(): 스칼라 저장 ***************************************************/
void MediumBusyIdleProbe::finish()
{
    /* 마지막 interval 누적 */
    simtime_t now = simTime();
    bool isIdle =
        (lastRxState == inet::physicallayer::IRadio::RECEPTION_STATE_IDLE);
    if (isIdle) idleAcc += (now - lastChange);
    else        busyAcc += (now - lastChange);

    recordScalar("ti_idle_time",  idleAcc.dbl());
    recordScalar("tb_busy_time",  busyAcc.dbl());

    if (slotTime > 0) {
        recordScalar("ni_idle_slots", idleAcc.dbl() / slotTime);
        recordScalar("nb_busy_slots", busyAcc.dbl() / slotTime);
    }
}
