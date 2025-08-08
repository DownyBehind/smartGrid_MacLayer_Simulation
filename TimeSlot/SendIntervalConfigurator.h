#pragma once
#include <omnetpp.h>
using namespace omnetpp;

class SendIntervalConfigurator : public cSimpleModule
{
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage*) override {}  // No runtime msgs
};
