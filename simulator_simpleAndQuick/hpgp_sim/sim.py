"""
sim.py
======
- shared_bus:
    * N0=EVSE, N1..=EV
    * EVs start SLAC in sequence (peer offset)
    * Detailed SLAC for SLAC stage (CAP3)
    * After SLAC (EV): DC CurrentDemand loop (CAP0), 100 ms default
- cp_point_to_point: EV <-> EVSE peers, same behavior
- Terminal progress bar (optional)
- Pass session timeout & DC loop params to metrics/app
- On finalize: write CSV/MD + PNG (efficiency/DMR + DC timeline)
"""

import json, os
from .utils import Sim
from .medium import Medium, BeaconScheduler, PRSManager
from .channel import GEChannel
from .mac_hpgp import HPGPMac, Priority
from .app_15118 import App15118
from .metrics import Metrics

def load_config(path):
    with open(path, "r") as f:
        return json.load(f)

# ---- simple terminal progress bar ----
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
            print(f"\r{label} [{'█'*state['bar_len']}] 100%  t={total_us/1e6:.2f}s", flush=True)
    sim.at(0, tick)

def _finalize_and_return(metrics, sim_time_us, out_dir):
    s = metrics.summary(sim_time_us)
    metrics.dump()
    metrics.dump_per_node(sim_time_us)
    metrics.dump_summary_csv(s)
    metrics.write_report(s)
    metrics.write_plots(sim_time_us)  # efficiency/dmr + dc timeline
    return s, os.path.abspath(out_dir)

