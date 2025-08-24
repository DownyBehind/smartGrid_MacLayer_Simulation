"""
metrics.py
==========
역할
- 시뮬레이션 결과를 수집/요약/저장
- 효율 분해(T_success/T_collision/T_idle/T_control) 및 Drop, Deadline Miss 집계

정의
- T_success: 성공한 데이터 전송 airtime 합
- T_collision: 경합 충돌 airtime 합(한 번만 가산)
- T_control: Beacon/PRS 등 제어 오버헤드 airtime 합
- T_idle: 전체시간 - (T_success + T_collision + T_control)
- 효율 η = T_success / (T_success + T_collision + T_idle) = T_success / (전체 - T_control)
"""

import csv, os

class Metrics:
    def __init__(self, sim, out_dir):
        self.sim = sim
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        self.tx_log = []              # per-frame TX 기록
        self.deadlines = []           # (app_id, kind, born, end, deadline_us, hit)
        self.timeouts = []            # (app_id, stage, t_us)

        # 효율 분해
        self.t_success_us = 0
        self.t_collision_us = 0
        self.t_control_us = 0

        # 드롭 집계
        self.drops = []               # (node, app_id, kind, attempts, born_t, drop_t)

    # ---- 시간 회계 ----
    def add_collision_time(self, dt_us):
        self.t_collision_us += max(0, int(dt_us))

    def add_control_time(self, kind, dt_us):
        self.t_control_us += max(0, int(dt_us))

    # ---- 이벤트 ----
    def on_tx(self, frame, success, start_t, end_t, node_id, medium):
        air = max(0, end_t - start_t)
        if success:
            self.t_success_us += air
        self.tx_log.append(dict(
            t_start=start_t, t_end=end_t, node=node_id, prio=frame.prio.name,
            bits=frame.bits, kind=frame.kind, app_id=frame.app_id, success=int(success),
            air_us=air
        ))
        if frame.deadline_us is not None:
            miss = int((end_t - frame.born_t) > frame.deadline_us)
            self.deadlines.append((frame.app_id, frame.kind, frame.born_t, end_t, frame.deadline_us, 1-miss))

    def on_timeout(self, app_id, stage):
        self.timeouts.append((app_id, stage, self.sim.now()))

    def on_drop(self, node_id, frame, attempts):
        self.drops.append((node_id, frame.app_id, frame.kind, attempts, frame.born_t, self.sim.now()))

    # ---- 요약/저장 ----
    def summary(self, sim_time_us):
        bits_ok = sum(r["bits"] for r in self.tx_log if r["success"]==1)
        denom = max(1, sim_time_us - self.t_control_us)
        eta = self.t_success_us / denom
        dmr = 1 - (sum(d[5] for d in self.deadlines)/max(1,len(self.deadlines)))
        e2e = [r["t_end"]-r["t_start"] for r in self.tx_log if r["success"]==1]
        p95  = e2e[int(0.95*len(e2e))-1] if e2e else None
        p999 = e2e[-1] if e2e else None
        return dict(
            sim_time_us=sim_time_us,
            throughput_mbps=(bits_ok/sim_time_us) if sim_time_us>0 else 0.0,
            efficiency_eta=eta,
            t_success_us=self.t_success_us,
            t_collision_us=self.t_collision_us,
            t_control_us=self.t_control_us,
            t_idle_us=max(0, sim_time_us - (self.t_success_us + self.t_collision_us + self.t_control_us)),
            n_tx=len(self.tx_log),
            n_ok=sum(1 for r in self.tx_log if r["success"]==1),
            n_deadline=len(self.deadlines),
            deadline_miss_ratio=dmr,
            p95_delay_us=p95,
            p999_delay_us=p999,
            timeouts=len(self.timeouts),
            drops=len(self.drops)
        )

    def dump(self):
        with open(os.path.join(self.out_dir,"tx_log.csv"),"w", newline="") as f:
            if self.tx_log:
                w=csv.DictWriter(f, fieldnames=self.tx_log[0].keys()); w.writeheader()
                for r in self.tx_log: w.writerow(r)
        with open(os.path.join(self.out_dir,"deadlines.csv"),"w", newline="") as f:
            w=csv.writer(f); w.writerow(["app_id","kind","born_t","end_t","deadline_us","hit"])
            for d in self.deadlines: w.writerow(d)
        with open(os.path.join(self.out_dir,"timeouts.csv"),"w", newline="") as f:
            w=csv.writer(f); w.writerow(["app_id","stage","t_us"])
            for d in self.timeouts: w.writerow(d)
        with open(os.path.join(self.out_dir,"drops.csv"),"w", newline="") as f:
            w=csv.writer(f); w.writerow(["node","app_id","kind","attempts","born_t","drop_t"])
            for d in self.drops: w.writerow(d)

    def dump_per_node(self, sim_time_us):
        nodes = {}
        for r in self.tx_log:
            nd = nodes.setdefault(r["node"], {"bits_ok":0,"tx":0,"ok":0,"deadline_total":0,"deadline_hit":0,"drops":0})
            nd["tx"] += 1
            if r["success"]==1:
                nd["ok"] += 1
                nd["bits_ok"] += r["bits"]
        for (app_id, kind, born, end, ddl, hit) in self.deadlines:
            nd = nodes.setdefault(app_id, {"bits_ok":0,"tx":0,"ok":0,"deadline_total":0,"deadline_hit":0,"drops":0})
            nd["deadline_total"] += 1
            nd["deadline_hit"] += hit
        for (node, app_id, kind, attempts, born_t, drop_t) in self.drops:
            nd = nodes.setdefault(node, {"bits_ok":0,"tx":0,"ok":0,"deadline_total":0,"deadline_hit":0,"drops":0})
            nd["drops"] += 1

        path = os.path.join(self.out_dir, "node_summary.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["node","throughput_mbps","deadline_miss_ratio","tx","ok","drops"])
            for node, st in sorted(nodes.items()):
                thr = (st["bits_ok"]/sim_time_us) if sim_time_us>0 else 0.0
                dmr = 1.0 - (st["deadline_hit"]/st["deadline_total"]) if st["deadline_total"]>0 else 0.0
                w.writerow([node, thr, dmr, st["tx"], st["ok"], st["drops"]])
        return path
