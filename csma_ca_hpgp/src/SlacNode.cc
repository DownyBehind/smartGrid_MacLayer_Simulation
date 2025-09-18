#include <omnetpp.h>

using namespace omnetpp;

class SlacNode : public cSimpleModule
{
protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage* msg) override;
};

Define_Module(SlacNode);

void SlacNode::initialize()
{
    // SlacNode는 단순한 패스스루 모듈
    // 모든 메시지를 HpgpMac으로 전달
}

void SlacNode::handleMessage(cMessage* msg)
{
    // 들어오는 메시지를 HpgpMac으로 전달
    if (msg->arrivedOn("in")) {
        // ChannelManager에서 온 메시지를 HpgpMac으로 전달
        if (strcmp(msg->getName(), "DC_REQUEST") == 0) {
            printf("[%.3f] SlacNode: Received DC_REQUEST from ChannelManager, forwarding to HpgpMac\n", simTime().dbl());
            fflush(stdout);
        }
        send(msg, "out");
    }
    else if (msg->arrivedOn("out")) {
        // HpgpMac에서 온 메시지를 ChannelManager로 전달
        send(msg, "in");
    }
    else {
        // 알 수 없는 메시지 - 삭제
        delete msg;
    }
}
