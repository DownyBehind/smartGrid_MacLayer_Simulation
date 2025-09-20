# SLAC Test Report / SLAC 상세 리포트
- Timeout / 타임아웃: 500s
- Repetitions / 반복횟수: 3

## slac_tc1
- Conditions / 조건: timeout=500s, repeats=3
- Objective / 목적: Nominal SLAC sequence order / SLAC 순서 검증
- Method / 방법: Observe ES logs of SLAC messages / SLAC 메시지 ES 로그 관찰
- Expected / 기대값: START_ATTEN×4 → M_SOUND×5 → ATTEN_CHAR → VALIDATE → SLAC_DONE
- Actual / 실제 순서: START_ATTEN → M_SOUND → ATTEN_CHAR → VALIDATE → SLAC_DONE
- Actual counts / 실제 횟수: START_ATTEN=4, M_SOUND=5, ATTEN_CHAR=1, VALIDATE=1, SLAC_DONE=1
- Runs Passed / 통과 회수: 3/3
- Run Statuses / 실행 상태: [P, P, P]
- Runner Output / 실행 출력:
```
--- run 1/3 [PASS] ---
[run.sh] slac_tc1 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/slac_tc1:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250919-08:15:21-423856
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...
Initializing channel TestBus.ev[0].plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[0].channel, stage 0
Initializing channel TestBus.evse.plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[1].channel, stage 0
Initializing module TestBus, stage 0
Initializing module TestBus.bus, stage 0
Initializing module TestBus.evse, stage 0
Initializing module TestBus.evse.plc, stage 0
Initializing module TestBus.evse.plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.evse.plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.evse.slac, stage 0
Initializing module TestBus.ev[0], stage 0
Initializing module TestBus.ev[0].plc, stage 0
Initializing module TestBus.ev[0].plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.ev[0].plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.ev[0].slac, stage 0
Initializing module TestBus.evse.plc, stage 1
[INFO]	Registering network interface, [1minterface[0m = (inet::NetworkInterface)plc plc ID:-1 MTU:1500 UP CARRIER macAddr:0A-AA-00-00-00-01, [1min[0m = (inet::NetworkInterface::LocalGate)upperLayerIn <-- slac.out, [1mout[0m = (omnetpp::cGate)upperLayerOut --> slac.in.
Initializing module TestBus.evse.plc.mac, stage 1
... (truncated) ...
```

## slac_tc2
- Conditions / 조건: timeout=500s, repeats=3
- Objective / 목적: No-EVSE timeout handling / EVSE 무응답 타임아웃
- Method / 방법: Observe timeout and retry logs / 타임아웃 및 재시도 로그 관찰
- Note / 비고: simulateNoEvse=true로 EV 노드의 SLAC_DONE 기록만 억제하여 '응답 부재' 상태를 관찰합니다 (EVSE는 실제로 응답할 수 있음). / With simulateNoEvse=true, we suppress only EV-side SLAC_DONE logging to emulate 'no response' while EVSE may still transmit.
- Expected / 기대값: EV node has START_ATTEN, no SLAC_DONE within run / EV 노드 START_ATTEN 발생, SLAC_DONE 미발생
- Actual / 실제값: hasStart=True, hasDone=False, startCount=4, doneCount=0
- Runs Passed / 통과 회수: 3/3
- Run Statuses / 실행 상태: [P, P, P]
- Runner Output / 실행 출력:
```
--- run 1/3 [PASS] ---
[run.sh] slac_tc2 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/slac_tc2:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250919-08:15:22-423941
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...
Initializing channel TestBus.ev[0].plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[0].channel, stage 0
Initializing channel TestBus.evse.plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[1].channel, stage 0
Initializing module TestBus, stage 0
Initializing module TestBus.bus, stage 0
Initializing module TestBus.evse, stage 0
Initializing module TestBus.evse.plc, stage 0
Initializing module TestBus.evse.plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.evse.plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.evse.slac, stage 0
Initializing module TestBus.ev[0], stage 0
Initializing module TestBus.ev[0].plc, stage 0
Initializing module TestBus.ev[0].plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.ev[0].plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.ev[0].slac, stage 0
Initializing module TestBus.evse.plc, stage 1
[INFO]	Registering network interface, [1minterface[0m = (inet::NetworkInterface)plc plc ID:-1 MTU:1500 UP CARRIER macAddr:0A-AA-00-00-00-01, [1min[0m = (inet::NetworkInterface::LocalGate)upperLayerIn <-- slac.out, [1mout[0m = (omnetpp::cGate)upperLayerOut --> slac.in.
Initializing module TestBus.evse.plc.mac, stage 1
... (truncated) ...
```

