simple ChannelManager
{
    parameters:
        int numNodes = default(5);
        double slotTime @unit(s) = default(20us);
        double sifs @unit(s) = default(10us);
        double difs @unit(s) = default(50us);
        double bitrate @unit(bps) = default(10Mbps);
    
    gates:
        input nodeIn[10];  // 최대 10개 노드 지원
        output nodeOut[10];
}

