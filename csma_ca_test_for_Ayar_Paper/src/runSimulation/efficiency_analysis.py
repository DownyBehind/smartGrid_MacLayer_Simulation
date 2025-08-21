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
    .sca에서 다음 원시값 추출:
      host[0].busyIdleProbe (채널 전역):
        - ni_idle_slots, nb_busy_slots, ti_idle_time, tb_busy_time
      송신노드( host[0] 제외 )의 txProbe:
        - ns_success_slots, ts_success_time
        - nc_collision_slots, tc_collision_time  # [NEW] 직접 파싱
      sink( host[0].app[0] ):
        - packetReceived:sum(packetBytes) 또는 rcvdPk:sum(packetBytes)
        - packetReceived:count        또는 rcvdPk:count (있으면)
    """
    # 채널 전역 (host[0]에서만)
    ni_slots = 0.0
    nb_slots = 0.0
    ti_time  = 0.0
    tb_time  = 0.0

    # 송신 측 합산 (host[0] 제외)
    ns_slots = 0.0
    ts_time  = 0.0
    nc_slots = None  # [NEW] 직접 기록이 있으면 누적, 없으면 None 유지
    tc_time  = None  # [NEW]

    # 수신량 (sink)
    bytes_rcvd   = 0.0
    packets_rcvd = 0.0

    # scalar 행 패턴: 따옴표 유무 모두 매칭
    pat = re.compile(r'^scalar\s+(\S+)\s+"?([^"]+?)"?\s+([-+0-9.eE]+)$')

    for L in file_path.read_text().splitlines():
        m = pat.match(L)
        if not m:
            continue

        module, name, val = m.groups()
        try:
            v = float(val)
        except ValueError:
            # 숫자가 아닌 라인은 무시 (예: "computation count")
            continue

        # 1) Sink 수신량(이름 변형 모두 지원)
        if module.endswith(".host[0].app[0]"):
            if name in ("packetReceived:sum(packetBytes)", "rcvdPk:sum(packetBytes)"):
                bytes_rcvd += v
                continue
            if name in ("packetReceived:count", "rcvdPk:count"):
                packets_rcvd += v
                continue

        # 2) 채널 전역 idle/busy: host[0]만 사용
        if module.endswith(".host[0].busyIdleProbe"):
            if name == "ni_idle_slots":
                ni_slots = v
            elif name == "nb_busy_slots":
                nb_slots = v
            elif name == "ti_idle_time":
                ti_time = v
            elif name == "tb_busy_time":
                tb_time = v
            continue

        # 3) 송신 노드들의 성공/충돌 합산 (host[0] 제외)
        if ".host[0]." in module:
            continue  # host[0]은 sink이므로 제외

        if name == "ns_success_slots":
            ns_slots += v
        elif name == "ts_success_time":
            ts_time += v
        elif name == "nc_collision_slots":           # [NEW]
            nc_slots = (0.0 if nc_slots is None else nc_slots) + v
        elif name == "tc_collision_time":            # [NEW]
            tc_time  = (0.0 if tc_time  is None else tc_time ) + v

    return {
        "ns_slots": ns_slots,
        "ni_slots": ni_slots,
        "nb_slots": nb_slots,
        "ts_time":  ts_time,
        "ti_time":  ti_time,
        "tb_time":  tb_time,
        "nc_slots": nc_slots,   # [NEW]
        "tc_time":  tc_time,    # [NEW]
        "bytes_rcvd":   bytes_rcvd,
        "packets_rcvd": packets_rcvd,
    }

def collect_metrics():
    """
    results/n{n}/ 첫 .sca 파일을 파싱해서
    η_slot, η_tx, p_coll, Throughput 등을 계산하고 원시값도 함께 반환.
    - 충돌 슬롯/시간: 기록이 있으면 우선 사용, 없으면 유도식으로 보정
      (nc_slots = max(0, nb_slots - ns_slots), tc_time = max(0, tb_time - ts_time))
    """
    recs = []
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("n"):
            continue
        try:
            n = int(d.name.lstrip("n"))
        except ValueError:
            continue

        sca = next(d.glob(f"{CONFIG}-*.sca"), None)
        if not sca:
            continue

        raw = parse_sca(sca)

        ns = raw["ns_slots"]
        nb = raw["nb_slots"]
        ni = raw["ni_slots"]
        ts = raw["ts_time"]
        tb = raw["tb_time"]
        ti = raw["ti_time"]

        # [FIX] 충돌: 기록값 우선, 없으면 유도
        nc = raw["nc_slots"] if raw["nc_slots"] is not None else max(0.0, nb - ns)
        tc = raw["tc_time"]  if raw["tc_time"]  is not None else max(0.0, tb - ts)

        # 지표
        denom_slots = ns + nc + ni
        eta_slot = ns / denom_slots if denom_slots > 0 else float("nan")

        denom_time = ts + tc + ti
        eta_tx = ts / denom_time if denom_time > 0 else float("nan")

        p_coll = nc / (ns + nc) if (ns + nc) > 0 else float("nan")

        # Throughput [Mbps]
        throughput_mbps = (raw["bytes_rcvd"] * 8.0) / SIM_TIME / 1e6

        recs.append({
            # 원시값 모두 저장
            "ns_slots": ns,
            "nc_slots": nc,
            "ni_slots": ni,
            "nb_slots": nb,
            "ts_time":  ts,
            "tc_time":  tc,
            "ti_time":  ti,
            "tb_time":  tb,
            "bytes_rcvd":   raw["bytes_rcvd"],
            "packets_rcvd": raw["packets_rcvd"],
            # 파생 지표
            "eta_slot": eta_slot,
            "eta_tx":   eta_tx,
            "p_coll":   p_coll,
            "throughput_Mbps": throughput_mbps,
            "nodes":    n,
        })

    df = pd.DataFrame(recs).sort_values("nodes").reset_index(drop=True)
    return df

def save_and_plot(df: pd.DataFrame):
    # CSV 저장 (원시값 + 지표 모두 포함)
    out_csv = RESULTS_DIR / "mac_efficiency_extended.csv"
    df.to_csv(out_csv, index=False)
    print(f"✔ CSV saved → {out_csv}")

    # 개별 그래프 3종 (기존 출력 유지)
    # 1) η_slot vs nodes
    plt.figure()
    plt.plot(df["nodes"], df["eta_slot"], marker="o")
    plt.xlabel("Number of Nodes")
    plt.ylabel("η_slot")
    plt.title("Slot-based MAC Efficiency vs Nodes")
    plt.grid(True)
    out_png1 = RESULTS_DIR / "eta_slot_vs_nodes.png"
    plt.tight_layout(); plt.savefig(out_png1, dpi=300)
    print(f"✔ Figure saved → {out_png1}")

    # 2) P_coll vs nodes
    plt.figure()
    plt.plot(df["nodes"], df["p_coll"], marker="s")
    plt.xlabel("Number of Nodes")
    plt.ylabel("Collision Probability (P_coll)")
    plt.title("Collision Probability vs Nodes")
    plt.grid(True)
    out_png2 = RESULTS_DIR / "p_coll_vs_nodes.png"
    plt.tight_layout(); plt.savefig(out_png2, dpi=300)
    print(f"✔ Figure saved → {out_png2}")

    # 3) Throughput vs nodes
    plt.figure()
    plt.plot(df["nodes"], df["throughput_Mbps"], marker="^")
    plt.xlabel("Number of Nodes")
    plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput vs Nodes")
    plt.grid(True)
    out_png3 = RESULTS_DIR / "throughput_vs_nodes.png"
    plt.tight_layout(); plt.savefig(out_png3, dpi=300)
    print(f"✔ Figure saved → {out_png3}")

def main():
    df = collect_metrics()
    # 콘솔 출력 (기존 형식 최대한 유지)
    cols = ["ns_slots","nc_slots","ni_slots","nb_slots",
            "ts_time","tc_time","ti_time","tb_time",
            "eta_slot","eta_tx","nodes","throughput_Mbps","packets_rcvd","bytes_rcvd"]
    cols = [c for c in cols if c in df.columns]  # 안전장치
    print("\n=== EXTENDED MAC EFFICIENCY RESULTS ===")
    with pd.option_context("display.max_rows", None,
                           "display.float_format", "{:.4f}".format):
        print(df[cols].to_string(index=False))
    save_and_plot(df)

if __name__=="__main__":
    main()
