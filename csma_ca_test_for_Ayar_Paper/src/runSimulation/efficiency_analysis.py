#!/usr/bin/env python3
import re
import pathlib
import pandas as pd
import matplotlib.pyplot as plt

# ─── 경로 설정 ─────────────────────────────────────────
PROJECT     = pathlib.Path(
    "/home/kimdawoon/study/workspace/research/"
    "project_smartCharging_macLayer_improvement/"
    "csma_ca_test_for_Ayar_Paper"
)
RESULTS_DIR = PROJECT / "ini" / "results"
CONFIG      = "Paper_Baseline"
SIM_TIME    = 5.0   # (s) omnetpp.ini 에서 sim-time-limit = 5s 로 고정
# ────────────────────────────────────────────────────────

def parse_sca(file_path: pathlib.Path):
    """
    .sca 파일에서 다음을 모두 뽑아서 반환:
      - ns_slots, nc_slots, ni_slots        (txProbe / busyIdleProbe)
      - ts_time, tc_time, ti_time
      - bytes_rcvd                          (host[0].lo[0].lo rcvdPkFromHl:sum(packetBytes))
    """
    ns = nc = 0.0
    ni = 0.0
    ts = tc = ti = 0.0
    bytes_rcvd = 0.0

    # scalar 행 패턴: 따옴표 유무 모두 매칭
    pat = re.compile(r'^scalar\s+(\S+)\s+"?([^"]+?)"?\s+([-+0-9.eE]+)')

    for L in file_path.read_text().splitlines():
        m = pat.match(L)
        if not m:
            continue
        module, name, val = m.groups()
        v = float(val)

        # 1) Throughput 계산용:
        #    loopback 인터페이스에서 수신된 바이트
        if ".host[0].lo[0].lo" in module and name == "rcvdPkFromHl:sum(packetBytes)":
            bytes_rcvd += v
            continue

        # 2) sink host[0] 나머지 스킵
        if ".host[0]." in module:
            continue

        # txProbe
        if name == "ns_success_slots":
            ns += v
        elif name == "nc_collision_slots":
            nc += v
        elif name == "ts_success_time":
            ts += v
        elif name == "tc_collision_time":
            tc += v

        # busyIdleProbe
        elif name == "ni_idle_slots":
            ni += v
        elif name == "ti_idle_time":
            ti += v

    return ns, nc, ni, ts, tc, ti, bytes_rcvd

def collect_metrics():
    recs = []
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("n"):
            continue
        n = int(d.name.lstrip("n"))
        sca = next(d.glob(f"{CONFIG}-*.sca"), None)
        if not sca:
            continue

        ns, nc, ni, ts, tc, ti, b = parse_sca(sca)
        # Slot efficiency
        eta_slot = ns / (ns + nc + ni) if (ns + nc + ni) > 0 else float("nan")
        # Collision probability
        p_coll = nc / (ns + nc) if (ns + nc) > 0 else float("nan")
        # Throughput [Mbps]
        tp_mbps = (b * 8.0) / SIM_TIME / 1e6

        recs.append({
            "nodes": n,
            "eta_slot": eta_slot,
            "p_coll": p_coll,
            "throughput_Mbps": tp_mbps,
        })
    return pd.DataFrame(recs).sort_values("nodes")

def save_and_plot(df):
    out_csv = RESULTS_DIR / "mac_additional_metrics.csv"
    df.to_csv(out_csv, index=False)
    print(f"✔ CSV saved → {out_csv}")

    # Slot-based Efficiency
    plt.figure()
    plt.plot(df["nodes"], df["eta_slot"], marker="o")
    plt.xlabel("Number of Nodes"); plt.ylabel("η_slot")
    plt.title("Slot-based MAC Efficiency")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "eta_slot_vs_nodes.png", dpi=300)
    print("✔ Figure saved → eta_slot_vs_nodes.png")

    # Collision Probability
    plt.figure()
    plt.plot(df["nodes"], df["p_coll"], marker="s", color='orange')
    plt.xlabel("Number of Nodes"); plt.ylabel("P_coll")
    plt.title("Collision Probability")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "p_coll_vs_nodes.png", dpi=300)
    print("✔ Figure saved → p_coll_vs_nodes.png")

    # Throughput
    plt.figure()
    plt.plot(df["nodes"], df["throughput_Mbps"], marker="^", color='green')
    plt.xlabel("Number of Nodes"); plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "throughput_vs_nodes.png", dpi=300)
    print("✔ Figure saved → throughput_vs_nodes.png")

def main():
    df = collect_metrics()
    print("\n=== ADDITIONAL MAC METRICS ===")
    print(df.to_string(index=False, float_format="%.4f"))
    save_and_plot(df)

if __name__ == "__main__":
    main()