def build_and_run(cfg_path, out_dir="/mnt/data/out", seed=1, *,
                  progress=False, progress_label=""):
    cfg = load_config(cfg_path)
    sim = Sim(seed=seed)
    os.makedirs(out_dir, exist_ok=True)

    # medium/metrics
    med = Medium(sim, topology=cfg["topology"])
    metrics = Metrics(sim, out_dir); med.metrics = metrics

    # ---- session timeout ----
    tt_s = cfg.get("traffic", {}).get("slac_session", {}).get("TT_session_s", None)
    if tt_s is not None and hasattr(metrics, "set_session_timeout_us"):
        metrics.set_session_timeout_us(int(float(tt_s) * 1e6))

    # ---- DC loop params (analysis labels) ----
    dc_cfg = cfg.get("traffic", {}).get("dc_loop", {})
    dc_enabled = bool(dc_cfg.get("enabled", True))
    dc_period_ms = float(dc_cfg.get("period_ms", 100))
    dc_deadline_ms = float(dc_cfg.get("deadline_ms", 100))
    dc_rsp_delay_us = int(dc_cfg.get("rsp_delay_us", 1500))
    dc_rsp_jitter_us = int(dc_cfg.get("rsp_jitter_us", 0))

    if hasattr(metrics, "set_dc_deadline_us"):
        metrics.set_dc_deadline_us(int(dc_deadline_ms * 1000))
    if hasattr(metrics, "set_dc_period_us"):
        metrics.set_dc_period_us(int(dc_period_ms * 1000))

    # timing (PRS/Beacon)
    timing = cfg["mac"].get("timing", {})
    prs_cfg = timing.get("prs", {"symbols":2, "symbol_us":36})
    med.prs = PRSManager(sim, med,
                         prs_symbols=prs_cfg.get("symbols",2),
                         symbol_us=prs_cfg.get("symbol_us",36))
    beacon_cfg = timing.get("beacon", {"period_us":100000, "duration_us":2000})
    med.beacon = BeaconScheduler(sim, med,
                                 period_us=beacon_cfg.get("period_us",100000),
                                 duration_us=beacon_cfg.get("duration_us",2000))
    if timing.get("beacon_enable", True):
        med.beacon.start()

    # channel
    ch  = GEChannel(sim,
        p_bg=cfg["channel"]["p_bg"],
        p_bb=cfg["channel"]["p_bb"],
        per_good=cfg["channel"]["per_good"],
        per_bad=cfg["channel"]["per_bad"],
        step_us=cfg["channel"]["step_us"],
        periodic=cfg["channel"].get("periodic", None)
    )

    # detailed SLAC params
    slac_detail = cfg.get("traffic", {}).get("slac_detail", {})
    N_start_atten = int(slac_detail.get("start_atten_count", 3))
    N_msound      = int(slac_detail.get("msound_count", 10))
    gap_start_us  = int(slac_detail.get("start_atten_gap_us", 2000))
    gap_msound_us = int(slac_detail.get("msound_gap_us",     2000))
    delay_evse_rsp_us = int(slac_detail.get("evse_resp_delay_us", 1000))
    gap_attn_us   = int(slac_detail.get("attn_gap_us", 2000))
    gap_match_us  = int(slac_detail.get("match_gap_us", 2000))

    # post-SLAC legacy (kept for compatibility)
    post_slac = cfg.get("traffic", {}).get("post_slac", {})
    rate_mean_pps = float(post_slac.get("rate_mean_pps", 50))
    bytes_min     = int(post_slac.get("bytes_min", 300))
    bytes_max     = int(post_slac.get("bytes_max", 1500))
    start_delay_us= int(post_slac.get("start_delay_us", 0))
    peer_offset   = int(cfg.get("traffic", {}).get("slac_peer_offset_us", 5000))

    sim_time_us = int(cfg["sim_time_s"] * 1e6)

    # ===== shared_bus =====
    nodes = cfg.get("nodes", 2)
    if cfg["topology"] == "shared_bus":
        apps = []
        for i in range(nodes):
            node_id = f"N{i}"
            mac = HPGPMac(sim, med, ch, node_id, cfg["mac"], metrics)
            role = "EVSE" if i == 0 else "EV"
            app = App15118(sim, mac, role=role,
                           timers=cfg["traffic"].get("slac_timers", None),
                           metrics=metrics, app_id=node_id)
            # SLAC & DC config
            app.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us,
                                      delay_evse_rsp_us, gap_attn_us, gap_match_us)
            app.configure_dc_loop(enabled=dc_enabled,
                                  period_ms=dc_period_ms,
                                  deadline_ms=dc_deadline_ms,
                                  rsp_delay_us=dc_rsp_delay_us,
                                  rsp_jitter_us=dc_rsp_jitter_us)
            # legacy random (used only if DC disabled)
            app.configure_post_slac_traffic(rate_mean_pps=rate_mean_pps,
                                            bytes_min=bytes_min, bytes_max=bytes_max,
                                            cap_choices=[Priority.CAP0, Priority.CAP1, Priority.CAP2],
                                            start_delay_us=start_delay_us)
            apps.append(app)

        # wire peers (all EVs point to EVSE N0)
        evse_app = apps[0]
        for i in range(1, nodes):
            apps[i].set_peer(evse_app)

        # start SLAC for EVs only (sequential offsets)
        for i in range(1, nodes):
            apps[i].start_slac(start_us=(i-1)*peer_offset)

        if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
            _install_progress(sim, sim_time_us, label=(progress_label or "sim"))

        sim.run(until=sim_time_us)

        if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
            print("")
        return _finalize_and_return(metrics, sim_time_us, out_dir)

    # ===== cp_point_to_point =====
    macA = HPGPMac(sim, med, ch, "EV",   cfg["mac"], metrics)
    macB = HPGPMac(sim, med, ch, "EVSE", cfg["mac"], metrics)
    appA = App15118(sim, macA, role="EV",   timers=cfg["traffic"].get("slac_timers", None), metrics=metrics, app_id="EV")
    appB = App15118(sim, macB, role="EVSE", timers=cfg["traffic"].get("slac_timers", None), metrics=metrics, app_id="EVSE")

    appA.set_peer(appB); appB.set_peer(appA)

    appA.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us,
                               delay_evse_rsp_us, gap_attn_us, gap_match_us)
    appB.configure_slac_detail(N_start_atten, N_msound, gap_start_us, gap_msound_us,
                               delay_evse_rsp_us, gap_attn_us, gap_match_us)

    appA.configure_dc_loop(enabled=dc_enabled,
                           period_ms=dc_period_ms,
                           deadline_ms=dc_deadline_ms,
                           rsp_delay_us=dc_rsp_delay_us,
                           rsp_jitter_us=dc_rsp_jitter_us)
    appB.configure_dc_loop(enabled=dc_enabled,
                           period_ms=dc_period_ms,
                           deadline_ms=dc_deadline_ms,
                           rsp_delay_us=dc_rsp_delay_us,
                           rsp_jitter_us=dc_rsp_jitter_us)

    # legacy random
    for app in (appA, appB):
        app.configure_post_slac_traffic(rate_mean_pps=rate_mean_pps,
                                        bytes_min=bytes_min, bytes_max=bytes_max,
                                        cap_choices=[Priority.CAP0, Priority.CAP1, Priority.CAP2],
                                        start_delay_us=start_delay_us)

    if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
        _install_progress(sim, sim_time_us, label=(progress_label or "sim"))

    appA.start_slac(start_us=0)
    sim.run(until=sim_time_us)
    if progress or os.environ.get("HPGP_PROGRESS", "") == "1":
        print("")
    return _finalize_and_return(metrics, sim_time_us, out_dir)
