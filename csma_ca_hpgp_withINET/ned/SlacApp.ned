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
        bool simulateNoEvse = default(false); // Observer-only: suppress EV SLAC_DONE for timeout tests
        bool testJamOnMatchCnf = default(false); // Test-only: drop SLAC_MATCH_CNF at EV reception
        int msoundDropEveryK = default(0); // Test-only: drop every K-th M_SOUND if >0
        bool testUnicastEvse = default(false); // Test-only: force unicast DC_REQUEST to EVSE
        int testTargetNodeId = default(1);
        bool testDcUseCap3 = default(false); // Test-only: send DC at CAP3 for diagnostics
        @display("i=block/app");
    gates:
        input in;
        output out;
}
