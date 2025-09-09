# Sweep Nodes 실험 리포트 (상세 분석)

본 문서는 `simulator_simpleAndQuick/scripts/sweep_nodes.py`로 수행한 N=5..100(5 간격) 스윕 결과를 해석하고, 메트릭 정의와 관찰사항, 주의점, 개선 방안을 요약합니다. 간단 표와 그래프는 기존 `report_sweep.md`, `efficiency_vs_nodes.png`를 참조합니다.

- 기본 요약 표: `simulator_simpleAndQuick/report_sweep.md`
- 전체 요약 CSV: `simulator_simpleAndQuick/out_sweep_summary.csv`
- 효율-노드수 그래프: `simulator_simpleAndQuick/efficiency_vs_nodes.png`

---

## 실험 개요
- 스크립트: `simulator_simpleAndQuick/scripts/sweep_nodes.py`
- 노드 수: 5, 10, …, 100
- 베이스 설정: `simulator_simpleAndQuick/config/defaults.json`
  - 토폴로지: shared_bus
  - 시뮬레이션 시간: 10 s
  - PHY: 14 Mbps, 슬롯(σ) 36 µs
  - Beacon: 100 ms 주기/2 ms 점유, PRS: 2 심볼 × 36 µs
  - 백오프: CAP별 `cw_table`, `retry_limit=7`, `dc_init_per_bpc` 사용
  - 채널: 배경상태 전환 확률과 PER(good/bad) 포함
- 워크로드 흐름:
  1) 모든 EV가 SLAC(CAP3) 절차 시작
  2) SLAC 성공 시에만 EV가 DC 루프(100 ms 주기) 시작(EVSE 응답)

## 메트릭 정의(핵심)
- throughput_mbps: 성공 전송된 전체 비트 / 시뮬레이션 시간
- efficiency_eta: t_success / (T - t_control)
  - t_control = BEACON + PRS 점유시간 합
- utilization: (t_success + t_collision) / T
- collision_ratio: t_collision / (t_success + t_collision)
- drops: 재시도 한계 초과로 드롭된 프레임 수
- 세션 집계: SLAC 로그 기반
  - session_success: ok=1 && timeout=0
  - session_timeouts: 세션 지속시간 > TT_session_s(기본 60s)

## 결과 요약(추세)
- 처리량(throughput): N=10에서 약 1.30 Mbps로 최대, 이후 전반적 하락(N≥50 구간 0.26~0.44 Mbps)
- 효율(efficiency_eta): N=10에서 ~0.098 → N 증가 시 0.02대까지 하락
- 충돌(collison_ratio): N=5 ~0.51 → N=40 ~0.97 → N≥60 ~0.99 부근
- utilization: N 증가와 함께 1을 초과(최대 ~1.93) — 해석 주의 필요(아래 참조)
- 드롭(drops): N 증가에 따라 단조 증가(혼잡으로 retry_limit 초과)
- SLAC 세션: 전 구간에서 session_success=0, session_timeouts=0 (10초 내 SLAC 완료 실패, 60초 타임아웃 미도달)

## 시각화
- 효율 vs 노드 수: `simulator_simpleAndQuick/efficiency_vs_nodes.png`
- 각 N별 상세: `simulator_simpleAndQuick/out_sweep_N*/`의 `report.md`, `efficiency_over_time.png` 등

## 주의/비정상 징후 해석
- utilization > 1의 원인:
  - 충돌 처리 경로에서 공유 충돌 airtime을 한 번 기록하는 것 외에, 각 실패 전송에 대해 개별적으로도 t_collision이 누적되어 이중 계상이 발생합니다.
  - 이 때문에 utilization이 물리적 점유율 개념을 벗어나 1을 초과할 수 있습니다. 본 스윕에서는 “충돌 강도 지표” 정도로만 참고하세요.

## DC 관련 산출물이 비어있는 이유
- App15118 로직상 DC 루프는 “SLAC 성공” 후에만 시작됩니다.
- 본 스윕에서는 충돌/혼잡으로 10초 내 SLAC 필수 응답 3종(SLAC_PARM_CNF, ATTEN_CHAR_IND, SLAC_MATCH_CNF)의 실제 성공 전파가 충족되지 못해 DC가 시작되지 않았습니다.
- 따라서 `out_sweep_N*/dc_entry_times.csv`, `dc_cycles.csv`는 헤더만 있고 데이터가 없습니다.

## 개선 제안 / 다음 단계
- SLAC 성공률 개선 및 DC 관찰을 위해:
  - 시뮬레이션 시간(sim_time_s) ≥ 60 s로 확대하여 SLAC 완료 기회 확보
  - SLAC 응답 지연(delay_evse_rsp_us) 단축, PRS/Beacon 점유 축소로 제어 오버헤드 완화
  - 채널 악화도 완화(per_bad↓) 또는 PHY 속도(phy_bps) 상향, 슬롯(sigma_us) 조정
  - 동시 시작 오프셋(slac_peer_offset_us) 확대로 초기 경합 완화
- utilization 산식 보정(선택):
  - 충돌 airtime을 매체 레벨에서 한 번만 계상하고, 개별 실패 on_tx에서는 제외
  - 또는 utilization을 매체 점유 기반 지표로 재정의
- 추가 분석:
  - 각 N별 `tx_log.csv`, `debug.csv`, `sessions.csv`로 SLAC 지연/실패 원인 세부 파악

## 참고 파일
- 스크립트: `simulator_simpleAndQuick/scripts/sweep_nodes.py`
- 요약: `simulator_simpleAndQuick/out_sweep_summary.csv`, `simulator_simpleAndQuick/report_sweep.md`
- 메트릭: `simulator_simpleAndQuick/hpgp_sim/metrics.py`
- 시뮬 흐름: `simulator_simpleAndQuick/hpgp_sim/sim.py`, `simulator_simpleAndQuick/hpgp_sim/app_15118.py`, `simulator_simpleAndQuick/hpgp_sim/mac_hpgp.py`
