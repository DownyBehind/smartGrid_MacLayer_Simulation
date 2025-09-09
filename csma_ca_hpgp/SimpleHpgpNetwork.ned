import SlacNode;

//
// Simple HPGP Network for SLAC simulation
// Replicates basic functionality without complex networking dependencies
//

network SimpleHpgpNetwork
{
    parameters:
        int numNodes = default(10);
        
    submodules:
        node[numNodes]: SlacNode {
            nodeId = index;
            nodeType = (index == 0) ? "EVSE" : "EV";
        }
        
    connections allowunconnected:
        // Connect nodes in a simple chain for now
        for i=0..numNodes-2 {
            node[i].out --> node[i+1].in;
        }
}
