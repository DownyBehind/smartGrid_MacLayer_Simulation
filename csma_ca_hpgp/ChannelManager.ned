package csma_ca_hpgp;

simple ChannelManager
{
    parameters:
        int numNodes = default(5);
        double slotTime @unit(s) = default(20us);
        double sifs @unit(s) = default(10us);
        double difs @unit(s) = default(50us);
        double bitrate @unit(bps) = default(10Mbps);
        
        // Channel model parameters
        double per = default(0.0);
        bool impulseNoiseEnabled = default(false);
        bool ispBusyEnabled = default(false);
        double impulseDuration @unit(s) = default(1ms);
        double ispBusyProbability = default(0.1);
        double ispBusyMeanDuration @unit(s) = default(2ms);
    
    gates:
        input nodeIn[10];  // 최대 10개 노드 지원
        output nodeOut[10];
}

