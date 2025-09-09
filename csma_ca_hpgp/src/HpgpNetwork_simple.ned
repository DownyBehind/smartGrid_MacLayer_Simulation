//
// HPGP Network with SLAC simulation
// Simple version for testing
//

// package csma_ca_hpgp.src;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.physicallayer.wireless.ieee80211.medium.Ieee80211ScalarRadioMedium;

network HpgpNetwork
{
    parameters:
        int numNodes = default(3);
        
    submodules:
        configurator: Ipv4NetworkConfigurator;
        radioMedium: Ieee80211ScalarRadioMedium;
        
        node[numNodes]: HpgpNode;
}
