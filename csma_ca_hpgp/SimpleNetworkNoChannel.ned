package csma_ca_hpgp;

import SlacNode;
import ChannelManager;

//
// Shared Bus Network with ChannelManager
// All nodes connected to shared medium for contention simulation
//

network SimpleNetworkNoChannel
{
    parameters:
        int numNodes = default(5);
        
    submodules:
        node[numNodes]: SlacNode {
            nodeId = index;
            nodeType = (index == 0) ? "EVSE" : "EV";
        }
        
        // Channel Manager for shared medium
        channelManager: ChannelManager {
            numNodes = parent.numNodes;
        }
        
    connections allowunconnected:
        // Shared Bus: 모든 노드가 ChannelManager에 연결
        for i=0..numNodes-1 {
            node[i].out --> channelManager.nodeIn[i];
            channelManager.nodeOut[i] --> node[i].in;
        }
}