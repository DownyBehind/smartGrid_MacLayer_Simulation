#!/usr/bin/env bash
set -euo pipefail
RBASE=/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET/research/hpgp_mac_protocol
python3 "$RBASE/scripts/run_experiments.py" >/dev/null || true
LAST=$(ls -1 "$RBASE/results/raw" | tail -n 1)
echo RUN=$LAST
echo "[ELOG DC_RESPONSE]"
grep -n "DC_RESPONSE" "$RBASE/results/raw/$LAST/results/General-#0.elog" | head -n 20 || true
echo "[SCA EV/EVSE DC]"
grep -E "(TestBus\.ev\[[0-9]+\]\.slac|TestBus\.evse\.slac) (dcReqSent|dcRspRecv|dcLatencyAvg\(s\))" "$RBASE/results/raw/$LAST/results/General-#0.sca" || true
echo "[SUMMARY]"
tail -n 5 "$RBASE/results/summary.csv" || true
