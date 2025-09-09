#!/bin/bash
# inet_plc 환경 설정 스크립트
# 사용법: source setup_inet_plc_env.sh

export INET_DIR="/home/kimdawoon/study/workspace/research/inet_plc/inet"
export TIMESLOT_DIR="/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot"

# 라이브러리 경로 설정
export LD_LIBRARY_PATH="${INET_DIR}/out/clang-release/src:${TIMESLOT_DIR}/out/clang-release:${LD_LIBRARY_PATH}"

# NED 경로 설정
export NED_PATH="${INET_DIR}/src:${TIMESLOT_DIR}/src"

echo "✓ inet_plc 환경 설정 완료"
echo "  INET_DIR: $INET_DIR"
echo "  TIMESLOT_DIR: $TIMESLOT_DIR"
echo "  LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "  NED_PATH: $NED_PATH"
