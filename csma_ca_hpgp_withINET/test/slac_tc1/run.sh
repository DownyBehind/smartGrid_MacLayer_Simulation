#!/usr/bin/env bash
set -euo pipefail
TC_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(cd "$TC_DIR/.." && pwd)
source "$BASE_DIR/test_slac.env"
mkdir -p "$TC_DIR/results"
echo "[run.sh] $(basename "$TC_DIR") sim start (timeout ${TEST_TIMEOUT_SECONDS}s)"
set +e
( cd "$TC_DIR"; timeout ${TEST_TIMEOUT_SECONDS}s bash -lc "$OPP_RUN" | tee results/sim.out )
SIM_RC=$?
set -e
if [[ $SIM_RC -eq 124 ]]; then echo "[run.sh] sim TIMEOUT" >&2; fi
if [[ -f "$TC_DIR/validate.py" ]]; then
  echo "[run.sh] validator start (timeout ${TEST_TIMEOUT_SECONDS}s)"
  set +e
  ( cd "$TC_DIR"; timeout ${TEST_TIMEOUT_SECONDS}s python3 validate.py > validate.out 2>&1 )
  VAL_RC=$?
  set -e
else
  echo "[run.sh] validator missing" >&2; VAL_RC=1
fi
if [[ $VAL_RC -eq 0 ]]; then echo "OK"; exit 0; else echo "FAIL"; exit 1; fi

