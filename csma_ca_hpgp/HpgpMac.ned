//
// HPGP MAC Module
// Implements CSMA/CA with priority-based access
//

simple HpgpMac
{
    parameters:
        int cwMin = default(8);
        int cwMax = default(1024);
        int maxRetries = default(3);
        double slotTime @unit(s) = default(20us);
        double sifs @unit(s) = default(10us);
        double difs @unit(s) = default(50us);
        
        // Priority-specific parameters
        int cap0CwMin = default(8);
        int cap0CwMax = default(64);
        int cap1CwMin = default(8);
        int cap1CwMax = default(64);
        int cap2CwMin = default(8);
        int cap2CwMax = default(32);
        int cap3CwMin = default(8);
        int cap3CwMax = default(32);
        
        double bitrate @unit(bps) = default(10Mbps);
        
    gates:
        input in;
        output out;
}

