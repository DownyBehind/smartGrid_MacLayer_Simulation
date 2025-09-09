// package src;

import inet.physicallayer.wired.common.WireJunction;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;

network PlcStarSlac
{
    parameters:
        int numNodes = default(10);
    submodules:
        configurator: Ipv4NetworkConfigurator;
        hub: WireJunction;
        evse: PlcHost {
            parameters:
                numWlanInterfaces = 1;
                wlan[0].typename = "IEEE1901Interface";
        }
        node[numNodes-1]: PlcHost {
            parameters:
                numWlanInterfaces = 1;
                wlan[0].typename = "IEEE1901Interface";
        }
    connections allowunconnected:
        // Connect all PLC interfaces to a common wired junction (PLC bus / hub)
        evse.plc <--> hub.port++;
        for i=0..numNodes-2 {
            node[i].plc <--> hub.port++;
        }
}
