//
// Copyright …
package csma_ca_test_for_Ayar_Paper;

import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import timeslot.WirelessHostWithProbe;          // ★ 새로 추가
import timeslot.SendIntervalConfigurator; 

network FakeWireCsmaCaNetwork
{
    parameters:
        // 노드(호스트)의 개수를 정의하는 정수형 파라미터입니다. 기본값은 10개입니다.
        int numHosts = default(100);

    // 네트워크를 구성하는 하위 모듈들을 정의하는 섹션입니다.
    submodules:
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,200;i=block/cog");
        }
        radioMedium: Ieee80211ScalarRadioMedium {
            @display("p=100,100;i=block/wifirouter");
            backgroundNoise.power = -100dBm;
            pathLoss.typename = "FreeSpacePathLoss";
        }
//        tsObs: TimeSlotObserver {      // 필요 없으면 나중에 제거 가능
//            parameters:
//                targetNodePath = ".host[0]";
//                wlanIndex      = 0;
//                slotTime       = 9e-6s;
//                sifs           = 16e-6s;
//                cifs           = 34e-6s;
//                ackTxTime      = 44e-6s;
//                ackTimeout     = 60e-6s;
//            @display("p=100,100");
//        }
        // ───────── 모든 호스트에 Probe 포함 ─────────
        host[numHosts]: WirelessHostWithProbe {
            @display("p=400,150");
            mobility.typename = "StationaryMobility";

            mobility.initialX = (index == 0) ? 0m
                           : cos((index - 1) * 2 * 3.141592 / (parent.numHosts - 1)) * 80m;
            mobility.initialY = (index == 0) ? 0m
                           : sin((index - 1) * 2 * 3.141592 / (parent.numHosts - 1)) * 80m;
        }
        // ② 새 Configurator (트래픽 간격 계산)
        cfg: SendIntervalConfigurator {
            parameters:
                baseInterval = default(0.000150000s);   // 1 ms
                @display("p=100,100;i=block/cogwheel");
        }
}
