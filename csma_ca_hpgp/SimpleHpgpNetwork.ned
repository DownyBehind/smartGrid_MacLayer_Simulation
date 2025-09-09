import SlacNode;
import ChannelManager;

//
// Simple HPGP Network for SLAC simulation with Shared Channel
// Uses Channel Manager for collision detection and CSMA/CA
//

network SimpleHpgpNetwork
{
    parameters:
        int numNodes = default(5);
        
    submodules:
        channelManager: ChannelManager {
            numNodes = parent.numNodes;
        }
        node[numNodes]: SlacNode {
            nodeId = index;
            nodeType = (index == 0) ? "EVSE" : "EV";
        }
        
connections allowunconnected:
    // All nodes connected to Channel Manager for shared medium simulation
    for i=0..numNodes-1 {
        node[i].out --> channelManager.nodeIn[i];
        channelManager.nodeOut[i] --> node[i].in;
    }
}
