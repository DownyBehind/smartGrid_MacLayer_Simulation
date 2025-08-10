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
SIM_TIME    = 5.0   # (s) omnetpp.ini 에서 sim-time-limit = 5s 고정
# ────────────────────────────────────────────────────────

def parse_sca(file_path: pathlib.Path):
    """
    .sca에서 다음을 추출:
      - ns_slots, nc_slots, ni_slots
      - ts_time, tc_time, ti_time
      - (참고) nb_slots, tb_time  ← busy(무선 매체 바쁨) 값도 있으면 같이 저장
      - bytes_rcvd (host[0] 수신 바이트 합계)
    """
    ns = nc = ni = 0.0
    ts = tc = ti = 0.0
    nb = tb = 0.0   # 선택적(있으면 기록)
    bytes_rcvd = 0.0

    # scalar 행 패턴: 따옴표 유무 모두 매칭
    pat = re.compile(r'^scalar\s+(\S+)\s+"?([^"]+?)"?\s+([-+0-9.eE]+)')

    for L in file_path.read_text().splitlines():
        m = pat.match(L)
        if not m:
            continue
        module, name, val = m.groups()
        v = float(val)

        # ── 1) Throughput 계산용: sink(host[0]) 수신 바이트 ─────────────
        # 환경마다 이름이 다를 수 있어 둘 다 지원:
        #  - app 경로: rcvdPk:sum(packetBytes)
        #  - loopback 경로: rcvdPkFromHl:sum(packetBytes)
        if "host[0]" in module:
            if (
                ("app[0]" in module and name.startswith("rcvdPk:sum(packetBytes)"))
                or ("lo[0].lo" in module and name.startswith("rcvdPkFromHl:sum(packetBytes)"))
            ):
                bytes_rcvd += v
            # host[0]의 다른 값들은 집계에서 제외
            continue

        # ── 2) txProbe 원시값 ─────────────────────────────────────────
        if name == "ns_success_slots":
            ns += v
        elif name == "nc_collision_slots":
            nc += v
        elif name == "ts_success_time":
            ts += v
        elif name == "tc_collision_time":
            tc += v

        # ── 3) busyIdleProbe 원시값 ──────────────────────────────────
        elif name == "ni_idle_slots":
            ni += v
        elif name == "ti_idle_time":
            ti += v
        elif name == "nb_busy_slots":
            nb += v
        elif name == "tb_busy_time":
            tb += v

    return {
        "ns_slots": ns, "nc_slots": nc, "ni_slots": ni,
        "ts_time": ts, "tc_time": tc, "ti_time": ti,
        "nb_slots": nb, "tb_time": tb,         # 있으면 유용하니 같이 저장
        "bytes_rcvd": bytes_rcvd
    }

def collect_metrics():
    """
    results/n{n}/ 의 첫 .sca 파일을 파싱해
    원시값 + 파생지표(η_slot, P_coll, Throughput)를 함께 반환(DataFrame).
    """
    recs = []
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("n"):
            continue
        n = int(d.name.lstrip("n"))
        sca = next(d.glob(f"{CONFIG}-*.sca"), None)
        if not sca:
            continue

        raw = parse_sca(sca)

        ns, nc, ni = raw["ns_slots"], raw["nc_slots"], raw["ni_slots"]
        ts, tc, ti = raw["ts_time"], raw["tc_time"], raw["ti_time"]
        b = raw["bytes_rcvd"]

        # ── 파생 지표 ────────────────────────────────────────────────
        # 1) 슬롯 기반 효율
        denom_slots = ns + nc + ni
        eta_slot = ns / denom_slots if denom_slots > 0 else float("nan")

        # 2) 충돌 확률 (attempt 기준)
        attempts = ns + nc
        p_coll = nc / attempts if attempts > 0 else float("nan")

        # 3) Throughput [Mbps]
        throughput_mbps = (b * 8.0) / SIM_TIME / 1e6

        rec = {
            "nodes": n,
            # ── 원시값(raw) 전부 저장 ──
            "ns_slots": ns, "nc_slots": nc, "ni_slots": ni, "nb_slots": raw["nb_slots"],
            "ts_time": ts, "tc_time": tc, "ti_time": ti, "tb_time": raw["tb_time"],
            "bytes_rcvd": b, "sim_time_s": SIM_TIME, "sca_file": str(sca),
            # ── 파생 지표 ──
            "eta_slot": eta_slot, "p_coll": p_coll, "throughput_Mbps": throughput_mbps,
        }
        recs.append(rec)

    cols_order = [
        # 지표
        "nodes", "eta_slot", "p_coll", "throughput_Mbps",
        # 원시값
        "ns_slots", "nc_slots", "ni_slots", "nb_slots",
        "ts_time", "tc_time", "ti_time", "tb_time",
        "bytes_rcvd", "sim_time_s", "sca_file",
    ]
    df = pd.DataFrame(recs)
    if not df.empty:
        df = df[cols_order].sort_values("nodes")
    return df

def save_and_plot(df: pd.DataFrame):
    out_csv = RESULTS_DIR / "mac_additional_metrics.csv"
    df.to_csv(out_csv, index=False)
    print(f"✔ CSV saved → {out_csv}")

    # ── 그래프 3종(기존과 동일) ─────────────────────────────────────
    plt.figure()
    plt.plot(df["nodes"], df["eta_slot"], marker="o")
    plt.xlabel("Number of Nodes"); plt.ylabel("η_slot")
    plt.title("Slot-based MAC Efficiency")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "eta_slot_vs_nodes.png", dpi=300)
    print("✔ Figure saved → eta_slot_vs_nodes.png")

    plt.figure()
    plt.plot(df["nodes"], df["p_coll"], marker="s")
    plt.xlabel("Number of Nodes"); plt.ylabel("P_coll")
    plt.title("Collision Probability")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "p_coll_vs_nodes.png", dpi=300)
    print("✔ Figure saved → p_coll_vs_nodes.png")

    plt.figure()
    plt.plot(df["nodes"], df["throughput_Mbps"], marker="^")
    plt.xlabel("Number of Nodes"); plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput")
    plt.grid(True); plt.tight_layout()
    plt.savefig(RESULTS_DIR / "throughput_vs_nodes.png", dpi=300)
    print("✔ Figure saved → throughput_vs_nodes.png")

def main():
    df = collect_metrics()
    if df.empty:
        print("No results found under:", RESULTS_DIR)
        return

    print("\n=== ADDITIONAL MAC METRICS (with RAW columns) ===")
    # 요약 출력만: 핵심 지표 3개 + nodes
    print(df[["nodes", "eta_slot", "p_coll", "throughput_Mbps"]]
          .to_string(index=False, float_format="%.4f"))
    save_and_plot(df)

if __name__ == "__main__":
    main()
