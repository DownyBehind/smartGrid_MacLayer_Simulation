### Step 1. Analysis of Differences Between Current Experimental Environment and Thesis Environment

| Item | Thesis Environment (Figure 1) | Current Experimental Environment | Differences & Considerations |
| :--- | :--- | :--- | :--- |
| **Medium Environment** | Wired (Powerline communication-based HomePlug Green PHY) | Wireless (802.11g based), approximating the wireless environment with FreeSpacePathLoss | The current method of modeling a wired PLC environment as wireless has differences in channel characteristics, interference, and delay. |
| **Network Configuration** | Single receiver + multiple transmitters (Star network) | 1 central receiving node + multiple transmitting nodes (Centralized structure is similar) | The similarity in network structure is sufficiently met. |
| **MAC Protocol** | HPGP MAC (CSMA/CA based, similar to EDCA but uses a clearly defined BEB and priority channel access) | Using IEEE 802.11 EDCA mode (`mac.useEdca=true`) | The essence of the MAC protocol is similar, but parameter tuning is needed (e.g., CW value, AIFSN). |
| **CW Parameter** | CW fixed at 7 (non-exponential BEB), making the contention window adaptively change. | CW values are set differently for each AC of EDCA, but adaptive dynamic adjustment is not implemented. | Needs to be matched with the thesis environment by setting a fixed CW=7. |
| **Retry Count Limit** | Retry limit exists (packet dropped after 7 failures). | Currently, retry limit is not explicitly set (using default value). | Explicit setting of the retry limit is needed (e.g., setting `retryLimit`). |
| **Traffic Characteristics** | Traffic sent at a constant interval (regular interval, inferred as 0.5ms~5ms from the thesis). | Currently set with constant traffic at a 0.5ms interval. | The traffic transmission interval is similar. |
| **Packet Size** | Not specified in the thesis, but in a PLC environment, messages are generally short (tens to hundreds of bytes). | Currently using a rather large packet size of 1500 bytes. | Needs to be changed to a smaller packet (though it can be maintained as is for initial experiments). |
| **ACK Usage** | Not explicitly specified in the thesis, but ACK usage is generally assumed. | By default, IEEE 802.11 EDCA uses ACK. | Similar. |


#### Ref 
M. Ayar, H. A. Latchman and J. McNair, "An adaptive MAC for HomePlug Green PHY PLC to support realistic smart grid applications," in 2015 IEEE International Conference on Smart Grid Communications (SmartGridComm), Miami, FL, USA, 2015, pp. 587–592. doi: 10.1109/SmartGridComm.2015.7436348