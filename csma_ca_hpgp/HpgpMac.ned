//
// HomePlug 1.0 MAC Layer
// Implements Priority Resolution + BPC/DC/BC based CSMA/CA
// Based on Table I parameters from Jung et al. (2005)
//

simple HpgpMac
{
    parameters:
        // HomePlug 1.0 standard timing parameters
        double cifs @unit(s) = default(35.84us);
        double rifs @unit(s) = default(26us);
        double prs0 @unit(s) = default(35.84us);
        double prs1 @unit(s) = default(35.84us);
        double slotTime @unit(s) = default(35.84us);
        int bpcMax = default(4);
        string priorityGroup = default("CA23"); // "CA23" or "CA01"
        
    gates:
        input in;
        output out;
}