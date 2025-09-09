// Wrapper host that provides PLC interface
module PlcHost
{
    parameters:
        numWlanInterfaces = default(1);
        
    gates:
        inout plc; // Exposed PLC gate to connect to wired PLC medium
        
    connections allowunconnected:
        // For now, just pass through
        // plcInterface.plc <--> plc;
}
