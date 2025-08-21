# run_demo.py
# ==========
# 역할
# - 기본 설정(config/defaults.json)을 사용해 시뮬레이터를 실행하고 요약을 출력한다.
# - Python 경로에 /mnt/data 를 추가해 로컬에서 패키지를 임포트할 수 있게 한다.

import sys
sys.path.append('/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/simulator_simpleAndQuick')  # 패키지 경로 추가

from hpgp_sim.sim import build_and_run  # 실행 엔트리 임포트

if __name__=="__main__":
    cfg = "../config/defaults.json"       # 설정 파일 경로
    s, out_dir = build_and_run(cfg, out_dir="../out", seed=42)  # 실행
    print("=== SUMMARY ===")
    for k,v in s.items():
        print(f"{k}: {v}")                      # 요약 출력
    print(f"Logs: {out_dir}")                   # 로그 경로
