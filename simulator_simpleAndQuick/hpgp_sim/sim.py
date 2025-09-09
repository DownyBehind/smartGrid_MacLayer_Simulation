"""
sim.py
======
- shared_bus:
    * N0=EVSE, N1..=EV
    * SLAC 상세 시퀀스
    * SLAC 완료 후: DC 루프(100ms 주기 Req / EVSE Res)
- cp_point_to_point: EV <-> EVSE peers
- 터미널 진행바(옵션), 세션 타임아웃 메트릭 전달
- DC 진입/주기/타임아웃 CSV & PNG 생성
- SLAC 타임라인 PNG 생성(메시지 5종 색상 간트)
"""

import json, os
from .utils import Sim
from .medium import Medium, BeaconScheduler, PRSManager
from .channel import GEChannel
from .mac_hpgp import HPGPMac, Priority
from .app_15118 import App15118
from .metrics import Metrics
from .plot_slac import write_slac_timeline

# ---- 진행바 ----
def _install_progress(sim, total_us, label="", step_pct=1):
    step_us = max(1, int(total_us * step_pct / 100))
    state = {"last_pct": -1, "bar_len": 30}
    def tick():
        now = sim.now()
        pct = min(100, int(now * 100 / max(1, total_us)))
        if pct != state["last_pct"]:
            filled = int(pct * state["bar_len"] / 100)
            bar = "█" * filled + "·" * (state["bar_len"] - filled)
            print(f"\r{label} [{bar}] {pct:3d}%  t={now/1e6:.2f}s", end="", flush=True)
            state["last_pct"] = pct
        if now < total_us:
            sim.at(min(step_us, total_us - now), tick)
        else:
            bar = "█" * state["bar_len"]
            print(f"\r{label} [{bar}] 100%  t={total_us/1e6:.2f}s", flush=True)
    sim.at(0, tick)

