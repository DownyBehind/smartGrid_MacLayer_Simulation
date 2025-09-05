"""
metrics.py
----------
- 기본 TX/충돌/제어/유휴 회계
- debug(tag, **kv) 로 모든 SLAC/DC 이벤트를 기록 (CSV로 덤프)
- write_plots(): 효율/시간, (필요시) 다른 PNG 생성
"""

import os, csv, math

# Headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class Metrics:
    def __init__(self, sim, out_dir):
        self.sim = sim
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        self.t_success = 0
        self.t_collision = 0
        self.t_control = 0
        self.t_idle = 0

        self.tx_ok = 0
        self.tx_err = 0
        self.drops = 0
        self.timeouts = 0

        self.per_node = {}

        self.tx_rows = []        # [start_us, end_us, node, prio, bits, kind, success]
        self.debug_rows = []     # [t_us, tag, kv]
        # (이 버전에선 per-frame deadline 미사용; 세션/주기 타임아웃은 debug로 기록)

        # 세션 타임아웃 파라미터(옵션)
        self.tt_session_us = 500_000
        self.sessions_active = {}
        self.sessions_log = []

    # ---- 외부에서 세션 타임아웃(us) 설정 가능 ----
    def set_session_timeout_us(self, us):
        self.tt_session_us = int(us)

    def _node_get(self, node):
        if node not in self.per_node:
            self.per_node[node] = dict(tx_ok=0, tx_err=0, bits_ok=0, drops=0)
        return self.per_node[node]

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

    # PRS/BEACON에서 ("PRS", duration) 형태로 호출하는 케이스를 허용
    def add_control_time(self, *args):
        if not args:
            return
        us = args[-1]
        try:
            us = int(us)
        except Exception:
            return
        self.t_control += max(0, us)

    def add_idle_time(self, us):
        self.t_idle += max(0, int(us))

    def debug(self, tag, **kv):
        t = self.sim.now()
        self.debug_rows.append([t, tag, dict(kv)])

        # SLAC 세션 추적 (선택)
        if tag == "SLAC_SEQ_START":
            node = kv.get("node")
            if node is not None:
                if node in self.sessions_active:
                    st = self.sessions_active.pop(node)
                    self.sessions_log.append(dict(node=node, start_us=st, end_us=t, duration_us=t-st, ok=0, timeout=1))
                self.sessions_active[node] = t

        elif tag == "SLAC_DONE":
            node = kv.get("node"); ok = int(kv.get("ok", 1))
            if node in self.sessions_active:
                st = self.sessions_active.pop(node)
                dur = t - st
                timeout = 1 if dur > self.tt_session_us else 0
                self.sessions_log.append(dict(node=node, start_us=st, end_us=t, duration_us=dur, ok=ok, timeout=timeout))
            else:
                self.sessions_log.append(dict(node=node, start_us=t, end_us=t, duration_us=0, ok=ok, timeout=0))

    def summary(self, sim_time_us):
        # 미완료 세션 닫기
        to_close = list(self.sessions_active.items())
        for node, st in to_close:
            dur = sim_time_us - st
            self.sessions_log.append(dict(node=node, start_us=st, end_us=sim_time_us, duration_us=dur, ok=0, timeout=1))
            self.sessions_active.pop(node, None)

        T = max(1, sim_time_us)
        util = (self.t_success + self.t_collision) / T
        coll_ratio = self.t_collision / max(1, (self.t_success + self.t_collision))

        s_total = len(self.sessions_log)
        s_ok = sum(1 for s in self.sessions_log if s["ok"] and not s["timeout"])
        s_to = sum(1 for s in self.sessions_log if s["timeout"])

        return dict(
            throughput_mbps=(self._bits_ok_total()/T)*1e6/1e6,
            efficiency_eta=(self.t_success / max(1, (T - self.t_control))),
            utilization=util,
            collision_ratio=coll_ratio,
            drops=self.drops,
            timeouts=self.timeouts,
            session_total=s_total,
            session_success=s_ok,
            session_timeouts=s_to,
            tt_session_us=self.tt_session_us
        )

    def _bits_ok_total(self):
        return sum(v["bits_ok"] for v in self.per_node.values())

    # ---- 덤프 ----
    def dump(self):
        with open(os.path.join(self.out_dir, "tx_log.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["start_us","end_us","node","prio","bits","kind","success"]); w.writerows(self.tx_rows)
        with open(os.path.join(self.out_dir, "debug.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["t_us","tag","kv"])
            for t, tag, kv in self.debug_rows:
                w.writerow([t, tag, kv])
        with open(os.path.join(self.out_dir, "sessions.csv"), "w", newline="") as f:
            cols=["node","start_us","end_us","duration_us","ok","timeout"]
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
            for s in self.sessions_log: w.writerow(s)

    def dump_per_node(self, sim_time_us):
        with open(os.path.join(self.out_dir, "node_summary.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["node","tx_ok","tx_err","bits_ok","drops"])
            for node, v in sorted(self.per_node.items()):
                w.writerow([node, v["tx_ok"], v["tx_err"], v["bits_ok"], v["drops"]])

    def dump_summary_csv(self, s):
        with open(os.path.join(self.out_dir, "summary.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(list(s.keys())); w.writerow(list(s.values()))

    def write_report(self, s):
        path = os.path.join(self.out_dir, "report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Experiment Report\n\n")
            f.write("## Summary\n\n")
            for k in ["throughput_mbps","efficiency_eta","utilization","collision_ratio","drops","timeouts",
                      "session_total","session_success","session_timeouts","tt_session_us"]:
                if k in s: f.write(f"- **{k}**: {s[k]}\n")

    # ---- 간단 효율 시계열 PNG (옵션) ----
    def write_plots(self, sim_time_us, bins=50):
        # 성공/충돌 에어타임으로 효율 추정
        if bins <= 0: bins = 50
        T = max(1, sim_time_us)
        edges = [int(i*T/bins) for i in range(bins+1)]
        mid   = [0.5*(edges[i]+edges[i+1]) for i in range(bins)]

        succ = [0]*bins; coll = [0]*bins
        for s_us, e_us, node, prio, bits, kind, ok in self.tx_rows:
            s = int(s_us); e = int(e_us); 
            if e<=s: continue
            s_idx = min(bins-1, max(0, int(s*bins/T)))
            e_idx = min(bins-1, max(0, int((e-1)*bins/T)))
            for bi in range(s_idx, e_idx+1):
                b0, b1 = edges[bi], edges[bi+1]
                ov = max(0, min(e, b1) - max(s, b0))
                if ov <= 0: continue
                if ok: succ[bi]+=ov
                else:  coll[bi]+=ov

        eff = [(succ[i]/(succ[i]+coll[i]) if (succ[i]+coll[i])>0 else 0.0) for i in range(bins)]
        try:
            plt.figure(figsize=(8,3.2))
            x = [t/1e6 for t in mid]
            plt.plot(x, eff, linewidth=2)
            plt.xlabel("Time (s)"); plt.ylabel("Efficiency"); plt.ylim(0,1.0); plt.title("Efficiency over time"); plt.grid(True, lw=0.4, alpha=0.5)
            plt.tight_layout(); plt.savefig(os.path.join(self.out_dir, "efficiency_over_time.png"), dpi=120); plt.close()
        except Exception as e:
            with open(os.path.join(self.out_dir, "plot_error.log"), "a", encoding="utf-8") as f:
                f.write(f"efficiency plot error: {e}\n")
