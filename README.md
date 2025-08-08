# Project Overview

This project implements a **MAC time-slot based Tx Outcome Probe** in an IEEE 802.11 DCF wireless network to reproduce the **Idle / Success / Collision** slot-time based **MAC efficiency (η)** curve from Ayar et al. (2015), specifically Figure 1 of their paper. It also extends the analysis to include **Throughput**, **Collision Probability**, and other key metrics.

---

## Directory Structure

```
project_smartCharging_macLayer_improvement/
├─ TimeSlot/                       # Probe module implementation
│   ├─ MediumBusyIdleProbe.h/.cc    # Idle/Busy slot counting
│   ├─ TxOutcomeProbe.h/.cc         # Success/Collision slot & time counting
│   └─ SendIntervalConfigurator.h/.cc  # Auto-configure sendInterval
├─ csma_ca_test_for_Ayar_Paper/
│   ├─ ned/
│   │   └─ FakeWireCsmaCaNetwork.ned  # Network topology definition
│   ├─ ini/
│   │   ├─ omnetpp.ini               # Simulation configuration
│   │   └─ results/                  # Output files (.sca, .vec, .vci, etc.)
│   └─ src/dataPostProcessing/
│       └─ calc_mac_efficiency.py    # Original MAC efficiency script
└─ csma_ca_test_for_Ayar_Paper/src/runSimulation/
    ├─ run_simulation.py            # Batch simulation automation script
    └─ efficiency_analysis.py       # Efficiency, Throughput, Collision analysis script
```

---

## Development Progress

| Step | Task                                                                    | Status  |
| :--: | :---------------------------------------------------------------------- | :------ |
|   1  | Confirmed MAC/RADIO types (Ieee80211Mac / Ieee80211ScalarRadio)         | Done    |
|   2  | Implemented ACK detection and success/collision logic in TxOutcomeProbe | Done    |
|   3  | Subscribed to all relevant MAC signals                                  | Done    |
|   4  | Configured MAC parameters (ackPolicy, CW, etc.)                         | Done    |
|   5  | Set timing parameters (SIFS, CIFS, ackTxTime, ackTimeout)               | Done    |
|   6  | (Optional) Document MAC submodule tree                                  | On Hold |
|   7  | (Optional) Capture and analyze eventlog                                 | On Hold |
|   8  | Verified debug scalars and vectors                                      | Done    |

---

## Key Implementation Details

### TimeSlotProbes NED Modules

* `MediumBusyIdleProbe`: Counts idle/busy slots
* `TxOutcomeProbe`: Records success/collision slots and durations
* `SendIntervalConfigurator`: Computes `sendInterval` based on node count
* `WirelessHostWithProbe`: Attaches probes to each host

### C++ Source Files

* **MediumBusyIdleProbe.{h,cc}**: Scalars `ni_idle_slots`, `nb_busy_slots` recorded
* **TxOutcomeProbe.{h,cc}**: Scalars `ns_success_slots`, `nc_collision_slots`, `ts_success_time`, `tc_collision_time` recorded
* **SendIntervalConfigurator.{h,cc}**: Reads `numHosts` parameter to set application `sendInterval`

### omnetpp.ini Configuration

* **Saturation Test**: `*.host[*].app[0].sendInterval = 1.5ms`
* **Load-Balanced Test**: `*.host[*].app[0].sendInterval = ${=1.5ms*${numHosts}/5}`
* Detailed DCF/EDCA, CW, ACK, and channel parameters set to match the paper

---

## Automation Scripts

### run\_simulation.py

Automatically runs simulations for `N = [5,10,15,20,25,30,…]` by:

1. Invoking OMNeT++:

   ```bash
   opp_run -u Cmdenv -n "<inet;ned;TimeSlot>" -x numHosts=N -c Paper_Baseline omnetpp.ini
   ```
2. Organizing output files into `ini/results/n<N>/`

### efficiency\_analysis.py

Parses each `n<N>/` folder’s `.sca` file to compute:

* Slot-based MAC efficiency (η\_slot)
* Collision probability (P\_coll)
* Throughput (Mbps)

Outputs:

* **CSV**: `mac_additional_metrics.csv`
* **Plots**: `eta_slot_vs_nodes.png`, `p_coll_vs_nodes.png`, `throughput_vs_nodes.png`

---

## Analysis Summary

1. **Load-Balanced Test**: When `sendInterval ∝ N`, aggregate offered load is constant, resulting in decreasing η and collision rate as N increases (underload regime).
2. **Saturation Test**: When `sendInterval` is fixed, increasing N leads to channel saturation: η drops sharply and collision probability rises, matching Figure 1 behavior.
3. **Reproducing Figure 1**: Set `sendInterval = 1.5ms` (fixed) and run saturation tests.

---

## Usage Instructions

1. **Build TimeSlot Library**

   ```bash
   cd TimeSlot
   export INET_PROJ=~/.../inet
   opp_makemake -f -I$INET_PROJ/src -L$INET_PROJ/out/clang-release/src -lINET -o timeslot
   make -j
   ```
2. **Run Batch Simulations**

   ```bash
   cd csma_ca_test_for_Ayar_Paper
   ./src/runSimulation/run_simulation.py   # Runs for N=5,10,15,...
   ```
3. **Analyze Results**

   ```bash
   cd src/runSimulation
   ./efficiency_analysis.py  # Generates CSV and plots
   ```

---

For questions or issues, refer to the scripts (`calc_mac_efficiency.py`, `run_simulation.py`, `efficiency_analysis.py`) or update this README.
