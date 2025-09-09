package csma_ca_hpgp;

message SlacMessage extends cPacket
{
    int messageType;
    int sourceId;
    int destId;
    int priority;
    double txPower = 1.0;
    simtime_t transmissionTime;
}