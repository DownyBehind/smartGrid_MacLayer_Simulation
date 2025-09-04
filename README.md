# Smart Grid MAC Layer Simulation

This project implements **MAC layer simulations** for smart grid communications, focusing on **CSMA/CA protocols** and **MAC efficiency analysis**. The project includes multiple simulation environments using OMNeT++ and custom Python-based simulators to analyze MAC layer performance in various network scenarios.

---

## Project Structure

```
smartGrid_MacLayer_Simulation/
├─ csma_ca_example/                    # Basic CSMA/CA simulation example
│   ├─ ned/csma_ca/
│   │   └─ CsmaCaNetwork.ned           # Network topology definition
│   └─ ini/omnetpp.ini                 # Basic simulation configuration
│
├─ csma_ca_fakewired/                  # Fake wired CSMA/CA simulation
│   ├─ ned/csma_ca_fakewired/
│   │   └─ FakeWireCsmaCaNetwork.ned   # Fake wired network topology
│   ├─ ini/omnetpp.ini                 # Simulation configuration
│   ├─ src/dataPostProcessing/         # Data analysis tools
│   │   ├─ check_backoffCnt.py
│   │   ├─ postProcessing.py
│   │   └─ data/                       # Processed data storage
│   └─ scan_results.py                 # Results scanning utility
│
├─ csma_ca_test_for_Ayar_Paper/        # Ayar et al. (2015) paper reproduction
│   ├─ ned/csma_ca_test_for_Ayar_Paper/
│   │   ├─ FakeWireCsmaCaNetwork.ned   # Network topology for paper reproduction
│   │   └─ FakeWireCsmaCaNetwork.ned.bak
│   ├─ ini/
│   │   ├─ omnetpp.ini                 # Main simulation configuration
│   │   └─ results/                    # Batch simulation results
│   ├─ src/dataPostProcessing/         # Post-processing tools
│   │   ├─ calc_mac_efficiency.py      # MAC efficiency calculations
│   │   ├─ check_backoffCnt.py
│   │   ├─ postProcessing.py
│   │   ├─ mac_efficiency_vs_nodes.png # Generated analysis plots
│   │   └─ data/
│   ├─ src/runSimulation/              # Simulation automation
│   │   └─ efficiency_analysis.py      # Comprehensive efficiency analysis
│   ├─ runconfig.txt                   # Run configuration settings
│   └─ scan_results.py                 # Results scanning utility
│
├─ csma_ca_wired/                      # Wired CSMA/CA simulation
│   ├─ ned/csma_ca/                    # Network definitions
│   └─ ini/omnetpp.ini                 # Wired simulation configuration
│
├─ simulator_simpleAndQuick/           # Python-based HPGP simulator
│   ├─ hpgp_sim/                       # Core simulator modules
│   │   ├─ __init__.py
│   │   ├─ app_15118.py                # Application layer (ISO 15118)
│   │   ├─ channel.py                  # Channel modeling
│   │   ├─ mac_hpgp.py                 # HomePlug Green PHY MAC
│   │   ├─ medium.py                   # Physical medium simulation
│   │   ├─ metrics.py                  # Performance metrics
│   │   ├─ sim.py                      # Main simulator engine
│   │   └─ utils.py                    # Utility functions
│   ├─ config/                         # Simulation configurations
│   │   ├─ defaults.json               # Default parameters
│   │   ├─ shared_bus_5.json           # 5-node shared bus config
│   │   ├─ shared_bus.json             # General shared bus config
│   │   └─ tmp_N*.json                 # Node count sweep configs (N=2-100)
│   ├─ scripts/                        # Automation scripts
│   │   ├─ run_demo.py                 # Demo simulation runner
│   │   └─ sweep_nodes.py              # Node count parameter sweep
│   ├─ hpgp_simulator_py.zip           # Packaged simulator
│   └─ README.md                       # Simulator documentation
│
├─ StudyForPrevPapers/                 # Previous research analysis
│   └─ MAC_Throughput_Analysis_of_HomePlug_1.0/
│       ├─ calculate3dMarkovChainModelAboutHPGP.py  # Markov chain analysis
│       └─ README.md
│
└─ TimeSlot/                           # Time-slot based probe implementation
    ├─ MediumBusyIdleProbe.{h,cc}      # Idle/Busy slot counting
    ├─ TxOutcomeProbe.{h,cc}           # Success/Collision slot & time counting
    ├─ SendIntervalConfigurator.{h,cc} # Auto-configure sendInterval
    ├─ timeslot/TimeSlotProbes.ned     # NED definitions for probes
    ├─ Makefile                        # Build configuration
    ├─ libtimeslot.so                  # Compiled library
    └─ README.md                       # TimeSlot module documentation
```

