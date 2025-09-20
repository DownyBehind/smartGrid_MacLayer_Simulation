#!/usr/bin/env bash
set -euo pipefail
CBASE=/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_hpgp_withINET
INET=/home/kimdawoon/study/workspace/research/inet_plc/inet
NED=".:$CBASE:$INET/src:$CBASE/test/common"
LIB1="$CBASE/out/clang-release/libcsma_ca_hpgp_withINET.so"
LIB2="$INET/out/clang-release/src/libINET.so"
export LD_LIBRARY_PATH="$CBASE/out/clang-release:$INET/out/clang-release/src:$LD_LIBRARY_PATH"
mkdir -p "$CBASE/research/reseach/results"
cd "$CBASE/research/reseach"
opp_run -u Cmdenv -n "$NED" -l "$LIB1" -l "$LIB2" -f omnetpp.ini > sim.out 2>&1 || true
