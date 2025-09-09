// package src;

import inet.node.inet.WirelessHost;

// Wrapper host that forwards the first WLAN interface's PLC gate to the outside
module PlcHost extends WirelessHost
{
    gates:
        inout plc; // Exposed PLC gate to connect to wired PLC medium
    connections allowunconnected:
        // Forward the internal NIC's plc gate to the outside
        wlan[0].plc <--> plc;
}
