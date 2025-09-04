# sweep_nodes.py
# ==============
# 역할
# - shared_bus 토폴로지에서 노드 수를 5,10,15,...,100으로 스윕
# - 각 노드에 '1노드 풀부하'와 같은 per-node rate를 적용(총부하 ∝ 노드 수)
# - 효율(η)과 DMR 그래프/CSV 저장

import sys, json, os
# Add the parent directory (simulator_simpleAndQuick) to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hpgp_sim.sim import build_and_run

import matplotlib.pyplot as plt

def run_sweep(base_cfg_path, out_csv, nodes_list):
    rows = []
    base = json.load(open(base_cfg_path))
    heavy_rate = base["traffic"]["background"].get("full_load_rate_pps",
                   base["traffic"]["background"].get("rate_pps", 50))

    for n in nodes_list:
        cfg = json.load(open(base_cfg_path))
        cfg["topology"] = "shared_bus"
        cfg["nodes"] = n
        # per-node 부하를 1노드 풀부하와 동일하게
        cfg["traffic"]["background"]["rate_pps"] = heavy_rate

        out_dir = os.path.join(os.path.dirname(base_cfg_path), f"..{os.sep}out_sweep_N{n}")
        out_dir = os.path.abspath(out_dir)

        tmp = os.path.join(os.path.dirname(base_cfg_path), f"tmp_N{n}.json")
        json.dump(cfg, open(tmp,"w"))

        s, _ = build_and_run(tmp, out_dir=out_dir, seed=42+n)
        rows.append([n, s["efficiency_eta"], s["deadline_miss_ratio"], s["drops"]])

    # CSV
    with open(out_csv, "w") as f:
        f.write("nodes,efficiency_eta,deadline_miss_ratio,drops\n")
        for r in rows:
            f.write(",".join(str(x) for x in r)+"\n")

    xs = [r[0] for r in rows]
    etas = [r[1] for r in rows]
    dmrs = [r[2] for r in rows]

    # 효율 그래프
    plt.figure()
    plt.plot(xs, etas, marker="o")
    plt.xlabel("Nodes")
    plt.ylabel("Efficiency η")
    plt.title("Efficiency vs Nodes (per-node full-load)")
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(out_csv), "out_sweep_efficiency.png"))

    # DMR 그래프
    plt.figure()
    plt.plot(xs, dmrs, marker="o")
    plt.xlabel("Nodes")
    plt.ylabel("Deadline Miss Ratio")
    plt.title("DMR vs Nodes (per-node full-load)")
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(out_csv), "out_sweep_dmr.png"))

if __name__ == "__main__":
    # 프로젝트 루트 기준으로 경로 맞춰주세요.
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "defaults.json"))
    out_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out_sweep_summary.csv"))
    nodes = list(range(5, 101, 5))
    run_sweep(base, out_csv, nodes)
    print("Wrote:", out_csv)
