package ned;

import inet.linklayer.plc.IEEE1901Interface;
// import inet.node.inet.StandardHost; // not used for simplified nodes
import inet.physicallayer.wired.common.WireJunction;

channel PLCMedium extends ned.DatarateChannel
{
    datarate = 100Mbps;
    delay = 0.1us;
}

module EvNode
{
    parameters:
        @display("i=device/pc2");
    gates:
        inout plcg;
    submodules:
        plc: IEEE1901Interface { @display("p=150,200"); }
        slac: SlacApp { parameters: role = "EV"; @display("p=300,200"); }
    connections allowunconnected:
        plcg <--> plc.plc;
        plc.upperLayerOut --> slac.in;
        slac.out --> plc.upperLayerIn;
}

module EvseNode
{
    parameters:
        @display("i=device/pc2");
    gates:
        inout plcg;
    submodules:
        plc: IEEE1901Interface { @display("p=150,200"); }
        slac: SlacApp { parameters: role = "EVSE"; @display("p=300,200"); }
    connections allowunconnected:
        plcg <--> plc.plc;
        plc.upperLayerOut --> slac.in;
        slac.out --> plc.upperLayerIn;
}

network EvEvseNetwork
{
    parameters:
        int numEvs = default(4);
    submodules:
        evse: EvseNode { @display("p=100,200"); }
        ev[numEvs]: EvNode { @display("p=300+100*index,200"); }
        bus: WireJunction { @display("p=250,350"); }
    connections allowunconnected:
        evse.plcg <--> PLCMedium <--> bus.port++;
        ev[0].plcg <--> PLCMedium <--> bus.port++;
        ev[1].plcg <--> PLCMedium <--> bus.port++;
        ev[2].plcg <--> PLCMedium <--> bus.port++;
        ev[3].plcg <--> PLCMedium <--> bus.port++;
}
