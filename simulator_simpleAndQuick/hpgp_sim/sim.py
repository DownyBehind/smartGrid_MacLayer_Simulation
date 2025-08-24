"""
sim.py
======
역할
- 설정(JSON) 파일을 읽어 시뮬레이션 구성 요소를 조립하고 실행한다.
- 토폴로지에 따라 2노드(cp_point_to_point) 또는 N노드(shared_bus)를 구성한다.
- 실행 후 요약 메트릭을 반환하고, CSV 로그를 디스크에 저장한다.

주요 엔트리
- load_config(path): JSON 로더
- build_and_run(cfg_path, out_dir, seed): 시뮬레이터 구축/실행/요약
"""

import json, os                                   # 설정 로드/경로
from .utils import Sim                            # 시뮬레이터 코어
from .medium import Medium, BeaconScheduler, PRSManager  # 매체/비콘/PRS
from .channel import GEChannel                    # 채널
from .mac_hpgp import HPGPMac, Priority, Frame    # MAC/우선순위
from .app_15118 import App15118                   # 트래픽 생성기
from .metrics import Metrics                      # 메트릭

def load_config(path):
    """JSON 설정 로드."""
    with open(path, "r") as f:
        return json.load(f)

def build_and_run(cfg_path, out_dir="/mnt/data/out", seed=1):
    """설정을 읽고 시뮬레이션을 구축한 뒤 실행하고 요약을 반환한다."""
    cfg = load_config(cfg_path)                         # 1) 설정 읽기
    sim = Sim(seed=seed)                                # 2) 시뮬레이터 생성
    med = Medium(sim, topology=cfg["topology"])       # 3) 매체 생성(토폴로지 설정)

    # 메트릭을 먼저 생성/연결(비콘/PRS 제어 오버헤드 집계용)
    metrics = Metrics(sim, out_dir)                     # 4) 메트릭 핸들
    med.metrics = metrics

    # Stage-2 타이밍 구성: PRS/Beacon/IFS 등
    timing = cfg["mac"].get("timing", {})
    prs_cfg = timing.get("prs", {"symbols":3, "symbol_us":10})
    med.prs = PRSManager(sim, med,
                         prs_symbols=prs_cfg.get("symbols",3),
                         symbol_us=prs_cfg.get("symbol_us",10))
    beacon_cfg = timing.get("beacon", {"period_us":100000, "duration_us":2000})
    med.beacon = BeaconScheduler(sim, med,
                                 period_us=beacon_cfg.get("period_us",100000),
                                 duration_us=beacon_cfg.get("duration_us",2000))
    if timing.get("beacon_enable", True):
        med.beacon.start()

    # 채널 생성
    ch  = GEChannel(sim,
        p_bg=cfg["channel"]["p_bg"],
        p_bb=cfg["channel"]["p_bb"],
        per_good=cfg["channel"]["per_good"],
        per_bad=cfg["channel"]["per_bad"],
        step_us=cfg["channel"]["step_us"],
        periodic=cfg["channel"].get("periodic", None)
    )

    # === 공유 버스 모드: 노드 수(nodes)만큼 자동 구성 ===
    nodes = cfg.get("nodes", 2)                       # 기본 2
    if cfg["topology"] == "shared_bus":
        macs = []
        apps = []
        for i in range(nodes):
            node_id = f"N{i}"                         # 노드 ID
            mac = HPGPMac(sim, med, ch, node_id, cfg["mac"], metrics)  # MAC 생성/등록
            macs.append(mac)
            app = App15118(sim, mac, role="NODE", timers=cfg["traffic"]["slac_timers"], metrics=metrics, app_id=node_id)
            apps.append(app)
            # SLAC 시작 시점 시차 부여(혼잡 패턴 생성)
            app.start_slac(start_us=i*cfg["traffic"].get("slac_peer_offset_us", 5000))
            # 배경 트래픽 주입 (노드별 동일 부하)
            if cfg["traffic"]["background"]["rate_pps"]>0:
                app.start_background(rate_pps=cfg["traffic"]["background"]["rate_pps"],
                                     bits=cfg["traffic"]["background"]["bits"],
                                     prio=Priority[cfg["traffic"]["background"]["prio"]])

        sim_time_us = int(cfg["sim_time_s"] * 1e6)     # 실행 시간(us)
        sim.run(until=sim_time_us)                       # 실행
        s = metrics.summary(sim_time_us)                 # 요약 산출
        metrics.dump()                                   # CSV 저장
        metrics.dump_per_node(sim_time_us)               # 노드별 요약 저장
        return s, os.path.abspath(out_dir)

    # === 1:1(cp_point_to_point) 모드: EV–EVSE 2노드 구성 ===
    macA = HPGPMac(sim, med, ch, "EV",   cfg["mac"], metrics)  # EV
    macB = HPGPMac(sim, med, ch, "EVSE", cfg["mac"], metrics)  # EVSE

    appA = App15118(sim, macA, role="EV",   timers=cfg["traffic"]["slac_timers"], metrics=metrics, app_id="EV")
    appB = App15118(sim, macB, role="EVSE", timers=cfg["traffic"]["slac_timers"], metrics=metrics, app_id="EVSE")

    # SLAC 유사 트랜잭션 시작
    appA.start_slac(start_us=0)
    appB.start_slac(start_us=cfg["traffic"].get("slac_peer_offset_us", 5_000))

    # 배경 트래픽(선택)
    if cfg["traffic"]["background"]["rate_pps"]>0:
        appA.start_background(rate_pps=cfg["traffic"]["background"]["rate_pps"],
                              bits=cfg["traffic"]["background"]["bits"],
                              prio=Priority[cfg["traffic"]["background"]["prio"]])
        appB.start_background(rate_pps=cfg["traffic"]["background"]["rate_pps"],
                              bits=cfg["traffic"]["background"]["bits"],
                              prio=Priority[cfg["traffic"]["background"]["prio"]])

    sim_time_us = int(cfg["sim_time_s"] * 1e6)         # 실행 시간(us)
    sim.run(until=sim_time_us)                           # 시뮬레이션 실행
    s = metrics.summary(sim_time_us)                     # 요약 계산
    metrics.dump()                                       # 로그 저장
    metrics.dump_per_node(sim_time_us)                   # 노드별 요약 저장
    return s, os.path.abspath(out_dir)                   # 결과 반환
