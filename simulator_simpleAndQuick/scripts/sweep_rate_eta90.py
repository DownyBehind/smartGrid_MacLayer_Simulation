# sweep_rate_eta90.py
# - 환경/프로토콜(config)은 그대로 두고 post_slac.rate_mean_pps만 스윕
# - N=5 기본, 효율(eta)≈target에 맞는 pps 추천
# - 범위/스텝/목표/노드 수/로그스페이스를 CLI로 지정 가능

import os, sys, json, math, argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from hpgp_sim.sim import build_and_run

# headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def parse_args():
    p = argparse.ArgumentParser(description="Sweep post_slac.rate_mean_pps to hit target efficiency")
    p.add_argument("--config", default=os.path.join(ROOT, "config", "defaults.json"))
    p.add_argument("--nodes", type=int, default=5, help="number of nodes (default: 5)")
    p.add_argument("--target-eta", type=float, default=0.90, help="target efficiency eta (0..1)")
    # 후보 생성 방식
    p.add_argument("--pps", type=str, help="comma-separated list, e.g., 2,4,6,8,10,20,50,100,150,200")
    p.add_argument("--min-pps", type=int, default=2)
    p.add_argument("--max-pps", type=int, default=200, help="increase this beyond 50 to explore higher load")
    p.add_argument("--step", type=int, default=2)
    p.add_argument("--logspace", action="store_true", help="use log-spaced candidates between min/max")
    p.add_argument("--logpoints", type=int, default=15, help="number of log-spaced points when --logspace")
    p.add_argument("--out-prefix", default="out_rate", help="output folder prefix")
    return p.parse_args()

def build_candidates(args):
    # 1) 명시 리스트 우선
    if args.pps:
        vals = []
        for tok in args.pps.split(","):
            tok = tok.strip()
            if not tok:
                continue
            try:
                v = int(tok)
                if v > 0:
                    vals.append(v)
            except:
                pass
        vals = sorted(set(vals))
        if vals:
            return vals

    # 2) 로그스페이스
    min_pps = max(1, args.min_pps)
    max_pps = max(min_pps, args.max_pps)
    if args.logspace:
        n = max(2, args.logpoints)
        a = math.log(min_pps)
        b = math.log(max_pps)
        xs = [int(round(math.exp(a + (b - a) * i / (n - 1)))) for i in range(n)]
        xs = sorted(set([x for x in xs if x > 0]))
        return xs

    # 3) 선형 범위
    step = max(1, args.step)
    return list(range(min_pps, max_pps + 1, step))

def run_once(base_cfg_path, nodes, pps, out_dir, label):
    with open(base_cfg_path, "r") as f:
        cfg = json.load(f)

    cfg["topology"] = cfg.get("topology", "shared_bus")
    cfg["nodes"] = nodes

    traffic = cfg.setdefault("traffic", {})
    ps = traffic.setdefault("post_slac", {})
    if "bytes_min" not in ps: ps["bytes_min"] = 300
    if "bytes_max" not in ps: ps["bytes_max"] = 1500
    if "start_delay_us" not in ps: ps["start_delay_us"] = 0
    ps["rate_mean_pps"] = int(pps)

    tmp_cfg = os.path.join(ROOT, "config", f"tmp_rate_N{nodes}_pps{pps}.json")
    os.makedirs(os.path.dirname(tmp_cfg), exist_ok=True)
    with open(tmp_cfg, "w") as wf:
        json.dump(cfg, wf, indent=2)

    s, _ = build_and_run(tmp_cfg, out_dir=out_dir, seed=100+pps, progress=True, progress_label=label)
    return s