# ---- 리포트/아티팩트 ----
def _write_dc_artifacts(metrics: Metrics, sim_time_us: int, out_dir: str):
    """
    metrics.debug_rows에서 DC_* 이벤트를 모아 다음을 생성:
      - dc_entry_times.csv : node, dc_start_us, first_req_us, first_gap_us
      - dc_cycles.csv      : node, seq, req_us, gap_violation(0/1), rsp_us(있으면), rsp_latency_us, timeout(0/1)
      - dc_timeline.png    : 파랑(DC_START), 회색(Req), 빨간 X(주기 위반), 초록 점(응답)
    """
    import csv
    # 수집
    start_by_node = {}
    reqs_by_node  = {}  # node -> list of (seq, t, gap_v)
    rsps_by_node  = {}  # node -> dict seq->t
    timeouts      = set()  # (node, seq)
    for t, tag, kv in metrics.debug_rows:
        if tag == "DC_START":
            start_by_node[kv.get("node")] = t
        elif tag == "DC_REQ":
            n = kv.get("node"); seq = int(kv.get("seq")); gap_v = int(kv.get("gap_violation", 0))
            reqs_by_node.setdefault(n, []).append((seq, t, gap_v))
        elif tag == "DC_RSP":
            n = kv.get("node"); seq = int(kv.get("seq"))
            rsps_by_node.setdefault(n, {})[seq] = t
        elif tag == "DC_TIMEOUT":
            n = kv.get("node"); seq = int(kv.get("seq"))
            timeouts.add((n, seq))

    # dc_entry_times.csv
    with open(os.path.join(out_dir, "dc_entry_times.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["node","dc_start_us","first_req_us","first_gap_us"])
        for node, st in sorted(start_by_node.items()):
            first_req = None; first_gap = None
            if node in reqs_by_node and reqs_by_node[node]:
                seq, t, gap_v = sorted(reqs_by_node[node], key=lambda x:x[0])[0]
                first_req = t; first_gap = (t - st) if st is not None else None
            w.writerow([node, st, first_req, first_gap])

    # dc_cycles.csv
    with open(os.path.join(out_dir, "dc_cycles.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["node","seq","req_us","gap_violation","rsp_us","rsp_latency_us","timeout"])
        for node, reqs in sorted(reqs_by_node.items()):
            for seq, t, gap_v in sorted(reqs, key=lambda x:x[0]):
                rsp_t = rsps_by_node.get(node, {}).get(seq)
                latency = (rsp_t - t) if rsp_t is not None else None
                to = 1 if (node, seq) in timeouts else 0
                w.writerow([node, seq, t, gap_v, rsp_t, latency, to])

    # png: 타임라인
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 4))
        # y축: node를 정렬해서 인덱스 부여
        nodes = sorted(set(list(start_by_node.keys()) + list(reqs_by_node.keys())))
        y_of = {n:i for i,n in enumerate(nodes)}
        # 파란 점: DC_START
        for n, st in start_by_node.items():
            plt.scatter([st/1e6],[y_of[n]], s=30, marker="o", label="DC_START" if n==nodes[0] else "", color="tab:blue")
        # 회색 점: Req
        for n, reqs in reqs_by_node.items():
            xs=[t/1e6 for (_,t,_) in reqs]; ys=[y_of[n]]*len(reqs)
            plt.scatter(xs, ys, s=12, marker=".", label="DC_REQ" if n==nodes[0] else "", color="gray")
        # 빨간 X: 주기 위반
        for n, reqs in reqs_by_node.items():
            xs=[t/1e6 for (_,t,g) in reqs if g]; ys=[y_of[n]]*len([1 for (_,_,g) in reqs if g])
            if xs:
                plt.scatter(xs, ys, s=30, marker="x", label="Period Violation" if n==nodes[0] else "", color="red")
        # 초록 점: 응답
        for n, m in rsps_by_node.items():
            xs=[t/1e6 for t in m.values()]; ys=[y_of[n]]*len(m)
            if xs:
                plt.scatter(xs, ys, s=14, marker="o", label="DC_RSP" if n==nodes[0] else "", color="tab:green")

        plt.yticks(range(len(nodes)), nodes)
        plt.xlabel("Time (s)"); plt.title("DC timeline (start/req/violations/rsp)")
        plt.grid(True, lw=0.4, alpha=0.5)
        plt.legend(loc="upper right", ncol=2, fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "dc_timeline.png"), dpi=140)
        plt.close()
    except Exception as e:
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
            f.write(f"dc_timeline plot error: {e}\n")

def _write_all_reports(metrics: Metrics, sim_time_us: int, out_dir: str):
    s = metrics.summary(sim_time_us)
    metrics.dump()
    metrics.dump_per_node(sim_time_us)
    metrics.dump_summary_csv(s)
    metrics.write_report(s)
    metrics.write_plots(sim_time_us)         # 효율 PNG (옵션)
    _write_dc_artifacts(metrics, sim_time_us, out_dir)  # DC 관련 CSV/PNG

    # --- 추가: SLAC 타임라인 생성 (메시지 5종 색상 간트) ---
    try:
        write_slac_timeline(out_dir, sim_time_us=sim_time_us)  # x축 [0..sim_time_s] 고정 slac_timeline.png
    except Exception as e:
        # 실패해도 전체 플로우에 영향 없도록 로그만 남김
        with open(os.path.join(out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
            f.write(f"slac_timeline plot error: {e}\n")

    return s

def _finalize_and_return(cfg, metrics, sim_time_us, out_dir):
    s = _write_all_reports(metrics, sim_time_us, out_dir)
    return s, os.path.abspath(out_dir)

def build_and_run(cfg_path, out_dir="/mnt/data/out", seed=1, progress=False, progress_label=""):
    # 설정 로드
    with open(cfg_path, "r") as f:
        cfg = json.load(f)

    sim = Sim(seed=seed)
    os.makedirs(out_dir, exist_ok=True)

    # Medium/metrics
    med = Medium(sim, topology=cfg["topology"])
    metrics = Metrics(sim, out_dir); med.metrics = metrics

    # MAC/Beacon/PRS
    timing = cfg["mac"].get("timing", {})
    prs_cfg = timing.get("prs", {"symbols":2, "symbol_us":36})
    med.prs = PRSManager(sim, med, prs_symbols=prs_cfg.get("symbols",2), symbol_us=prs_cfg.get("symbol_us",36))
    beacon_cfg = timing.get("beacon", {"period_us":100000, "duration_us":2000})
    med.beacon = BeaconScheduler(sim, med, period_us=beacon_cfg.get("period_us",100000), duration_us=beacon_cfg.get("duration_us",2000))
    if timing.get("beacon_enable", True): med.beacon.start()

    # 채널
    ch  = GEChannel(sim,
        p_bg=cfg["channel"]["p_bg"],
        p_bb=cfg["channel"]["p_bb"],
        per_good=cfg["channel"]["per_good"],
        per_bad=cfg["channel"]["per_bad"],
        step_us=cfg["channel"]["step_us"],
        periodic=cfg["channel"].get("periodic", None)
    )

    # 세션 타임아웃
    tt_s = cfg.get("traffic", {}).get("slac_session", {}).get("TT_session_s", None)
    if tt_s is not None and hasattr(metrics, "set_session_timeout_us"):
        metrics.set_session_timeout_us(int(float(tt_s) * 1e6))

    # SLAC 상세 파라미터
    slac_detail = cfg.get("traffic", {}).get("slac_detail", {})
    N_start_atten = int(slac_detail.get("start_atten_count", 3))
    N_msound      = int(slac_detail.get("msound_count", 10))
    gap_start_us  = int(slac_detail.get("start_atten_gap_us", 2000))
    gap_msound_us = int(slac_detail.get("msound_gap_us",     2000))
    delay_evse_rsp_us = int(slac_detail.get("evse_resp_delay_us", 1000))
    gap_attn_us   = int(slac_detail.get("attn_gap_us", 2000))
    gap_match_us  = int(slac_detail.get("match_gap_us", 2000))

    # DC 루프 파라미터
    dc_loop = cfg.get("traffic", {}).get("dc_loop", {})
    dc_enabled       = bool(dc_loop.get("enabled", True))
    dc_period_ms     = int(dc_loop.get("period_ms", 100))
    dc_deadline_ms   = int(dc_loop.get("deadline_ms", 100))
    dc_rsp_delay_us  = int(dc_loop.get("rsp_delay_us", 1500))
    dc_rsp_jitter_us = int(dc_loop.get("rsp_jitter_us", 0))

    # Optional global override via environment variable
    try:
        _env_sim_time = os.environ.get("SIM_TIME_S", None)
        if _env_sim_time is not None:
            cfg["sim_time_s"] = float(_env_sim_time)
    except Exception:
        pass
    sim_time_us = int(cfg["sim_time_s"] * 1e6)

    # --- 토폴로지별 빌드 ---
    topo = cfg["topology"]
    if topo == "shared_bus":
        nodes = cfg.get("nodes", 2)
        apps = []
        for i in range(nodes):
            node_id = f"N{i}"
            mac = HPGPMac(sim, med, ch, node_id, cfg["mac"], metrics)
            role = "EVSE" if i == 0 else "EV"
            app = App15118(sim, mac, role=role, timers=cfg["traffic"].get("slac_timers", None), metrics=metrics, app_id=node_id)
            app.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us, delay_evse_rsp_us, gap_attn_us, gap_match_us)
            app.configure_dc_loop(enabled=dc_enabled, period_ms=dc_period_ms, deadline_ms=dc_deadline_ms,
                                  rsp_delay_us=dc_rsp_delay_us, rsp_jitter_us=dc_rsp_jitter_us)
            apps.append(app)

        # EV들 peer → EVSE(N0)
        evse_app = apps[0]
        for i in range(1, nodes):
            apps[i].set_peer(evse_app)

        # SLAC 시작(피어 오프셋)
        peer_offset = int(cfg.get("traffic", {}).get("slac_peer_offset_us", 5000))
        for i in range(1, nodes):
            apps[i].start_slac(start_us=(i-1)*peer_offset)

        if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
            _install_progress(sim, sim_time_us, label=(progress_label or f"N={nodes}"))

        sim.run(until=sim_time_us)
        if progress or os.environ.get("HPGP_PROGRESS", "") == "1": print("")
        return _finalize_and_return(cfg, metrics, sim_time_us, out_dir)

    else:
        # point-to-point
        macA = HPGPMac(sim, med, ch, "EV",   cfg["mac"], metrics)
        macB = HPGPMac(sim, med, ch, "EVSE", cfg["mac"], metrics)
        appA = App15118(sim, macA, role="EV",   timers=cfg["traffic"].get("slac_timers", None), metrics=metrics, app_id="EV")
        appB = App15118(sim, macB, role="EVSE", timers=cfg["traffic"].get("slac_timers", None), metrics=metrics, app_id="EVSE")
        appA.set_peer(appB); appB.set_peer(appA)
        appA.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us, delay_evse_rsp_us, gap_attn_us, gap_match_us)
        appB.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us, delay_evse_rsp_us, gap_attn_us, gap_match_us)
        appA.configure_dc_loop(enabled=dc_enabled, period_ms=dc_period_ms, deadline_ms=dc_deadline_ms,
                               rsp_delay_us=dc_rsp_delay_us, rsp_jitter_us=dc_rsp_jitter_us)
        appB.configure_dc_loop(enabled=dc_enabled, period_ms=dc_period_ms, deadline_ms=dc_deadline_ms,
                               rsp_delay_us=dc_rsp_delay_us, rsp_jitter_us=dc_rsp_jitter_us)

        if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
            _install_progress(sim, sim_time_us, label=(progress_label or "sim"))

        appA.start_slac(start_us=0)
        sim.run(until=sim_time_us)
        if progress or os.environ.get("HPGP_PROGRESS", "") == "1": print("")
        return _finalize_and_return(cfg, metrics, sim_time_us, out_dir)