## slac_tc3
- Conditions / 조건: timeout=500s, repeats=3
- Objective / 목적: High BER timeout (no SLAC completion) / 고BER 타임아웃(완료 미수신)
- Method / 방법: Enable PHY BER/noise and observe EV SLAC_DONE absence / PHY BER/노이즈로 EV SLAC_DONE 부재 관찰
- Expected / 기대값: EV node has START_ATTEN, no SLAC_DONE within run / EV 노드 START_ATTEN 발생, SLAC_DONE 미발생
- Actual / 실제값: hasStart=True, hasDone=False, startCount=4, doneCount=0
- Runs Passed / 통과 회수: 3/3
- Run Statuses / 실행 상태: [P, P, P]
- Runner Output / 실행 출력:
```
--- run 1/3 [PASS] ---
[run.sh] slac_tc3 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/slac_tc3:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250919-08:15:23-424011
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...
Initializing channel TestBus.ev[0].plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[0].channel, stage 0
Initializing channel TestBus.evse.plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[1].channel, stage 0
Initializing module TestBus, stage 0
Initializing module TestBus.bus, stage 0
Initializing module TestBus.evse, stage 0
Initializing module TestBus.evse.plc, stage 0
Initializing module TestBus.evse.plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.evse.plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.evse.slac, stage 0
Initializing module TestBus.ev[0], stage 0
Initializing module TestBus.ev[0].plc, stage 0
Initializing module TestBus.ev[0].plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.00003584 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.ev[0].plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.ev[0].slac, stage 0
Initializing module TestBus.evse.plc, stage 1
[INFO]	Registering network interface, [1minterface[0m = (inet::NetworkInterface)plc plc ID:-1 MTU:1500 UP CARRIER macAddr:0A-AA-00-00-00-01, [1min[0m = (inet::NetworkInterface::LocalGate)upperLayerIn <-- slac.out, [1mout[0m = (omnetpp::cGate)upperLayerOut --> slac.in.
Initializing module TestBus.evse.plc.mac, stage 1
... (truncated) ...
```

## slac_tc4
- Conditions / 조건: timeout=500s, repeats=3
- Objective / 목적: Partial M-SOUND loss recovery / 일부 손실 복구
- Runs Passed / 통과 회수: 3/3
- Run Statuses / 실행 상태: [P, P, P]
- Runner Output / 실행 출력:
```
--- run 1/3 [PASS] ---
[run.sh] slac_tc4 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/slac_tc4:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250919-08:15:24-424092
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...
Initializing channel TestBus.ev[0].plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[0].channel, stage 0
Initializing channel TestBus.evse.plcg$o.channel, stage 0
Initializing channel TestBus.bus.port$o[1].channel, stage 0
Initializing module TestBus, stage 0
Initializing module TestBus.bus, stage 0
Initializing module TestBus.evse, stage 0
Initializing module TestBus.evse.plc, stage 0
Initializing module TestBus.evse.plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.000009 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.evse.plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.evse.slac, stage 0
Initializing module TestBus.ev[0], stage 0
Initializing module TestBus.ev[0].plc, stage 0
Initializing module TestBus.ev[0].plc.mac, stage 0
[INFO]	IEEE1901Mac initialized with parameters:
[INFO]	  txPower: 20 dBm
[INFO]	  bitrate: 2e+08 bps
[INFO]	  maxRetries: 7
[INFO]	  slotTime: 0.000009 s
[INFO]	  sifsTime: 0.00001 s
[INFO]	  difsTime: 0.000034 s
[INFO]	  cwMin: 16
[INFO]	  cwMax: 1024
[INFO]	  prs0Duration: 0.00003584 s
[INFO]	  prs1Duration: 0.00003584 s
Initializing module TestBus.ev[0].plc.phy, stage 0
[INFO]	IEEE1901Phy initialized with parameters:
[INFO]	  dataRate: 10 Mbps
[INFO]	  transmitPower: 10 dBm
[INFO]	  noisePower: -90 dBm
[INFO]	  channelAttenuation: 20 dB
[INFO]	  enableBER: true
[INFO]	  baseSNR: 25 dB
[INFO]	  berAlpha: 0.5
[INFO]	  berBeta: 0.4
[INFO]	  maxBER: 0.1
Initializing module TestBus.ev[0].slac, stage 0
Initializing module TestBus.evse.plc, stage 1
[INFO]	Registering network interface, [1minterface[0m = (inet::NetworkInterface)plc plc ID:-1 MTU:1500 UP CARRIER macAddr:0A-AA-00-00-00-01, [1min[0m = (inet::NetworkInterface::LocalGate)upperLayerIn <-- slac.out, [1mout[0m = (omnetpp::cGate)upperLayerOut --> slac.in.
Initializing module TestBus.evse.plc.mac, stage 1
... (truncated) ...
```

## Summary / 요약
- Passed / 통과: 4
- Failed / 실패: 0
