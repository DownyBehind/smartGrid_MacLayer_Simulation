// package csma_ca_hpgp;

import inet.applications.contract.IApp;

simple SlacApp like IApp
{
    parameters:
        @display("i=block/app");
        int localPort = default(5000);
        int destPort = default(5001);
        int burst = default(1);
        double startJitter @unit(s) = default(0s);
        @signal[slacCompletionTime](type=simtime_t);
        @statistic[slacCompletionTime](title="SLAC completion time"; source=slacCompletionTime; record=vector,mean);
    gates:
        input socketIn @labels(UdpControlInfo/down);
        output socketOut @labels(UdpControlInfo/up);
}