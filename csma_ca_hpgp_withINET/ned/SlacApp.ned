package ned;

simple SlacApp
{
    parameters:
        @class(::SlacApp);
        string role = default("EV");
        int nodeId = default(0);
        int numStartAtten = default(3);
        int numMsound = default(10);
        int startPriority = default(3);
        double startJitter @unit(s) = default(0s);
        double dcPeriod @unit(s) = default(100ms);
        int dcPriority = default(0);
        bool enableDcPriorityCycle = default(false);
        bool enablePriorityCycle = default(false);
        double dcRspDelay @unit(s) = default(2ms);
        @display("i=block/app");
    gates:
        input in;
        output out;
}
