// project_smartCharging_macLayer_improvement/TimeSlot/TimeSlotProbes.ned
package timeslot;

simple MediumBusyIdleProbe
{
    parameters:
        string targetNodePath;          // 예: ".host[0]"
        int wlanIndex = default(0);
        double slotTime @unit(s);
        @display("i=block/timer");
}

simple TxOutcomeProbe
{
    parameters:
        string targetNodePath;          // 예: ".host[0]"
        int wlanIndex = default(0);
        double sifs @unit(s);
        double cifs @unit(s);
        double ackTxTime @unit(s);
        double ackTimeout @unit(s);
        @display("i=block/cogwheel");
}

module TimeSlotObserver
{
    parameters:
        string targetNodePath;          // 네트워크 내 대상 노드: ".host[0]" 권장
        int wlanIndex = default(0);
        double slotTime   @unit(s) = default(9e-6s);
        double sifs       @unit(s) = default(16e-6s);
        double cifs       @unit(s) = default(34e-6s);
        double ackTxTime  @unit(s) = default(44e-6s);
        double ackTimeout @unit(s) = default(60e-6s);
    submodules:
        mediumProbe: MediumBusyIdleProbe {
            parameters:
                targetNodePath = default(parent.targetNodePath);
                wlanIndex      = default(parent.wlanIndex);
                slotTime       = default(parent.slotTime);
        }
        txProbe: TxOutcomeProbe {
            parameters:
                targetNodePath = default(parent.targetNodePath);
                wlanIndex      = default(parent.wlanIndex);
                sifs           = default(parent.sifs);
                cifs           = default(parent.cifs);
                ackTxTime      = default(parent.ackTxTime);
                ackTimeout     = default(parent.ackTimeout);
        }
}
