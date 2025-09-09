# HPGP SLAC Simulation with OMNET++

This project implements HPGP (HomePlug Green PHY) SLAC (Signal Level Attenuation Characterization) simulation using OMNET++ and INET framework with IEEE1901 Power Line Communication support.

## Overview

Based on the Python simulator in `../simulator_simpleAndQuick/`, this OMNET++ implementation provides a comprehensive simulation environment for studying SLAC protocol performance in smart charging scenarios, specifically for **ISO15118 MAC Layer 실험**.

### Key Features

- **IEEE1901 Power Line Communication**: Complete MAC/PHY layer simulation using `inet_plc/inet`
- **Full SLAC Protocol**: Implementation of all 9 SLAC message types (CM_SLAC_PARM, CM_START_ATTEN_CHAR, CM_MNBC_SOUND, etc.)
- **Multi-node Scenarios**: Support for multiple EVSE and EV nodes with concurrent SLAC procedures
- **Comprehensive Metrics**: SLAC completion time, retry counts, success rates, timeout analysis
- **Multiple Configurations**: Various test scenarios from baseline to high-density deployments
- **Automated Analysis**: Python-based result analysis with statistical summaries and visualizations

### Research Objectives

**Primary Goal**: "여러 노드가 연결되어 있을 때, SLAC이 동시에 불리면 지연이 얼마나 발생하는지를 확인"

This simulation measures:
- SLAC completion delays with multiple concurrent nodes
- Impact of network density on SLAC performance  
- Retry patterns and failure rates under various conditions
- Performance comparison between single vs. multiple EVSE scenarios
- MAC layer contention effects on ISO15118 SLAC procedures

## Project Structure

```
csma_ca_hpgp/
├── src/
│   ├── HpgpNetwork.ned         # Network topology definition
│   ├── HpgpNode.ned           # Node configuration  
│   ├── SlacApplication.h      # SLAC protocol header
│   └── SlacApplication.cc     # SLAC protocol implementation
├── omnetpp.ini                # Simulation configurations
├── Makefile                   # Build configuration
├── run_simulation.sh          # Automated simulation runner
├── analyze_results.py         # Results analysis tool
└── README.md                  # This file
└── README.md
```

## 사용법

1. 환경 설정:
```bash
cd /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement
source setup_inet_plc_env.sh
```

2. 시뮬레이션 실행:
```bash
cd csma_ca_hpgp
opp_run -r 0..4 -m -u Cmdenv -c General -n ../src:${INET_DIR}/src --image-path=${INET_DIR}/images -l ${INET_DIR}/out/clang-release/src/libINET.so ini/omnetpp.ini
```

## 참고

- 기반이 된 파이썬 시뮬레이터: `../simulator_simpleAndQuick/`
- IEEE 1901 PLC 구현: `inet_plc/inet/src/inet/linklayer/plc/`
- 관련 논문: Ayar et al. - 2015 - An adaptive MAC for HomePlug Green PHY PLC
