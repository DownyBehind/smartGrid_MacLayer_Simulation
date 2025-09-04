"""
metrics.py (session-timeout centric + PNG plots)
- TX/충돌 로깅
- SLAC 세션 추적 (세션 시작/종료/타임아웃)
- 효율/타임아웃 시간경과 그래프 PNG 저장
- summary.csv / node_summary.csv / report.md에 session_* 지표 포함
- sessions.csv 생성: node, start_us, end_us, duration_us, ok, timeout
NOTE: 이전의 DMR(deadline miss) 관련 로직/아티팩트는 제거되었습니다.
"""

import os, csv
import math

# Matplotlib for PNG plotting (headless)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class Metrics:
    def __init__(self, sim, out_dir):
        self.sim = sim
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        # time accounting (totals)
        self.t_success = 0
        self.t_collision = 0
        self.t_control = 0
        self.t_idle = 0

        # counters
        self.tx_ok = 0
        self.tx_err = 0
        self.drops = 0
        self.timeouts = 0  # (message-level; kept for backward compat — not used for SLAC)

        # per-node counters
        self.per_node = {}

        # logs (in-memory)
        # start_us, end_us, node, prio, bits, kind, success
        self.tx_rows = []
        # t_us, tag, kv
        self.debug_rows = []

        # SLAC session tracking
        self.tt_session_us = 500_000  # default 0.5 s (override via sim.py from config)
        self.sessions_active = {}     # node -> start_us
        self.sessions_log = []        # dict(node, start_us, end_us, duration_us, ok, timeout)

    # ===== session timeout config =====
    def set_session_timeout_us(self, us):
        self.tt_session_us = int(us)

    # ===== helpers =====
    def _node_get(self, node):
        if node not in self.per_node:
            self.per_node[node] = dict(tx_ok=0, tx_err=0, bits_ok=0, drops=0)
        return self.per_node[node]

    # ===== logging API =====
    def on_tx(self, frame, success, start_us, end_us, node, medium):
        air = max(0, end_us - start_us)
        if success:
            self.t_success += air
            self.tx_ok += 1
            n = self._node_get(node)
            n["tx_ok"] += 1
            n["bits_ok"] += frame.bits
        else:
            self.t_collision += air
            self.tx_err += 1
            n = self._node_get(node)
            n["tx_err"] += 1

        self.tx_rows.append([start_us, end_us, node, getattr(frame.prio, "name", str(frame.prio)),
                             frame.bits, getattr(frame, "kind", "DATA"), int(success)])

    def on_drop(self, node, frame, attempts):
        self.drops += 1
        self._node_get(node)["drops"] += 1

    def add_collision_time(self, us):
        self.t_collision += max(0, int(us))

    # Accept ("label", us) or (us) for compatibility with medium/PRS calls
    def add_control_time(self, *args):
        """
        Accepts:
          - add_control_time(us)
          - add_control_time(label, us)  # label is ignored
        """
        if not args:
            return
        if len(args) == 1:
            us = args[0]
        else:
            us = args[-1]
        try:
            us = int(us)
        except Exception:
            return
        self.t_control += max(0, us)

    def add_idle_time(self, us):
        self.t_idle += max(0, int(us))

    # ===== debug hook (used also for sessions) =====
    def debug(self, tag, **kv):
        t = self.sim.now()
        self.debug_rows.append([t, tag, dict(kv)])

        if tag == "SLAC_SEQ_START":
            node = kv.get("node")
            if node is not None:
                # If a session was active, close as timeout (unfinished)
                if node in self.sessions_active:
                    st = self.sessions_active.pop(node)
                    # unfinished -> timeout
                    self.sessions_log.append(dict(node=node, start_us=st, end_us=t,
                                                  duration_us=t - st, ok=0, timeout=1))
                # start new
                self.sessions_active[node] = t

        elif tag == "SLAC_DONE":
            node = kv.get("node")
            ok = int(kv.get("ok", 1))
            if node in self.sessions_active:
                st = self.sessions_active.pop(node)
                dur = t - st
                timeout = 1 if dur > self.tt_session_us else 0
                self.sessions_log.append(dict(node=node, start_us=st, end_us=t,
                                              duration_us=dur, ok=ok, timeout=timeout))
            else:
                # DONE without START (edge) — record as zero-duration session
                st = t
                self.sessions_log.append(dict(node=node, start_us=st, end_us=t,
                                              duration_us=0, ok=ok, timeout=0))

    # ===== finalize / summaries =====
    def summary(self, sim_time_us):
        # close any active sessions (timeout if unfinished by sim end)
        to_close = list(self.sessions_active.items())
        for node, st in to_close:
            dur = sim_time_us - st
            # sim end without DONE -> timeout
            self.sessions_log.append(dict(node=node, start_us=st, end_us=sim_time_us,
                                          duration_us=dur, ok=0, timeout=1))
            self.sessions_active.pop(node, None)

        T = max(1, sim_time_us)
        util = (self.t_success + self.t_collision) / T
        coll_ratio = self.t_collision / max(1, (self.t_success + self.t_collision))

        # sessions
        s_total = len(self.sessions_log)
        s_ok = sum(1 for s in self.sessions_log if s["ok"] and not s["timeout"])
        s_to = sum(1 for s in self.sessions_log if s["timeout"])
        s_ratio = (s_to / s_total) if s_total > 0 else 0.0

        return dict(
            throughput_mbps=(self._bits_ok_total()/T)*1e6/1e6,
            efficiency_eta=(self.t_success / max(1, (T - self.t_control))),
            utilization=util,
            collision_ratio=coll_ratio,
            drops=self.drops,
            timeouts=self.timeouts,   # (message-level legacy)
            session_total=s_total,
            session_success=s_ok,
            session_timeouts=s_to,
            session_timeout_ratio=s_ratio,
            tt_session_us=self.tt_session_us
        )

    def _bits_ok_total(self):
        return sum(v["bits_ok"] for v in self.per_node.values())

    # ===== dumps (csv/md) =====
    def dump(self):
        with open(os.path.join(self.out_dir, "tx_log.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["start_us","end_us","node","prio","bits","kind","success"])
            w.writerows(self.tx_rows)

        with open(os.path.join(self.out_dir, "debug.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_us","tag","kv"])
            for t, tag, kv in self.debug_rows:
                w.writerow([t, tag, kv])

        with open(os.path.join(self.out_dir, "sessions.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["node","start_us","end_us","duration_us","ok","timeout"])
            w.writeheader()
            for s in self.sessions_log:
                w.writerow(s)

    def dump_per_node(self, sim_time_us):
        with open(os.path.join(self.out_dir, "node_summary.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["node","tx_ok","tx_err","bits_ok","drops"])
            for node, v in sorted(self.per_node.items()):
                w.writerow([node, v["tx_ok"], v["tx_err"], v["bits_ok"], v["drops"]])

    def dump_summary_csv(self, s):
        with open(os.path.join(self.out_dir, "summary.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(s.keys()))
            w.writerow(list(s.values()))

    def write_report(self, s):
        path = os.path.join(self.out_dir, "report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Experiment Report\n\n")
            f.write("## Summary\n\n")
            for k in ["throughput_mbps","efficiency_eta","utilization","collision_ratio",
                      "drops","timeouts",
                      "session_total","session_success","session_timeouts","session_timeout_ratio","tt_session_us"]:
                if k in s:
                    f.write(f"- **{k}**: {s[k]}\n")
            f.write("\n## Health Checks\n\n")
            verdicts = []
            util = s.get("utilization", 0.0)
            coll = s.get("collision_ratio", 0.0)
            s_to_ratio = s.get("session_timeout_ratio", 0.0)
            if not (0.0 <= util <= 1.05): verdicts.append("FAIL: Util out of range")
            elif coll > 0.9: verdicts.append("FAIL: Collision too high")
            elif coll < 0.02: verdicts.append("WARN: Collision unusually low (check load)")
            if s_to_ratio > 0.2: verdicts.append(f"WARN: High SLAC timeouts ratio = {s_to_ratio:.2f}")
            if not verdicts:
                verdicts.append("OK")
            for v in verdicts:
                f.write(f"- {v}\n")

            # Embed plots (relative paths)
            f.write("\n## Plots\n\n")
            f.write("![Efficiency over time](efficiency_over_time.png)\n\n")
            f.write("![SLAC timeout ratio over time](timeout_over_time.png)\n")

    # ===== PNG plots =====
    def write_plots(self, sim_time_us, bins=50):
        """
        Save two PNGs into out_dir:
        - efficiency_over_time.png : success_airtime / (success + collision) per bin
        - timeout_over_time.png    : (# session timeouts ended in bin) / (# sessions ended in bin)
        """
        if bins <= 0:
            bins = 50
        T = max(1, sim_time_us)
        edges = [int(i * T / bins) for i in range(bins + 1)]
        mid_ts = [0.5 * (edges[i] + edges[i+1]) for i in range(bins)]

        # --- per-bin success and collision airtime from tx_rows ---
        succ = [0] * bins
        coll = [0] * bins
        for start_us, end_us, node, prio, bits, kind, success in self.tx_rows:
            s = int(start_us); e = int(end_us)
            if e <= s:
                continue
            # which bins?
            s_idx = min(bins - 1, max(0, int(math.floor(s * bins / T))))
            e_idx = min(bins - 1, max(0, int(math.floor((e - 1) * bins / T))))
            for bi in range(s_idx, e_idx + 1):
                b0 = edges[bi]; b1 = edges[bi + 1]
                overlap = max(0, min(e, b1) - max(s, b0))
                if overlap <= 0:
                    continue
                if success:
                    succ[bi] += overlap
                else:
                    coll[bi] += overlap

        eff = []
        for i in range(bins):
            denom = succ[i] + coll[i]
            eff.append((succ[i] / denom) if denom > 0 else 0.0)

        # --- per-bin SLAC timeout ratio from sessions (by end_us bin) ---
        ended = [0] * bins
        timed_out = [0] * bins
        for s in self.sessions_log:
            e = int(s["end_us"])
            bi = min(bins - 1, max(0, int(math.floor(e * bins / T))))
            ended[bi] += 1
            if s.get("timeout", 0):
                timed_out[bi] += 1

        to_ratio = []
        for i in range(bins):
            to_ratio.append((timed_out[i] / ended[i]) if ended[i] > 0 else 0.0)

        # --- Plot 1: Efficiency over time ---
        try:
            plt.figure(figsize=(8, 3.2))
            x = [t / 1e6 for t in mid_ts]  # seconds
            plt.plot(x, eff, linewidth=2)
            plt.xlabel("Time (s)")
            plt.ylabel("Efficiency (success / (success+collision))")
            plt.ylim(0, 1.0)
            plt.title("Efficiency over time")
            plt.grid(True, linewidth=0.4, alpha=0.5)
            plt.tight_layout()
            plt.savefig(os.path.join(self.out_dir, "efficiency_over_time.png"), dpi=120)
            plt.close()
        except Exception as e:
            with open(os.path.join(self.out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
                f.write(f"efficiency plot error: {e}\n")

        # --- Plot 2: SLAC Timeout ratio over time ---
        try:
            plt.figure(figsize=(8, 3.2))
            x = [t / 1e6 for t in mid_ts]
            plt.plot(x, to_ratio, linewidth=2)
            plt.xlabel("Time (s)")
            plt.ylabel("Timeout ratio (timeouts / ended sessions)")
            plt.ylim(0, 1.0)
            plt.title("SLAC Timeout ratio over time")
            plt.grid(True, linewidth=0.4, alpha=0.5)
            plt.tight_layout()
            plt.savefig(os.path.join(self.out_dir, "timeout_over_time.png"), dpi=120)
            plt.close()
        except Exception as e:
            with open(os.path.join(self.out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
                f.write(f"timeout plot error: {e}\n")
