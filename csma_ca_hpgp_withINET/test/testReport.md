# Test Report (Detailed / 상세 리포트)

- Timeout / 타임아웃: 500s
- Repetitions / 반복횟수: 10

## tc1
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Enforce PRS0/PRS1 durations and slotTime slot increments / PRS0/PRS1 지속시간과 슬롯 간격(slotTime) 검증
- Method / 방법: Parse ES(prs0/prs1/backoff/tx) durations and slot steps / 이벤트로그 ES(prs0/prs1/backoff/tx)로 지속시간·슬롯 간격 파싱
- Expected / 기대값: PRS0=3.584000e-05s, PRS1=3.584000e-05s, estimatedSlotTime=3.584000e-05s
- Actual / 실제값: PRS0=3.584000e-05s, PRS1=3.584000e-05s, estimatedSlotTime=1.592889e-05s
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc1 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:34-291701
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 8e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 18   present: 18   in FES: 3
** Event #253   t=5   Elapsed: 0.002392s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 65   present: 18   in FES: 2

<!> Simulation time limit reached -- at t=5s, event #253

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc1 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:34-291719
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 8e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 18   present: 18   in FES: 3
** Event #253   t=5   Elapsed: 0.002354s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 65   present: 18   in FES: 2

<!> Simulation time limit reached -- at t=5s, event #253

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc1 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1:  0

... (truncated) ...
```

## tc2
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Winner must be among first PRS1-window contenders / 최초 PRS1 윈도우 경쟁자 중에서 승자 결정
- Method / 방법: Compare first PRS1-window contenders vs earliest TX module / PRS1 최초 윈도우 경쟁자와 가장 빠른 TX 모듈 비교
- Expected / 기대값: winner∈contenders at t0 / 승자는 최초 윈도우 경쟁자 집합에 포함
### Inventory / 인벤토리
- All MAC IDs / 전체 MAC ID: 5 (SLAC CAP=3, DC CAP=0 for all)
  - MAC ID(20), Node(evse), CAP(3)
  - MAC ID(24), Node(ev[0]), CAP(3)
  - MAC ID(28), Node(ev[1]), CAP(3)
  - MAC ID(32), Node(ev[2]), CAP(3)
  - MAC ID(36), Node(ev[3]), CAP(3)

- Note / 참고: dcPriority=0 for all nodes (same-CAP contention) / 모든 노드 dcPriority=0(동일 CAP 경쟁)

### Windows / 윈도우
- First 30 PRS1 windows / 첫 30개 PRS1 윈도우
  - Window 1 @ t0=1.716800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 2 @ t0=2.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 3 @ t0=4.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 4 @ t0=6.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 5 @ t0=8.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 6 @ t0=1.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 7 @ t0=1.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 8 @ t0=1.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 9 @ t0=1.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(10)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 10 @ t0=1.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 11 @ t0=2.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 12 @ t0=2.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 13 @ t0=2.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 14 @ t0=2.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 15 @ t0=2.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 16 @ t0=3.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 17 @ t0=3.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(10)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 18 @ t0=3.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 19 @ t0=3.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 20 @ t0=3.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 21 @ t0=4.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 22 @ t0=4.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 23 @ t0=4.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(8)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 24 @ t0=4.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 25 @ t0=4.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 26 @ t0=5.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 27 @ t0=5.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 28 @ t0=5.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 29 @ t0=5.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 30 @ t0=5.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(12)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots

- Evidence / 증거: see `/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2/results/General-#0.elog`
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc2 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:37-291961
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 7e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 45   present: 45   in FES: 6
** Event #1117   t=6.2   Elapsed: 0.010427s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=107187   simsec/sec=575.796   ev/simsec=186.155
     Messages:  created: 263   present: 45   in FES: 5

<!> Simulation time limit reached -- at t=6.2s, event #1117

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc2 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:37-291995
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 1.1e-05s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 45   present: 45   in FES: 6
** Event #1117   t=6.2   Elapsed: 0.010955s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=102028   simsec/sec=548.079   ev/simsec=186.155
     Messages:  created: 263   present: 45   in FES: 5

<!> Simulation time limit reached -- at t=6.2s, event #1117

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc2 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2:  0

... (truncated) ...
```

## tc3
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Backoff slot mean≈slotTime / 백오프 슬롯 평균 간격≈슬롯시간
- Method / 방법: Compute mean of BS(backoffTimer) intervals / BS(backoffTimer) 간격 평균 계산
- Expected / 기대값: mean≈3.584000e-05s (validator-aligned)
- Actual / 실제값: mean=3.584000e-05s (validator-aligned)
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc3 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:41-292218
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 7e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 18   present: 18   in FES: 3
** Event #1472   t=5   Elapsed: 0.013027s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=113039   simsec/sec=382.443   ev/simsec=295.572
     Messages:  created: 207   present: 18   in FES: 2

<!> Simulation time limit reached -- at t=5s, event #1472

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc3 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:41-292260
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 8e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 18   present: 18   in FES: 3
** Event #1472   t=5   Elapsed: 0.011996s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=122769   simsec/sec=415.36   ev/simsec=295.572
     Messages:  created: 207   present: 18   in FES: 2

<!> Simulation time limit reached -- at t=5s, event #1472

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc3 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3:  0

... (truncated) ...
```

