package test.common;

// import modules from package 'ned'
import ned.EvNode;
import ned.EvseNode;
import inet.physicallayer.wired.common.WireJunction;

channel PLCMedium extends ned.DatarateChannel
{
    datarate = 100Mbps;
    delay = 0.1us;
}

network TestBus
{
    parameters:
        int numEvs = default(1);
    submodules:
        bus: WireJunction {}
        evse: EvseNode { }
        ev[numEvs]: EvNode { }
    connections allowunconnected:
        for i=0..numEvs-1 {
            ev[i].plcg <--> PLCMedium <--> bus.port++;
        }
        evse.plcg <--> PLCMedium <--> bus.port++;
}
