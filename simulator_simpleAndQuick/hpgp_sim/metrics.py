"""
metrics.py
==========
역할
- 시뮬레이션 결과를 수집/요약/저장한다.
- 프레임 단위 TX 로그, 데드라인 hit/miss, 상위계층 타임아웃, 채널 활용도(η), 처리율, 퍼센타일 지연을 계산한다.

출력
- tx_log.csv     : 전송 기록(시작/종료, 우선순위, 길이, 성공여부 등)
- deadlines.csv  : 데드라인 기록(생성/종료 시각, 데드라인, hit=1/miss=0)
- timeouts.csv   : 상위계층 타임아웃 발생 시각
"""

import math, statistics, csv, json, os  # 통계/파일 입출력

class Metrics:
    def __init__(self, sim, out_dir):
        self.sim = sim                               # 시뮬레이터
        self.out_dir = out_dir                       # 출력 디렉터리
        os.makedirs(out_dir, exist_ok=True)          # 폴더 생성
        self.tx_log = []                             # TX 로그 레코드
        self.deadlines = []                          # 데드라인 레코드
        self.timeouts = []                           # 타임아웃 이벤트
        self.busy_time = 0                           # 매체 점유 누적 시간
        self.last_busy_mark = None                   # (미사용) 세밀 회계용
        self.frames_in_flight = 0                    # (미사용) 동시 전송 추적

    def on_tx(self, frame, success, start_t, end_t, node_id, medium):
        """프레임 전송 결과를 기록하고, 채널 점유 시간(에어타임)을 누적."""
        self.busy_time += max(0, end_t-start_t)      # 점유 시간 누적
        record = dict(t_start=start_t, t_end=end_t, node=node_id, prio=frame.prio.name,
                      bits=frame.bits, kind=frame.kind, app_id=frame.app_id, success=int(success))
        self.tx_log.append(record)                   # TX 로그 추가
        if frame.deadline_us is not None:           # 데드라인 평가
            miss = int((end_t - frame.born_t) > frame.deadline_us)
            self.deadlines.append((frame.app_id, frame.kind, frame.born_t, end_t, frame.deadline_us, 1-miss))

    def on_timeout(self, app_id, stage):
        """상위계층(애플리케이션) 타임아웃 기록."""
        self.timeouts.append((app_id, stage, self.sim.now()))

    def summary(self, sim_time_us):
        """요약 메트릭 계산."""
        bits_ok = sum(r["bits"] for r in self.tx_log if r["success"]==1)   # 성공 비트 합
        eta = self.busy_time / max(1, sim_time_us)                         # 채널 활용도
        delays = [ (r["t_end"]-r["t_start"]) for r in self.tx_log if r["success"]==1 ]  # TX 지연(매체 점유)
        # e2e 지연(간이): 프레임 생성시각 대비 종료시각 차이
        e2e_delays = []
        for r in self.tx_log:
            if r["success"]!=1: 
                continue
            # deadlines 테이블에서 같은 app_id/kind의 born_t를 찾거나, 없으면 t_start 사용
            born_t = None
            for d in self.deadlines:
                if d[0]==r["app_id"] and d[1]==r["kind"]:
                    born_t = d[2]; break
            e2e_delays.append((r["t_end"]-(born_t if born_t is not None else r["t_start"])))

        # 퍼센타일(표본 수에 따라 근사)
        p95 = None
        p999 = None
        if e2e_delays:
            ed = sorted(e2e_delays)
            p95  = ed[int(max(0, min(len(ed)-1, 0.95*len(ed)-1)))]
            p999 = ed[-1] if len(ed)<1000 else ed[int(0.999*len(ed))-1]

        dmr = 1 - (sum(d[5] for d in self.deadlines)/max(1,len(self.deadlines)))  # 데드라인 미스 비율

        return dict(
            sim_time_us=sim_time_us,
            throughput_mbps= (bits_ok/sim_time_us) if sim_time_us>0 else 0.0,
            utilization_eta= eta,
            n_tx=len(self.tx_log),
            n_ok=sum(1 for r in self.tx_log if r["success"]==1),
            n_deadline=len(self.deadlines),
            deadline_miss_ratio= dmr,
            p95_delay_us=p95,
            p999_delay_us=p999,
            timeouts=len(self.timeouts)
        )

    def dump(self):
        """CSV 파일로 로그를 저장."""
        with open(os.path.join(self.out_dir,"tx_log.csv"),"w", newline="") as f:
            w=csv.DictWriter(f, fieldnames=self.tx_log[0].keys() if self.tx_log else [])
            if self.tx_log: w.writeheader()
            for r in self.tx_log: w.writerow(r)
        with open(os.path.join(self.out_dir,"deadlines.csv"),"w", newline="") as f:
            w=csv.writer(f); w.writerow(["app_id","kind","born_t","end_t","deadline_us","hit"])
            for d in self.deadlines: w.writerow(d)
        with open(os.path.join(self.out_dir,"timeouts.csv"),"w", newline="") as f:
            w=csv.writer(f); w.writerow(["app_id","stage","t_us"])
            for d in self.timeouts: w.writerow(d)