## tc4
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Validate full sequence PRS0→PRS1→Backoff→TX→RIFS→CIFS→next PRS0 / 전체 MAC 시퀀스 검증
- Method / 방법: Check ES timers order and durations (PRS≈slot, RIFS/CIFS presence) / PRS≈슬롯시간, RIFS/CIFS 존재 확인
- Expected / 기대값: PRS0≈3.584000e-05s, PRS1≈3.584000e-05s, backoffExists=True, rifsExists=True, cifsExists=True; counts>0
- Actual / 실제값: d0=3.584000e-05s, d1=3.584000e-05s, backoffExists=True, rifsExists=True, cifsExists=True, counts(PRS1,TX)=(750,389)
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc4 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:44-292464
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 7e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 63   present: 63   in FES: 8
** Event #6098   t=5   Elapsed: 0.051995s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=117299   simsec/sec=95.4156   ev/simsec=1229.34
     Messages:  created: 965   present: 63   in FES: 7

<!> Simulation time limit reached -- at t=5s, event #6098

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc4 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:44-292488
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 7e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 63   present: 63   in FES: 8
** Event #6098   t=5   Elapsed: 0.05409s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=112759   simsec/sec=91.7229   ev/simsec=1229.34
     Messages:  created: 965   present: 63   in FES: 7

<!> Simulation time limit reached -- at t=5s, event #6098

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc4 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4:  0

... (truncated) ...
```

## tc5
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Verify per-message CAP cycling 3→2→1→0 / 메시지별 CAP 순환(3→2→1→0) 검증
- Method / 방법: Enable SlacApp.enableDcPriorityCycle and observe PRS windows & winners / SlacApp.enableDcPriorityCycle 활성화 후 윈도우·승자 관찰
- Expected / 기대값: Across windows, winners vary over time consistent with CAP cycling / 윈도우가 진행되며 승자가 순환 특성을 반영
### Inventory / 인벤토리
- All MAC IDs / 전체 MAC ID: 5 (SLAC CAP=3, DC CAP cycles per message)
| MAC ID | Node | initCAP |
|---:|:---|---:|
| 20 | evse | 3 |
| 24 | ev[0] | 3 |
| 28 | ev[1] | 3 |
| 32 | ev[2] | 3 |
| 36 | ev[3] | 3 |

### Windows / 윈도우
- First 15 PRS1 windows / 첫 15개 PRS1 윈도우
  - Window 1 @ t0=1.716800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
  - Window 2 @ t0=2.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
  - Window 3 @ t0=4.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(8)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(8)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
  - Window 4 @ t0=6.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(6)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 5 @ t0=8.001717e-01
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(8)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(4)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(12)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(8)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(12)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
  - Window 6 @ t0=1.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(8)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
  - Window 7 @ t0=1.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(10)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 8 @ t0=1.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 9 @ t0=1.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(10)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(10)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(10)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
  - Window 10 @ t0=1.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
  - Window 11 @ t0=2.000172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 12 @ t0=2.200172e+00
    - Contenders / 경쟁자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 13 @ t0=2.400172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(12)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(12)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(12)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(12)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(12)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
  - Window 14 @ t0=2.600172e+00
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(12)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(12)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
  - Window 15 @ t0=2.800172e+00
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)

- CAP_LOG (runtime) / 런타임 CAP 로그:
```
```
- Evidence / 증거: see `/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/General-#0.elog` and `/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/sim.out`
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc5 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:48-292698
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 9e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 45   present: 45   in FES: 6
** Event #1282   t=6   Elapsed: 0.011711s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=109535   simsec/sec=495.592   ev/simsec=221.019
     Messages:  created: 259   present: 45   in FES: 5

<!> Simulation time limit reached -- at t=6s, event #1282

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc5 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5:  0

Preparing for running configuration General, run #0...
Assigned runID=General-0-20250918-21:00:48-292733
Setting up network "test.common.TestBus"...
Recording eventlog to file `results/General-#0.elog'...
Initializing...

Running simulation...
** Event #0   t=0   Elapsed: 7e-06s (0m 00s)  0% completed  (0% total)
     Speed:     ev/sec=0   simsec/sec=0   ev/simsec=0
     Messages:  created: 45   present: 45   in FES: 6
** Event #1282   t=6   Elapsed: 0.011517s (0m 00s)  100% completed  (100% total)
     Speed:     ev/sec=111372   simsec/sec=503.901   ev/simsec=221.019
     Messages:  created: 259   present: 45   in FES: 5

<!> Simulation time limit reached -- at t=6s, event #1282

Calling finish() at end of Run #0...
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc5 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5:  0

... (truncated) ...
```

## Summary / 요약
- Passed / 통과: 5
- Failed / 실패: 0
