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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc1/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
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
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 2 @ t0=3.360000e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 3 @ t0=4.076800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 4 @ t0=4.435200e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 5 @ t0=4.793600e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 6 @ t0=5.003200e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 7 @ t0=5.594000e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 8 @ t0=6.078400e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 9 @ t0=6.436800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 10 @ t0=6.646400e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(0)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(20), Node(evse), CAP(3), reason=smallest backoffSlots
  - Window 11 @ t0=7.153600e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 12 @ t0=8.080000e-04
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 13 @ t0=8.648000e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 14 @ t0=8.796800e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 15 @ t0=9.155200e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 16 @ t0=1.008160e-03
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 17 @ t0=1.044000e-03
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 18 @ t0=1.079840e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 19 @ t0=1.100800e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(8)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(8)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 20 @ t0=1.244160e-03
    - Contenders / 경쟁자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 21 @ t0=1.265120e-03
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 22 @ t0=1.351680e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(0)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(6)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 23 @ t0=1.501120e-03
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 24 @ t0=1.516000e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3), reason=smallest backoffSlots
  - Window 25 @ t0=1.551840e-03
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3), reason=smallest backoffSlots
  - Window 26 @ t0=1.659360e-03
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 27 @ t0=1.665440e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A), reason=smallest backoffSlots
  - Window 28 @ t0=1.716160e-03
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3), reason=smallest backoffSlots
  - Window 29 @ t0=1.859520e-03
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3), reason=smallest backoffSlots
  - Window 30 @ t0=1.895360e-03
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc2/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc3/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc4
- Conditions / 조건: timeout=500s, repeats=10
- Objective / 목적: Validate full sequence PRS0→PRS1→Backoff→TX→RIFS→CIFS→next PRS0 / 전체 MAC 시퀀스 검증
- Method / 방법: Check ES timers order and durations (PRS≈slot, RIFS/CIFS presence) / PRS≈슬롯시간, RIFS/CIFS 존재 확인
- Expected / 기대값: PRS0≈3.584000e-05s, PRS1≈3.584000e-05s, backoffExists=True, rifsExists=True, cifsExists=True; counts>0
- Actual / 실제값: d0=3.584000e-05s, d1=3.584000e-05s, backoffExists=True, rifsExists=True, cifsExists=True, counts(PRS1,TX)=(1561,1561)
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc4/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
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
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(6)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(8)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
  - Window 2 @ t0=3.360000e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 3 @ t0=4.076800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(None)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 4 @ t0=4.435200e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 5 @ t0=4.793600e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 6 @ t0=5.003200e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
  - Window 7 @ t0=5.594000e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(36), Node(ev[3]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 8 @ t0=6.078400e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 9 @ t0=6.436800e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 10 @ t0=6.646400e-04
    - Contenders / 경쟁자:
      - MAC ID(20), Node(evse), CAP(3), backoffSlots(2)
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(0)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(20), Node(evse), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(0)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 11 @ t0=7.153600e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(2)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Winner / 승자: MAC ID(28), Node(ev[1]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(4)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
  - Window 12 @ t0=8.080000e-04
    - Contenders / 경쟁자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(28), Node(ev[1]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 13 @ t0=8.648000e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(None)
    - Winner / 승자: MAC ID(None), Node(None), CAP(N/A)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(None)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 14 @ t0=8.796800e-04
    - Contenders / 경쟁자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
      - MAC ID(32), Node(ev[2]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(32), Node(ev[2]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(0)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(24), Node(ev[0]), CAP(3)
      - MAC ID(36), Node(ev[3]), CAP(3)
  - Window 15 @ t0=9.155200e-04
    - Contenders / 경쟁자:
      - MAC ID(24), Node(ev[0]), CAP(3), backoffSlots(2)
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Winner / 승자: MAC ID(24), Node(ev[0]), CAP(3)
    - Losers / 탈락자:
      - MAC ID(28), Node(ev[1]), CAP(3), backoffSlots(4)
      - MAC ID(36), Node(ev[3]), CAP(3), backoffSlots(2)
    - Non-contenders / 불참자:
      - MAC ID(20), Node(evse), CAP(3)
      - MAC ID(32), Node(ev[2]), CAP(3)

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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
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

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
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
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc5/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc6
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc6 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc6/results/cmdenv.log"...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc6 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc6/results/cmdenv.log"...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc6 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc6/results/cmdenv.log"...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc6 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc6/results/cmdenv.log"...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 5/10 [FAIL] ---
[run.sh] tc6 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
... (truncated) ...
```

## tc7
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 5/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 6/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 7/10 [FAIL] ---
[run.sh] tc7 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer


<!> Error: Configuration option cmdenv-log-level should be specified per object, try **.cmdenv-log-level=
... (truncated) ...
```

## tc8
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc8 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc8 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc8 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc8 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc8/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc9
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 10/10
- Run Statuses / 실행 상태: [P, P, P, P, P, P, P, P, P, P]
- Verdict / 판정: PASS
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [PASS] ---
[run.sh] tc9 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 2/10 [PASS] ---
[run.sh] tc9 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 3/10 [PASS] ---
[run.sh] tc9 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
OK
--- run 4/10 [PASS] ---
[run.sh] tc9 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc9/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc10
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc10 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc10 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc10 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc10 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc10/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc11
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc11 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc11 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc11 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc11 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc11/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## tc12
- Conditions / 조건: timeout=500s, repeats=10
- Runs Passed / 통과 회수: 0/10
- Run Statuses / 실행 상태: [F, F, F, F, F, F, F, F, F, F]
- Verdict / 판정: FAIL
- Runner Output (first lines) / 실행 출력(일부):
```
--- run 1/10 [FAIL] ---
[run.sh] tc12 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 2/10 [FAIL] ---
[run.sh] tc12 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 3/10 [FAIL] ---
[run.sh] tc12 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...

End.
[run.sh] validator start (timeout 500s)
FAIL
--- run 4/10 [FAIL] ---
[run.sh] tc12 sim start (timeout 500s)
OMNeT++ Discrete Event Simulation  (C) 1992-2024 Andras Varga, OpenSim Ltd.
Version: 6.1, build: 241008-f7568267cd, edition: Academic Public License -- NOT FOR COMMERCIAL USE
See the license for distribution terms and warranty disclaimer

Setting up Cmdenv...

Loading NED files from .:  0
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET:  3
Loading NED files from /home/kimdawoon/study/workspace/research/inet_plc/inet/src:  1232
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/common:  1
Loading NED files from /home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12:  0

Preparing for running configuration General, run #0...
Redirecting output to file "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/test/tc12/results/cmdenv.log"...
Recording eventlog to file `results/General-#0.elog'...
... (truncated) ...
```

## Summary / 요약
- Passed / 통과: 6
- Failed / 실패: 6

### Passed List / 통과 TC
- tc1: PRS 지속시간/슬롯 간격 검증
- tc2: PRS 윈도우 경쟁자 vs 승자 일치
- tc3: 백오프 슬롯 평균≈slotTime
- tc4: PRS→Backoff→TX→RIFS→CIFS 시퀀스
- tc5: CAP 순환 동작
- tc9: CA3 vs CA0 우선순위 우위

### Failed List / 실패 TC
- tc6: PRS 패배 시 defer 처리(삭제 금지)
- tc7: Busy 슬롯 경로 동작
- tc8: 충돌→MAC 재시도(BPC++)
- tc10: DC==0 & busy에서 BPC++
- tc11: 충돌 모델 ON 시 재시도 경로
- tc12: Table I 백오프 매핑 증거
