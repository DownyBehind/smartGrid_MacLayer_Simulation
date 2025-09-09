# sweep_nodes.py
# ===============
# - N=5,10,...,100 스윕
# - 각 실험 out_sweep_N*/ 에 summary.csv / report.md / dc_entry_times.csv / dc_cycles.csv / dc_timeline.png 생성
# - 루트에 out_sweep_summary.csv + report_sweep.md + dctiming_vs_nodes.png 생성
# - 각 run 진행률 바 출력 + 한 줄 요약

import os, sys, json, argparse
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from hpgp_sim.sim import build_and_run

# Headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _write_overall_plots(rows, out_dir):
    """
    rows: [ [nodes, thr, eta, util, coll, drops, sess_ok, sess_to], ... ]
    """
    if not rows: return
    nodes = [r[0] for r in rows]
    eta   = [r[2] for r in rows]
    try:
        plt.figure(figsize=(7,3.2))
        plt.plot(nodes, eta, marker="o", linewidth=2)
        plt.xlabel("Nodes"); plt.ylabel("Efficiency (eta)"); plt.ylim(0,1.0)
        plt.title("Efficiency vs Nodes"); plt.grid(True, lw=0.4, alpha=0.5)
        plt.tight_layout(); plt.savefig(os.path.join(out_dir,"efficiency_vs_nodes.png"), dpi=120); plt.close()
    except Exception as e:
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f: f.write(f"efficiency_vs_nodes plot error: {e}\n")

def run_sweep(base_cfg_path, out_csv_path, nodes_list, sim_time_s: float | None = None):
    with open(base_cfg_path, "r") as f:
        base = json.load(f)

    rows = []
    total = len(nodes_list)
    for idx, n in enumerate(nodes_list, 1):
        with open(base_cfg_path, "r") as f:
            cfg = json.load(f)

        cfg["topology"] = "shared_bus"
        cfg["nodes"] = n
        if sim_time_s is not None:
            cfg["sim_time_s"] = float(sim_time_s)

        # DC 루프(100ms) 켜기
        cfg.setdefault("traffic", {})
        cfg["traffic"].setdefault("dc_loop", {"enabled": True, "period_ms":100, "deadline_ms":100, "rsp_delay_us":1500, "rsp_jitter_us":0})

        # tmp cfg 저장
        tmp_cfg_path = os.path.join(ROOT, "config", f"tmp_N{n}.json")
        os.makedirs(os.path.dirname(tmp_cfg_path), exist_ok=True)
        with open(tmp_cfg_path, "w") as wf: json.dump(cfg, wf, indent=2)

        out_dir = os.path.join(ROOT, f"out_sweep_N{n}")
        label = f"N={n} ({idx}/{total})"
        s, _ = build_and_run(tmp_cfg_path, out_dir=out_dir, seed=42+n, progress=True, progress_label=label)

        print(f"[{idx}/{total}] N={n} thr={s.get('throughput_mbps',0.0):.3f} Mbps  "
              f"eta={s.get('efficiency_eta',0.0):.3f} util={s.get('utilization',0.0):.3f} "
              f"coll={s.get('collision_ratio',0.0):.3f} drops={s.get('drops',0)} "
              f"sess_ok={s.get('session_success',0)}/{s.get('session_total',0)} to={s.get('session_timeouts',0)}")

        rows.append([n, s.get('throughput_mbps',0.0), s.get('efficiency_eta',0.0),
                     s.get('utilization',0.0), s.get('collision_ratio',0.0),
                     s.get('drops',0), s.get('session_success',0), s.get('session_timeouts',0)])

    # 집계 CSV
    with open(out_csv_path, "w") as f:
        f.write("nodes,throughput_mbps,efficiency_eta,utilization,collision_ratio,drops,session_success,session_timeouts\n")
        for r in rows: f.write(",".join(str(x) for x in r) + "\n")

    # 집계 PNG
    out_dir = os.path.dirname(out_csv_path)
    _write_overall_plots(rows, out_dir)

    # 집계 MD
    md_path = os.path.join(out_dir, "report_sweep.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Sweep Report\n\n")
        f.write("| nodes | thr(Mbps) | eta | util | coll | drops | sess_ok | sess_to |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for (n, thr, eta, util, coll, drops, s_ok, s_to) in rows:
            f.write(f"| {n} | {thr:.3f} | {eta:.3f} | {util:.3f} | {coll:.3f} | {drops} | {s_ok} | {s_to} |\n")

    return out_csv_path, md_path

def _parse_args():
    p = argparse.ArgumentParser(description="Sweep N (nodes) and summarize results")
    p.add_argument("--config", default=os.path.join(ROOT, "config", "defaults.json"))
    p.add_argument("--out-csv", default=os.path.join(ROOT, "out_sweep_summary.csv"))
    p.add_argument("--min-n", type=int, default=5)
    p.add_argument("--max-n", type=int, default=100)
    p.add_argument("--step", type=int, default=5)
    p.add_argument("--sim-time-s", type=float, default=None, help="override sim_time_s for all runs")
    return p.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    nodes = list(range(max(1, args.min_n), max(args.min_n, args.max_n) + 1, max(1, args.step)))
    csv_path, md_path = run_sweep(args.config, args.out_csv, nodes, sim_time_s=args.sim_time_s)
    print("Wrote:", csv_path)
    print("Wrote:", md_path)
