//
// SLAC Application Module
// Implements the SLAC protocol for PLC communication
//

simple SlacApplication
{
    parameters:
        string nodeType = default("EV");
        int nodeId = default(0);
        
        // SLAC timing parameters
        double slacMsgTimeout @unit(s) = default(2s);
        double slacProcTimeout @unit(s) = default(60s);
        int slacMaxRetry = default(3);
        double slacRetryBackoff @unit(s) = default(0.15s);
        
        // DC loop parameters
        bool dcLoopEnabled = default(false);
        double dcPeriod @unit(s) = default(100ms);
        double dcDeadline @unit(s) = default(100ms);
        double dcRspDelay @unit(s) = default(1.5ms);
        double dcRspJitter @unit(s) = default(0ms);
        
        // SLAC detailed parameters
        int nStartAtten = default(3);
        int nMsound = default(10);
        double gapStart @unit(ms) = default(2ms);
        double gapMsound @unit(ms) = default(2ms);
        double delayEvseRsp @unit(ms) = default(1ms);
        double gapAttn @unit(ms) = default(2ms);
        double gapMatch @unit(ms) = default(2ms);
        
    gates:
        input in;
        output out;
}
