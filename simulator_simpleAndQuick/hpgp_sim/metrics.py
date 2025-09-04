"""
metrics.py (session-aware + PNG plots + DC loop analysis)
- TX/충돌/데드라인 로깅(기존)
- SLAC 세션 추적 (세션 시작/종료/타임아웃)
- DC 루프 분석:
   * debug("DC_START", node=...)
   * TX kinds: "CD_REQ_<EVNODE>_<CID>", "CD_RSP_<EVNODE>_<CID>"
   * dc_entries.csv  : (node, start_us)
   * dc_cycles.csv   : (node, cid, start_us, end_us, latency_us, deadline_us, violation)
   * dc_timeline.png : x=시간(s), y=노드 index; DC 진입(초록 점), 주기 위반(빨간 점)
- summary.csv / node_summary.csv / report.md 유지
"""

import os, csv, math, re

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
        self.timeouts = 0  # (message-level; kept for backward compat)

        # per-node counters
        self.per_node = {}

        # logs (in-memory)
        # start_us, end_us, node, prio, bits, kind, success
        self.tx_rows = []
        # node, prio, kind, born_us, end_us, deadline_us, hit_or_miss
        self.deadline_rows = []
        # t_us, tag, kv
        self.debug_rows = []

        # SLAC session tracking
        self.tt_session_us = 500_000  # default 0.5 s (override via sim.py from config)
        self.sessions_active = {}     # node -> start_us
        self.sessions_log = []        # dict(node, start_us, end_us, duration_us, ok, timeout)

        # DC loop params (for analysis/labels)
        self.dc_deadline_us = 100_000
        self.dc_period_us   = 100_000

    # ===== param setters =====
    def set_session_timeout_us(self, us):
        self.tt_session_us = int(us)

    def set_dc_deadline_us(self, us):
        self.dc_deadline_us = int(us)

    def set_dc_period_us(self, us):
        self.dc_period_us = int(us)

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

        if getattr(frame, "deadline_us", None):
            born = getattr(frame, "born_t", start_us)
            miss = 1 if (end_us - born) > int(frame.deadline_us) else 0
            self.deadline_rows.append([node,
                                       getattr(frame.prio, "name", str(frame.prio)),
                                       getattr(frame, "kind", "DATA"),
                                       born, end_us, int(frame.deadline_us),
                                       "miss" if miss else "hit"])

    def on_drop(self, node, frame, attempts):
        self.drops += 1
        self._node_get(node)["drops"] += 1

    def add_collision_time(self, us):
        self.t_collision += max(0, int(us))

    # accept (us) or (label, us)
    def add_control_time(self, *args):
        if not args: return
        us = args[-1]
        try:
            us = int(us)
        except Exception:
            return
        self.t_control += max(0, us)

    def add_idle_time(self, us):
        self.t_idle += max(0, int(us))

    # ===== debug hook (sessions + dc start/cycle marks) =====
    def debug(self, tag, **kv):
        t = self.sim.now()
        self.debug_rows.append([t, tag, dict(kv)])

        if tag == "SLAC_SEQ_START":
            node = kv.get("node")
            if node is not None:
                if node in self.sessions_active:
                    st = self.sessions_active.pop(node)
                    self.sessions_log.append(dict(node=node, start_us=st, end_us=t,
                                                  duration_us=t - st, ok=0, timeout=1))
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
                st = t
                self.sessions_log.append(dict(node=node, start_us=st, end_us=t,
                                              duration_us=0, ok=ok, timeout=0))

        # DC_START / DC_CYCLE_START are just markers; analysis happens offline in write_plots()

    # ===== finalize / summaries =====
    def summary(self, sim_time_us):
        # close any active SLAC sessions
        to_close = list(self.sessions_active.items())
        for node, st in to_close:
            dur = sim_time_us - st
            self.sessions_log.append(dict(node=node, start_us=st, end_us=sim_time_us,
                                          duration_us=dur, ok=0, timeout=1))
            self.sessions_active.pop(node, None)

        T = max(1, sim_time_us)
        util = (self.t_success + self.t_collision) / T
        coll_ratio = self.t_collision / max(1, (self.t_success + self.t_collision))

        # legacy DMR from deadline_rows (kept for compatibility; you can ignore if using session timeouts)
        d_total = len(self.deadline_rows)
        d_miss = sum(1 for r in self.deadline_rows if r[-1] == "miss")
        dmr = (d_miss / d_total) if d_total > 0 else 0.0

        # sessions
        s_total = len(self.sessions_log)
        s_ok = sum(1 for s in self.sessions_log if s["ok"] and not s["timeout"])
        s_to = sum(1 for s in self.sessions_log if s["timeout"])

        return dict(
            throughput_mbps=(self._bits_ok_total()/T)*1e6/1e6,
            efficiency_eta=(self.t_success / max(1, (T - self.t_control))),
            utilization=util,
            collision_ratio=coll_ratio,
            deadline_miss_ratio=dmr,
            drops=self.drops,
            timeouts=self.timeouts,
            session_total=s_total,
            session_success=s_ok,
            session_timeouts=s_to,
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

        with open(os.path.join(self.out_dir, "deadlines.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["node","prio","kind","born_us","end_us","deadline_us","hit_or_miss"])
            w.writerows(self.deadline_rows)

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
                      "deadline_miss_ratio","drops","timeouts",
                      "session_total","session_success","session_timeouts","tt_session_us"]:
                if k in s:
                    f.write(f"- **{k}**: {s[k]}\n")
            f.write("\n## Health Checks\n\n")
            verdicts = []
            util = s.get("utilization", 0.0)
            dmr  = s.get("deadline_miss_ratio", 0.0)
            coll = s.get("collision_ratio", 0.0)
            s_to = s.get("session_timeouts", 0)
            if not (0.0 <= util <= 1.05): verdicts.append("FAIL: Util out of range")
            elif dmr > 0.2 or coll > 0.9: verdicts.append("FAIL: DMR/Collision too high")
            elif dmr > 0.05 or coll < 0.02: verdicts.append("WARN: DMR/Collision unusual")
            if s_to > 0: verdicts.append(f"WARN: {s_to} session timeouts")
            if not verdicts:
                verdicts.append("OK")
            for v in verdicts:
                f.write(f"- {v}\n")

            f.write("\n## Plots\n\n")
            f.write("![Efficiency over time](efficiency_over_time.png)\n\n")
            f.write("![Deadline Miss Ratio over time](dmr_over_time.png)\n\n")
            f.write("![DC start & violations](dc_timeline.png)\n")

    # ===== PNG plots (efficiency/DMR legacy + DC timeline) =====
    def write_plots(self, sim_time_us, bins=50):
        # legacy efficiency & dmr
        self._plot_efficiency(sim_time_us, bins)
        self._plot_dmr(sim_time_us, bins)
        # new DC timeline
        self._write_dc_csv_and_plot(sim_time_us)

    # --- helpers: legacy charts ---
    def _plot_efficiency(self, sim_time_us, bins):
        if bins <= 0: bins = 50
        T = max(1, sim_time_us)
        edges = [int(i * T / bins) for i in range(bins + 1)]
        mid_ts = [0.5 * (edges[i] + edges[i+1]) for i in range(bins)]

        succ = [0] * bins
        coll = [0] * bins
        for start_us, end_us, node, prio, bits, kind, success in self.tx_rows:
            s = int(start_us); e = int(end_us)
            if e <= s: continue
            s_idx = min(bins - 1, max(0, int(math.floor(s * bins / T))))
            e_idx = min(bins - 1, max(0, int(math.floor((e - 1) * bins / T))))
            for bi in range(s_idx, e_idx + 1):
                b0 = edges[bi]; b1 = edges[bi + 1]
                overlap = max(0, min(e, b1) - max(s, b0))
                if overlap <= 0: continue
                if success: succ[bi] += overlap
                else:       coll[bi] += overlap

        eff = []
        for i in range(bins):
            denom = succ[i] + coll[i]
            eff.append((succ[i] / denom) if denom > 0 else 0.0)

        try:
            plt.figure(figsize=(8, 3.2))
            x = [t / 1e6 for t in mid_ts]
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

    def _plot_dmr(self, sim_time_us, bins):
        if bins <= 0: bins = 50
        T = max(1, sim_time_us)
        edges = [int(i * T / bins) for i in range(bins + 1)]
        mid_ts = [0.5 * (edges[i] + edges[i+1]) for i in range(bins)]

        miss = [0] * bins
        with_deadline = [0] * bins
        for node, prio, kind, born_us, end_us, deadline_us, hit_or_miss in self.deadline_rows:
            e = int(end_us)
            bi = min(bins - 1, max(0, int(math.floor(e * bins / T))))
            with_deadline[bi] += 1
            if hit_or_miss == "miss":
                miss[bi] += 1

        dmr = []
        for i in range(bins):
            dmr.append((miss[i] / with_deadline[i]) if with_deadline[i] > 0 else 0.0)

        try:
            plt.figure(figsize=(8, 3.2))
            x = [t / 1e6 for t in mid_ts]
            plt.plot(x, dmr, linewidth=2)
            plt.xlabel("Time (s)")
            plt.ylabel("DMR (miss / total with deadline)")
            plt.ylim(0, 1.0)
            plt.title("Deadline Miss Ratio over time")
            plt.grid(True, linewidth=0.4, alpha=0.5)
            plt.tight_layout()
            plt.savefig(os.path.join(self.out_dir, "dmr_over_time.png"), dpi=120)
            plt.close()
        except Exception as e:
            with open(os.path.join(self.out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
                f.write(f"dmr plot error: {e}\n")

    # --- DC CSV/PNG ---
    def _write_dc_csv_and_plot(self, sim_time_us):
        # 1) DC entries (from debug rows)
        dc_entries = []  # (node, start_us)
        for t, tag, kv in self.debug_rows:
            if tag == "DC_START":
                node = kv.get("node")
                if node is not None:
                    dc_entries.append((node, t))

        # write dc_entries.csv
        try:
            with open(os.path.join(self.out_dir, "dc_entries.csv"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["node","dc_start_us"])
                for node, t in dc_entries:
                    w.writerow([node, t])
        except Exception:
            pass

        # 2) DC cycles: parse tx_rows kinds
        req_pat = re.compile(r"^CD_REQ_(?P<ev>[^_]+)_(?P<cid>\d+)$")
        rsp_pat = re.compile(r"^CD_RSP_(?P<ev>[^_]+)_(?P<cid>\d+)$")
        starts = {}   # (ev,cid) -> start_us
        ends   = {}   # (ev,cid) -> end_us

        for start_us, end_us, node, prio, bits, kind, success in self.tx_rows:
            m = req_pat.match(kind)
            if m:
                ev = m.group("ev"); cid = int(m.group("cid"))
                # use start_us of Req
                starts[(ev, cid)] = int(start_us)
                continue
            m = rsp_pat.match(kind)
            if m:
                ev = m.group("ev"); cid = int(m.group("cid"))
                # use end_us of Rsp
                ends[(ev, cid)] = int(end_us)
                continue

        # match & compute latencies
        cycles = []  # dict(node, cid, start_us, end_us, latency_us, deadline_us, violation)
        ddl = max(1, int(self.dc_deadline_us))
        for (ev, cid), s_us in starts.items():
            e_us = ends.get((ev, cid), None)
            if e_us is None:
                # no response seen; treat as open cycle (could mark as violation)
                continue
            lat = max(0, e_us - s_us)
            vio = 1 if lat > ddl else 0
            cycles.append(dict(node=ev, cid=cid, start_us=s_us, end_us=e_us,
                               latency_us=lat, deadline_us=ddl, violation=vio))

        # write dc_cycles.csv
        try:
            with open(os.path.join(self.out_dir, "dc_cycles.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["node","cid","start_us","end_us","latency_us","deadline_us","violation"])
                w.writeheader()
                for row in sorted(cycles, key=lambda x: (x["node"], x["cid"])):
                    w.writerow(row)
        except Exception:
            pass

        # 3) PNG: timeline with DC start (green) and violations (red)
        try:
            # collect all nodes
            nodes = sorted({n for n,_ in dc_entries} | {c["node"] for c in cycles})
            if not nodes:
                return
            idx = {n:i for i,n in enumerate(nodes)}  # y = index

            # data
            x_start = [t/1e6 for (_,t) in dc_entries]
            y_start = [idx[n] for (n,_) in dc_entries]

            x_vio = [c["end_us"]/1e6 for c in cycles if c["violation"]]
            y_vio = [idx[c["node"]] for c in cycles if c["violation"]]

            plt.figure(figsize=(9, 3.2))
            if x_start:
                plt.scatter(x_start, y_start, marker="o", label="DC start (after SLAC)")
            if x_vio:
                plt.scatter(x_vio, y_vio, marker="x", label=f"Period violations (> {self.dc_deadline_us/1000:.0f} ms)", color="red")

            plt.yticks(range(len(nodes)), nodes)
            plt.xlabel("Time (s)")
            plt.ylabel("Node")
            plt.title("DC entry & 100 ms period violations over time")
            plt.grid(True, linewidth=0.4, alpha=0.5)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(self.out_dir, "dc_timeline.png"), dpi=120)
            plt.close()
        except Exception as e:
            with open(os.path.join(self.out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
                f.write(f"dc_timeline plot error: {e}\n")
