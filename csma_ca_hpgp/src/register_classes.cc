#include "SlacApplication.h"
#include "HpgpMac.h"
#include "ChannelManager.h"

// Manual class registration
void registerAllClasses() {
    // Register SlacApplication
    omnetpp::cObjectFactory *slacFactory = new omnetpp::cObjectFactory(
        omnetpp::opp_typename(typeid(SlacApplication)),
        []() -> omnetpp::cObject* { return new SlacApplication; },
        [](omnetpp::cObject *obj) -> void* { return dynamic_cast<SlacApplication*>(obj); },
        "module"
    );
    omnetpp::internal::classes.getInstance()->add(slacFactory);
    
    // Register HpgpMac
    omnetpp::cObjectFactory *macFactory = new omnetpp::cObjectFactory(
        omnetpp::opp_typename(typeid(HpgpMac)),
        []() -> omnetpp::cObject* { return new HpgpMac; },
        [](omnetpp::cObject *obj) -> void* { return dynamic_cast<HpgpMac*>(obj); },
        "module"
    );
    omnetpp::internal::classes.getInstance()->add(macFactory);
    
    // Register ChannelManager
    omnetpp::cObjectFactory *channelFactory = new omnetpp::cObjectFactory(
        omnetpp::opp_typename(typeid(ChannelManager)),
        []() -> omnetpp::cObject* { return new ChannelManager; },
        [](omnetpp::cObject *obj) -> void* { return dynamic_cast<ChannelManager*>(obj); },
        "module"
    );
    omnetpp::internal::classes.getInstance()->add(channelFactory);
}

// Execute registration on startup
EXECUTE_ON_STARTUP(registerAllClasses());
