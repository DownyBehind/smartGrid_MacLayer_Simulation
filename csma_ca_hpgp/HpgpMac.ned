package csma_ca_hpgp;

//
// HomePlug 1.0 MAC Layer
// Implements Priority Resolution + BPC/DC/BC based CSMA/CA
// Based on Table I parameters from Jung et al. (2005)
//

simple HpgpMac
{
    parameters:
        // HomePlug 1.0 standard timing parameters
        double cifs @unit(s) = default(35.84us);
        double rifs @unit(s) = default(26us);
        double prs0 @unit(s) = default(35.84us);
        double prs1 @unit(s) = default(35.84us);
        double slotTime @unit(s) = default(35.84us);
        int bpcMax = default(4);
        string priorityGroup = default("CA23"); // "CA23" or "CA01"
        
        // Logging parameters
        bool recordTxAttempts = default(false);
        bool recordCollisions = default(false);
        bool recordSlacMessages = default(false);
        bool recordDcCycles = default(false);
        
        // SLAC and DC parameters
        string nodeType = default("EV");
        int nodeId = default(0);
        string scenario = default("Default"); // WC_A_Sequential, WC_B_Simultaneous, Default
        bool dcLoopEnabled = default(true);
        double dcPeriod @unit(s) = default(100ms);
        double dcDeadline @unit(s) = default(100ms);
        double dcRspDelay @unit(s) = default(1.5ms);
        double dcRspJitter @unit(s) = default(0ms);
        
    gates:
        input in;
        output out;
}