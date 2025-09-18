#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
BIN_SIM = ROOT / "out" / "clang-release" / "csma_ca_hpgp"

SCENARIOS = {
    "WC_A": {
        "config": "Baseline_WC_A_Sequential_SLAC",
        "ini": ROOT / "test" / "baseline_wc_a" / "omnetpp.ini",
    },
    "WC_B": {
        "config": "Baseline_WC_B_Simultaneous_SLAC",
        "ini": ROOT / "test" / "baseline_wc_b" / "omnetpp.ini",
    },
}

RESULTS_DIR = ROOT / "results"

def run_once(scenario_key: str, num_nodes: int, run_index: int, sim_time: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clean shared results logs before run
    for fn in ["dc_jobs.log", "dc_misses.log", "mac_tx.log", "medium_windows.log", "slac_attempt.log"]:
        p = RESULTS_DIR / fn
        if p.exists():
            p.unlink()

    sc = SCENARIOS[scenario_key]
    base_ini = sc["ini"]
    cfg = sc["config"]

    # Create overlay ini for numNodes and dcLoopEnable
    overlay = (
        "[General]\n"
        f"sim-time-limit = {sim_time}\n"
        f"*.numNodes = {num_nodes}\n"
        # DC loop: EV only (node[0] assumed EVSE)
        "*.node[*].dcLoopEnabled = true\n"
        "*.node[0].dcLoopEnabled = false\n"
    )
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ini") as tf:
        tf.write(overlay)
        overlay_path = Path(tf.name)

    # Run opp_run selecting the repetition index
    cmd = [
        str(BIN_SIM), "-u", "Cmdenv",
        "-n", ".",
        "-f", str(base_ini),
        "-f", str(overlay_path),
        "-c", cfg,
        "-r", str(run_index),
        "--sim-time-limit", sim_time,
    ]
    env = os.environ.copy()
    # Ensure OMNeT++ libs are in path
    omnet_lib = "/home/kimdawoon/study/workspace/research/omnetpp-6.1/lib"
    env["LD_LIBRARY_PATH"] = omnet_lib + ":" + env.get("LD_LIBRARY_PATH", "")

    try:
        subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    finally:
        try:
            overlay_path.unlink()
        except Exception:
            pass

    # Move produced logs into out_dir
    for fn in ["dc_jobs.log", "dc_misses.log", "mac_tx.log", "medium_windows.log", "slac_attempt.log"]:
        src = RESULTS_DIR / fn
        if src.exists():
            shutil.move(str(src), str(out_dir / fn))


def summarize_run_dir(run_dir: Path):
    out = {}
    jobs = run_dir / "dc_jobs.log"
    misses = run_dir / "dc_misses.log"
    windows = run_dir / "medium_windows.log"
    if jobs.exists():
        cols=["node","job","rel","winS","winE","ddl","state","seq","req","res","enq_req","txS","txE","enq_rsp","rxS","rxE","event"]
        df = pd.read_csv(jobs, header=None, names=cols)
        ok = df[df["event"]=="DC_RES_RX_OK"].copy()
        if not ok.empty:
            ok["rtt_ms"] = (ok["rxE"]-ok["txE"]) * 1000.0
            out["ok_count"] = len(ok)
            out["rtt_mean_ms"] = float(ok["rtt_ms"].mean())
            out["rtt_p95_ms"] = float(ok["rtt_ms"].quantile(0.95))
            out["rtt_p99_ms"] = float(ok["rtt_ms"].quantile(0.99))
        else:
            out["ok_count"] = 0
            out["rtt_mean_ms"] = out["rtt_p95_ms"] = out["rtt_p99_ms"] = float("nan")
    if misses.exists():
        mcols=["node","job","rel","winS","winE","ddl","state","miss","req","tardi","enq_req","txS","txE","enq_rsp","rxS","rxE"]
        md = pd.read_csv(misses, header=None, names=mcols)
        cnt = md.groupby("miss").size()
        out["M0"] = int(cnt.get(0, 0))
        out["M1"] = int(cnt.get(1, 0))
        out["M2"] = int(cnt.get(2, 0))
        out["M3"] = int(cnt.get(3, 0))
    if windows.exists():
        w = pd.read_csv(windows, header=None, names=["type","start","end"])  # 1=data,2=beacon,3=collision
        w["dur_ms"] = (w["end"]-w["start"]) * 1000.0
        out["Vmax_ms"] = float(w["dur_ms"].max()) if not w.empty else 0.0
        bytype = w.groupby("type").size()
        out["count_data"] = int(bytype.get(1, 0))
        out["count_beacon"] = int(bytype.get(2, 0))
        out["count_collision"] = int(bytype.get(3, 0))
    return out


def aggregate_condition(cond_dir: Path):
    rows = []
    for run_dir in sorted(cond_dir.glob("run_*")):
        rows.append(summarize_run_dir(run_dir))
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Aggregate by mean for RTT, sum for counts
    summary = pd.DataFrame({
        "runs": [len(df)],
        "ok_count_sum": [int(df["ok_count"].sum())],
        "M0_sum": [int(df["M0"].sum())],
        "M1_sum": [int(df["M1"].sum())],
        "M2_sum": [int(df["M2"].sum())],
        "M3_sum": [int(df["M3"].sum())],
        "rtt_mean_ms": [float(df["rtt_mean_ms"].mean(skipna=True))],
        "rtt_p95_ms": [float(df["rtt_p95_ms"].mean(skipna=True))],
        "rtt_p99_ms": [float(df["rtt_p99_ms"].mean(skipna=True))],
        "Vmax_ms_mean": [float(df["Vmax_ms"].mean(skipna=True))],
        "data_cnt_mean": [float(df["count_data"].mean(skipna=True))],
        "beacon_cnt_mean": [float(df["count_beacon"].mean(skipna=True))],
        "collision_cnt_mean": [float(df["count_collision"].mean(skipna=True))],
    })
    return summary, df


def plot_condition(cond_dir: Path, df_runs: pd.DataFrame, summary: pd.DataFrame):
    cond_dir.mkdir(parents=True, exist_ok=True)
    # DMR (window-based) = (M0+M1+M2+M3)/((M0+M1+M2+M3)+ok_count) approximated per sum
    misses = summary[["M0_sum","M1_sum","M2_sum","M3_sum"]].sum(axis=1).iloc[0]
    oks = summary["ok_count_sum"].iloc[0]
    dmr = misses / (misses + oks) if (misses + oks) > 0 else 0.0
    with open(cond_dir / "aggregate_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["runs","ok_count","M0","M1","M2","M3","DMR","rtt_mean_ms","rtt_p95_ms","rtt_p99_ms","Vmax_ms_mean"]) 
        w.writerow([int(summary["runs"].iloc[0]), int(oks), int(summary["M0_sum"].iloc[0]), int(summary["M1_sum"].iloc[0]), int(summary["M2_sum"].iloc[0]), int(summary["M3_sum"].iloc[0]), f"{dmr:.6f}", f"{summary['rtt_mean_ms'].iloc[0]:.3f}", f"{summary['rtt_p95_ms'].iloc[0]:.3f}", f"{summary['rtt_p99_ms'].iloc[0]:.3f}", f"{summary['Vmax_ms_mean'].iloc[0]:.3f}"])

    # Simple bar for miss composition
    plt.figure(figsize=(5,3))
    parts = [summary["M0_sum"].iloc[0], summary["M1_sum"].iloc[0], summary["M2_sum"].iloc[0], summary["M3_sum"].iloc[0]]
    plt.bar(["M0","M1","M2","M3"], parts)
    plt.title("Miss composition")
    plt.tight_layout()
    plt.savefig(cond_dir / "miss_composition.png")
    plt.close()

    # RTT histogram (ok)
    if not df_runs.empty and "rtt_mean_ms" in df_runs:
        # Note: we didn't store per-packet RTTs to avoid huge memory; we use run-level means.
        plt.figure(figsize=(5,3))
        df_runs["rtt_mean_ms"].dropna().plot(kind="hist", bins=20)
        plt.title("Per-run RTT mean (ms)")
        plt.tight_layout()
        plt.savefig(cond_dir / "rtt_mean_hist.png")
        plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Dry run: 1 repetition each, 10s sim-time")
    parser.add_argument("--outdir", type=str, default="", help="Explicit output root directory (optional)")
    args = parser.parse_args()

    if args.outdir:
        root = Path(args.outdir)
    else:
        now = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        root = ROOT / f"experiments_{now}"
    root.mkdir(parents=True, exist_ok=True)

    Ns = [5,10,20]
    rep_count = 1 if args.dry else 50
    sim_time = "10s" if args.dry else "120s"

    overall_rows = []

    for scen in ("WC_A","WC_B"):
        for N in Ns:
            cond_dir = root / f"{scen}_N{N}"
            cond_dir.mkdir(parents=True, exist_ok=True)
            # Run repetitions
            for r in range(rep_count):
                run_dir = cond_dir / f"run_{r:02d}"
                run_once(scen, N, r, sim_time, run_dir)
            # Aggregate
            summary, df_runs = aggregate_condition(cond_dir)
            if isinstance(summary, pd.DataFrame):
                plot_condition(cond_dir, df_runs, summary)
                # Append to overall
                misses = int(summary[["M0_sum","M1_sum","M2_sum","M3_sum"]].sum(axis=1).iloc[0])
                oks = int(summary["ok_count_sum"].iloc[0])
                dmr = misses / (misses + oks) if (misses + oks) > 0 else 0.0
                overall_rows.append({
                    "scenario": scen,
                    "N": N,
                    "runs": int(summary["runs"].iloc[0]),
                    "DMR": dmr,
                    "ok_count": oks,
                    "M0": int(summary["M0_sum"].iloc[0]),
                    "M1": int(summary["M1_sum"].iloc[0]),
                    "M2": int(summary["M2_sum"].iloc[0]),
                    "M3": int(summary["M3_sum"].iloc[0]),
                    "rtt_mean_ms": float(summary["rtt_mean_ms"].iloc[0]),
                    "rtt_p95_ms": float(summary["rtt_p95_ms"].iloc[0]),
                    "rtt_p99_ms": float(summary["rtt_p99_ms"].iloc[0]),
                    "Vmax_ms_mean": float(summary["Vmax_ms"].iloc[0]) if "Vmax_ms" in summary else float("nan"),
                })

    # Save overall CSV and a couple of comparison plots
    overall = pd.DataFrame(overall_rows)
    overall_csv = root / "overall_summary.csv"
    overall.to_csv(overall_csv, index=False)

    # Plot DMR vs N per scenario
    plt.figure(figsize=(5,3))
    for scen in overall["scenario"].unique():
        sub = overall[overall["scenario"]==scen]
        plt.plot(sub["N"], sub["DMR"], marker='o', label=scen)
    plt.xlabel("N")
    plt.ylabel("DMR")
    plt.legend()
    plt.tight_layout()
    plt.savefig(root / "dmr_vs_N.png")
    plt.close()

    # Plot p99 RTT vs N per scenario
    plt.figure(figsize=(5,3))
    for scen in overall["scenario"].unique():
        sub = overall[overall["scenario"]==scen]
        plt.plot(sub["N"], sub["rtt_p99_ms"], marker='o', label=scen)
    plt.xlabel("N")
    plt.ylabel("p99 RTT (ms)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(root / "p99_rtt_vs_N.png")
    plt.close()

    print(f"Done. Results aggregated under: {root}")

if __name__ == "__main__":
    main()