---

## Key Components

### 1. CSMA/CA Simulation Environments

- **csma_ca_example/**: Basic CSMA/CA simulation setup for learning and testing
- **csma_ca_fakewired/**: Simulation with fake wired connections for controlled testing
- **csma_ca_wired/**: Traditional wired CSMA/CA implementation
- **csma_ca_test_for_Ayar_Paper/**: Specific implementation to reproduce results from Ayar et al. (2015)

### 2. Python-based HPGP Simulator

The `simulator_simpleAndQuick/` directory contains a comprehensive Python-based simulator for **HomePlug Green PHY (HPGP)** protocol analysis:

- **Core Modules**: MAC layer, channel modeling, medium simulation, and metrics collection
- **Application Support**: ISO 15118 application layer implementation
- **Configuration System**: JSON-based parameter configuration with support for parameter sweeps
- **Automation**: Scripts for running demos and parameter sweeps across different node counts

### 3. TimeSlot Probe Implementation

Custom OMNeT++ modules for detailed MAC layer analysis:

- **Probes**: Medium busy/idle detection, transmission outcome tracking
- **Configurators**: Automatic parameter adjustment based on network size
- **Integration**: Seamless integration with OMNeT++ simulation framework

### 4. Data Analysis Tools

Comprehensive post-processing and analysis capabilities:

- **MAC Efficiency Calculation**: Slot-based and time-based efficiency metrics
- **Collision Analysis**: Collision probability and backoff behavior analysis
- **Throughput Analysis**: Network throughput under various conditions
- **Visualization**: Automated plot generation for research presentations

---

## Research Focus Areas

### MAC Efficiency Analysis

Reproduction and extension of results from Ayar et al. (2015), focusing on:

- **Idle/Success/Collision** slot-time based MAC efficiency curves
- **Throughput** analysis under various network loads
- **Collision Probability** calculations and modeling

### HomePlug Green PHY (HPGP) Protocol

Detailed simulation and analysis of HPGP for smart grid applications:

- **ISO 15118** application layer integration
- **Multi-node** network scenarios (2-100 nodes)
- **Parameter sweep** capabilities for comprehensive analysis

### Smart Grid Communications

Application of MAC layer protocols to smart grid scenarios:

- **Power line communication** modeling
- **Vehicle-to-Grid (V2G)** communication protocols
- **Network scalability** analysis for large-scale deployments

---

## Usage Instructions

### OMNeT++ Simulations

1. **Build TimeSlot Library**

   ```bash
   cd TimeSlot
   export INET_PROJ=~/.../inet
   opp_makemake -f -I$INET_PROJ/src -L$INET_PROJ/out/clang-release/src -lINET -o timeslot
   make -j
   ```

2. **Run Individual Simulations**

   ```bash
   cd csma_ca_test_for_Ayar_Paper
   opp_run -u Cmdenv -n "<inet;ned;TimeSlot>" -c Paper_Baseline omnetpp.ini
   ```

3. **Analyze Results**
   ```bash
   cd src/dataPostProcessing
   python calc_mac_efficiency.py
   python postProcessing.py
   ```

### Python HPGP Simulator

1. **Run Demo Simulation**

   ```bash
   cd simulator_simpleAndQuick/scripts
   python run_demo.py
   ```

2. **Parameter Sweep**

   ```bash
   python sweep_nodes.py
   ```

3. **Custom Configuration**
   - Edit JSON files in `config/` directory
   - Modify parameters for specific scenarios
   - Run with custom configurations

---

## Output and Results

### Generated Files

- **Simulation Results**: `.sca`, `.vec`, `.vci` files from OMNeT++
- **Analysis Data**: CSV files with computed metrics
- **Visualizations**: PNG plots showing efficiency, throughput, and collision analysis
- **Logs**: Detailed execution logs for debugging and verification

### Key Metrics

- **MAC Efficiency (η)**: Slot-based and time-based calculations
- **Throughput**: Network throughput in Mbps
- **Collision Probability**: P_coll calculations
- **Backoff Analysis**: CSMA/CA backoff behavior analysis

---

## Contributing

When adding new simulations or analysis tools:

1. Follow the existing directory structure
2. Include appropriate documentation in README files
3. Ensure compatibility with existing analysis scripts
4. Add configuration files for parameter sweeps when applicable

---

For detailed information about specific components, refer to the README files in individual subdirectories.
