# sweep_nodes.py
# ===============
# - N=5,10,...,100 스윕
# - background 대신 post_slac.rate_mean_pps 사용
# - 각 실험 out_sweep_N*/ 에 summary.csv / report.md 생성
# - 루트에 out_sweep_summary.csv + report_sweep.md 집계
# - 각 run 진행률 바 출력 + 한 줄 요약
# - PNG: timeout_vs_nodes.png, efficiency_vs_nodes.png, timeout_efficiency_vs_nodes.png

import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from hpgp_sim.sim import build_and_run

# --- headless plotting (PNG) ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _write_sweep_plots(rows, out_dir):
    """
    rows: [ [nodes, thr, eta, util, coll, timeout_ratio, drops, timeouts], ... ]
    Writes 3 PNGs:
      - timeout_vs_nodes.png
      - efficiency_vs_nodes.png
      - timeout_efficiency_vs_nodes.png (overlay)
    """
    if not rows:
        return
    nodes = [r[0] for r in rows]
    timeout_ratio = [r[5] for r in rows]  # session_timeout_ratio
    eta   = [r[2] for r in rows]          # efficiency_eta

    # 1) Timeout vs Nodes
    try:
        plt.figure(figsize=(7, 3.2))
        plt.plot(nodes, timeout_ratio, marker="o", linewidth=2)
        plt.xlabel("Nodes")
        plt.ylabel("SLAC Timeout Ratio")
        plt.ylim(0, 1.0)
        plt.title("SLAC Timeout Ratio vs Nodes")
        plt.grid(True, linewidth=0.4, alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "timeout_vs_nodes.png"), dpi=120)
        plt.close()
    except Exception as e:
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
            f.write(f"timeout_vs_nodes plot error: {e}\n")

    # 2) Efficiency vs nodes
    try:
        plt.figure(figsize=(7, 3.2))
        plt.plot(nodes, eta, marker="o", linewidth=2)
        plt.xlabel("Nodes")
        plt.ylabel("Efficiency (eta)")
        plt.ylim(0, 1.0)
        plt.title("Efficiency vs Nodes")
        plt.grid(True, linewidth=0.4, alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "efficiency_vs_nodes.png"), dpi=120)
        plt.close()
    except Exception as e:
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
            f.write(f"efficiency_vs_nodes plot error: {e}\n")

    # 3) Overlay: Timeout + Efficiency
    try:
        plt.figure(figsize=(7.6, 3.2))
        plt.plot(nodes, timeout_ratio, marker="o", linewidth=2, label="SLAC Timeout Ratio")
        plt.plot(nodes, eta, marker="s", linewidth=2, label="Efficiency (eta)")
        plt.xlabel("Nodes")
        plt.ylabel("Ratio")
        plt.ylim(0, 1.0)
        plt.title("SLAC Timeout & Efficiency vs Nodes")
        plt.grid(True, linewidth=0.4, alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "timeout_efficiency_vs_nodes.png"), dpi=120)
        plt.close()
    except Exception as e:
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
            f.write(f"timeout_efficiency_vs_nodes plot error: {e}\n")


def run_sweep(base_cfg_path, out_csv_path, nodes_list):
    with open(base_cfg_path, "r") as f:
        base = json.load(f)

    traffic = base.get("traffic", {})
    base_rate = (
        traffic.get("post_slac", {}).get("rate_mean_pps",
            traffic.get("background", {}).get("full_load_rate_pps",
                traffic.get("background", {}).get("rate_pps", 50)))
    )

    rows = []
    total = len(nodes_list)
    for idx, n in enumerate(nodes_list, 1):
        with open(base_cfg_path, "r") as f:
            cfg = json.load(f)

        cfg["topology"] = "shared_bus"
        cfg["nodes"] = n

        cfg.setdefault("traffic", {})
        cfg["traffic"].pop("background", None)
        ps = cfg["traffic"].setdefault("post_slac", {})
        ps.setdefault("bytes_min", 300)
        ps.setdefault("bytes_max", 1500)
        ps.setdefault("start_delay_us", 0)
        ps["rate_mean_pps"] = base_rate  # per-node 평균 pps

        tmp_cfg_path = os.path.join(ROOT, "config", f"tmp_N{n}.json")
        os.makedirs(os.path.dirname(tmp_cfg_path), exist_ok=True)
        with open(tmp_cfg_path, "w") as wf:
            json.dump(cfg, wf, indent=2)

        out_dir = os.path.join(ROOT, f"out_sweep_N{n}")
        label = f"N={n} ({idx}/{total})"
        s, _ = build_and_run(tmp_cfg_path, out_dir=out_dir, seed=42+n,
                             progress=True, progress_label=label)

        print(f"[{idx}/{total}] N={n}  thr={s.get('throughput_mbps',0.0):.3f} Mbps  "
              f"eta={s.get('efficiency_eta',0.0):.3f}  util={s.get('utilization',0.0):.3f}  "
              f"coll={s.get('collision_ratio',0.0):.3f}  "
              f"timeouts={s.get('session_timeouts',0)}/{s.get('session_total',0)} "
              f"({s.get('session_timeout_ratio',0.0):.3f})  "
              f"drops={s.get('drops',0)}")

        rows.append([
            n,
            s.get("throughput_mbps", 0.0),
            s.get("efficiency_eta", 0.0),
            s.get("utilization", 0.0),
            s.get("collision_ratio", 0.0),
            s.get("session_timeout_ratio", 0.0),
            s.get("drops", 0),
            s.get("timeouts", 0),
        ])

    # 집계 CSV (노드별)
    with open(out_csv_path, "w") as f:
        f.write("nodes,throughput_mbps,efficiency_eta,utilization,collision_ratio,session_timeout_ratio,drops,timeouts\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")

    # PNG 그래프(노드 축)
    out_dir = os.path.dirname(out_csv_path)
    _write_sweep_plots(rows, out_dir)

    # 집계 MD
    md_path = os.path.join(out_dir, "report_sweep.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Sweep Report\n\n")
        f.write("| nodes | thr(Mbps) | eta | util | coll | TimeoutRatio | drops | timeouts | verdict |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|:---|\n")
        for (n, thr, eta, util, coll, to_ratio, drops, timeouts) in rows:
            verdict = "OK"
            if not (0.0 <= util <= 1.05): verdict = "FAIL"
            elif coll > 0.9: verdict = "FAIL"
            elif coll < 0.02: verdict = "WARN"
            if to_ratio > 0.2: verdict = "WARN" if verdict == "OK" else verdict
            f.write(f"| {n} | {thr:.3f} | {eta:.3f} | {util:.3f} | {coll:.3f} | {to_ratio:.3f} | {drops} | {timeouts} | {verdict} |\n")

        f.write("\n## Plots (Nodes → Ratio)\n\n")
        f.write("![SLAC Timeout Ratio vs Nodes](timeout_vs_nodes.png)\n\n")
        f.write("![Efficiency vs Nodes](efficiency_vs_nodes.png)\n\n")
        f.write("![SLAC Timeout & Efficiency vs Nodes](timeout_efficiency_vs_nodes.png)\n")

    return out_csv_path, md_path

if __name__ == "__main__":
    base_cfg = os.path.join(ROOT, "config", "defaults.json")
    out_csv  = os.path.join(ROOT, "out_sweep_summary.csv")
    nodes    = list(range(5, 101, 5))
    csv_path, md_path = run_sweep(base_cfg, out_csv, nodes)
    print("Wrote:", csv_path)
    print("Wrote:", md_path)
