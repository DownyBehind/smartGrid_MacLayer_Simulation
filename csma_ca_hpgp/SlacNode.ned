package csma_ca_hpgp;

//
// SLAC Node for HPGP simulation
// Simplified node without INET dependencies
//

module SlacNode
{
    parameters:
        string nodeType = default("EV");  // "EVSE" or "EV"
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
        
    submodules:
        hpgpMac: HpgpMac {
            cifs = 35.84us;
            rifs = 26us;
            prs0 = 35.84us;
            prs1 = 35.84us;
            slotTime = 35.84us;
            bpcMax = 4;
            priorityGroup = "CA23";
            recordTxAttempts = true;
            recordCollisions = true;
            recordSlacMessages = true;
            recordDcCycles = true;
            nodeType = parent.nodeType;
            nodeId = parent.nodeId;
            dcLoopEnabled = parent.dcLoopEnabled;
            dcPeriod = parent.dcPeriod;
            dcDeadline = parent.dcDeadline;
            dcRspDelay = parent.dcRspDelay;
            dcRspJitter = parent.dcRspJitter;
            looseResponseMatching = default(false);
        }
        
    connections:
        in --> hpgpMac.in;
        hpgpMac.out --> out;
}