def main():
    args = parse_args()
    candidates = build_candidates(args)
    total = len(candidates)
    if total == 0:
        print("No candidate pps specified.", file=sys.stderr)
        sys.exit(1)

    rows = []  # (pps, eta, dmr, util, coll, thr)
    for i, pps in enumerate(candidates, 1):
        out_dir = os.path.join(ROOT, f"{args.out_prefix}_N{args.nodes}_pps{pps}")
        label = f"pps={pps} ({i}/{total})"
        s = run_once(args.config, args.nodes, pps, out_dir, label)
        eta  = s.get("efficiency_eta", 0.0)
        dmr  = s.get("deadline_miss_ratio", 0.0)
        util = s.get("utilization", 0.0)
        coll = s.get("collision_ratio", 0.0)
        thr  = s.get("throughput_mbps", 0.0)
        print(f"pps={pps:>4}  eta={eta:.3f}  DMR={dmr:.3f}  util={util:.3f}  coll={coll:.3f}  thr={thr:.3f} Mbps")
        rows.append((pps, eta, dmr, util, coll, thr))

    TARGET_ETA = max(0.0, min(1.0, args.target_eta))
    feasible = [r for r in rows if r[1] >= TARGET_ETA]
    if feasible:
        best = max(feasible, key=lambda r: r[0])  # 가장 높은 pps 중 target 충족
        note = "picked highest pps meeting target eta"
    else:
        best = min(rows, key=lambda r: abs(r[1] - TARGET_ETA))
        note = "target not reached; picked closest eta"

    best_pps, best_eta, best_dmr, best_util, best_coll, best_thr = best
    mean_gap_s = 1.0 / best_pps if best_pps > 0 else float("inf")

    # 플롯 (루트)
    pps_list = [r[0] for r in rows]
    eta_list = [r[1] for r in rows]
    dmr_list = [r[2] for r in rows]

    try:
        plt.figure(figsize=(7.6, 3.2))
        plt.plot(pps_list, eta_list, marker="o", linewidth=2)
        plt.axhline(TARGET_ETA, linestyle="--", linewidth=1)
        plt.xlabel("rate_mean_pps (per node)")
        plt.ylabel("Efficiency (eta)")
        plt.ylim(0, 1.0)
        plt.title(f"Efficiency vs rate_mean_pps (N={args.nodes})")
        plt.grid(True, linewidth=0.4, alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(ROOT, "eta_vs_rate.png"), dpi=120)
        plt.close()
    except Exception as e:
        with open(os.path.join(ROOT, "plot_error.log"), "a") as f:
            f.write(f"eta_vs_rate plot error: {e}\n")

    try:
        plt.figure(figsize=(7.6, 3.2))
        plt.plot(pps_list, dmr_list, marker="o", linewidth=2)
        plt.xlabel("rate_mean_pps (per node)")
        plt.ylabel("DMR")
        plt.ylim(0, 1.0)
        plt.title(f"DMR vs rate_mean_pps (N={args.nodes})")
        plt.grid(True, linewidth=0.4, alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(ROOT, "dmr_vs_rate.png"), dpi=120)
        plt.close()
    except Exception as e:
        with open(os.path.join(ROOT, "plot_error.log"), "a") as f:
            f.write(f"dmr_vs_rate plot error: {e}\n")

    md = os.path.join(ROOT, "rate_sweep_report.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# Rate Sweep (N={args.nodes}, Poisson gaps)\n\n")
        f.write(f"- target eta: **{TARGET_ETA:.2f}**\n")
        f.write(f"- best pps: **{best_pps}** (mean gap **{mean_gap_s:.3f} s**)\n")
        f.write(f"- at best: eta={best_eta:.3f}, DMR={best_dmr:.3f}, util={best_util:.3f}, coll={best_coll:.3f}, thr={best_thr:.3f} Mbps\n")
        f.write(f"- note: {note}\n\n")
        f.write("| pps | eta | DMR | util | coll | thr(Mbps) |\n|---:|---:|---:|---:|---:|---:|\n")
        for (pps, eta, dmr, util, coll, thr) in rows:
            f.write(f"| {pps} | {eta:.3f} | {dmr:.3f} | {util:.3f} | {coll:.3f} | {thr:.3f} |\n")

    print("\n== Recommended ==")
    print(f"rate_mean_pps={best_pps}  (mean gap ≈ {mean_gap_s:.3f}s)")
    print(f"eta={best_eta:.3f}, DMR={best_dmr:.3f}, util={best_util:.3f}, coll={best_coll:.3f}, thr={best_thr:.3f} Mbps")
    print("Saved plots: eta_vs_rate.png, dmr_vs_rate.png")
    print(f"Saved report: {md}")

if __name__ == "__main__":
    main()
