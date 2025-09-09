# run_demo.py
# ==========
# 역할
# - 기본 설정(config/defaults.json)을 사용해 시뮬레이터를 실행하고 요약을 출력한다.
# - Python 경로에 /mnt/data 를 추가해 로컬에서 패키지를 임포트할 수 있게 한다.

import sys, os, argparse, json
sys.path.append('/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/simulator_simpleAndQuick')  # 패키지 경로 추가

from hpgp_sim.sim import build_and_run  # 실행 엔트리 임포트

if __name__=="__main__":
    ap = argparse.ArgumentParser(description="Run demo with optional sim_time_s override")
    ap.add_argument("--config", default="../config/defaults.json")
    ap.add_argument("--sim-time-s", type=float, default=None, help="override sim_time_s")
    ap.add_argument("--out", default="../out")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    # Load and optionally override sim_time_s without editing source JSON on disk
    cfg_path = args.config
    if args.sim_time_s is not None:
        try:
            with open(cfg_path, "r") as f:
                cfg_obj = json.load(f)
            cfg_obj["sim_time_s"] = float(args.sim_time_s)
            tmp_cfg = os.path.join(os.path.dirname(cfg_path), 
                                   f"tmp_demo_sim{int(float(args.sim_time_s))}.json")
            with open(tmp_cfg, "w") as wf:
                json.dump(cfg_obj, wf, indent=2)
            cfg_path = tmp_cfg
        except Exception:
            pass

    s, out_dir = build_and_run(cfg_path, out_dir=args.out, seed=args.seed)  # 실행
    print("=== SUMMARY ===")
    for k,v in s.items():
        print(f"{k}: {v}")                      # 요약 출력
    print(f"Logs: {out_dir}")                   # 로그 경로
