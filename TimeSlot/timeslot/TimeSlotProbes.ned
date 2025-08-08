// project_smartCharging_macLayer_improvement/TimeSlot/TimeSlotProbes.ned
package timeslot;

import inet.node.inet.WirelessHost;
import timeslot.TxOutcomeProbe;      // C++ 모듈


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
        double slotTime   @unit(s) = default(9e-6s); 

        bool   debugSignals = default(false);   // ★ 추가
        int    debugMaxLines = default(12);     // ★ 추가

        @display("i=block/cogwheel");
}

simple SendIntervalConfigurator
{
    parameters:
        double baseInterval @unit(s) = default(0.0015s);   // 1.5 ms
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

//
// WirelessHost + TxOutcomeProbe  =  실험용 호스트
//
module WirelessHostWithProbe extends WirelessHost
{
    submodules:
        // ① Idle/Busy 추적용 Probe ――――――――――――――――――――――――――
        busyIdleProbe: MediumBusyIdleProbe {
            parameters:
                targetNodePath = default("^");   // 자신을 가리킴
                wlanIndex      = default(0);
                slotTime       = default(9e-6s); // 802.11g SlotTime
                @display("p=70,30;i=block/timer");
        }

        // ② Tx Outcome Probe (기존 그대로) ―――――――――――――――――――――――

        txProbe: TxOutcomeProbe {
            parameters:
                // -- Probe 가 스스로 부모 노드를 바라보도록 —
                targetNodePath = default("^");   // “^” = 나 자신
                wlanIndex      = default(0);

                // ---- 타이밍 파라미터 (필요시 실험값으로 덮어쓰기) ----
                sifs           = default(16e-6s);
                cifs           = default(34e-6s);
                ackTxTime      = default(44e-6s);
                ackTimeout     = default(60e-6s);
                slotTime       = default(parent.slotTime);      // (Observer 모듈일 때)

                // ---- 디버그 (기본 끔; INI 에서 켜면 됨) ----
                debugSignals   = default(false);
                debugMaxLines  = default(12);

                @display("p=70,50;i=block/cogwheel");
        }
}

simple SmartUdpApp extends inet.applications.udpapp.UdpBasicApp
{
    parameters:
        sendInterval @mutable(true);     // ★ 런타임에 변경 허용
        @display("i=block/app");
}