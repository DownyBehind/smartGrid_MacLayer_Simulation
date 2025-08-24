"""
medium.py
=========
역할
- 공유 매체(전력선) 모델: 점유 상태, 전송 시작/종료, 승자 결정 규칙(공유버스) 제공
- Stage-2: Beacon 스케줄러, PRS(우선순위 해상) 타이밍 포함
- Metrics 연동: 제어 오버헤드(BEACON/PRS) airtime 집계 지원

구성
- Medium: 매체 상태, 구독 MAC 목록, 승자 결정(request_tx_shared)
- BeaconScheduler: 주기적 비콘으로 매체 점유(제어 오버헤드로 기록)
- PRSManager: PRS 심볼 시간만큼 매체 점유 후 승자 결정
"""

from typing import List, Tuple, Optional

class Medium:
    def __init__(self, sim, topology: str = "cp_point_to_point"):
        self.sim = sim
        self.topology = topology           # "cp_point_to_point" | "shared_bus"
        self.tx_owner = None               # 현재 전송 소유 MAC의 ID
        self.ongoing = []                  # 진행 중 전송(진단용)
        self.last_end_t = 0                # 마지막 전송 종료 시각(us)
        self.listeners: List = []          # 등록된 MAC 객체들
        self.metrics = None                # Metrics 핸들(선택)

        # Stage-2 구성요소(심볼릭; sim.py에서 주입)
        self.beacon = None                 # BeaconScheduler
        self.prs = None                    # PRSManager

    # ---- 공용 API ----
    def subscribe(self, mac):
        """MAC가 매체에 자신을 등록(경합 후보 검색에서 사용)."""
        self.listeners.append(mac)

    def is_idle(self) -> bool:
        """매체가 유휴 상태인가?"""
        return self.tx_owner is None

    def start_tx(self, owner_id: str, duration_us: int):
        """매체 점유 시작. 유휴 상태가 아니면 예외."""
        if not self.is_idle():
            raise RuntimeError("Medium busy")
        self.tx_owner = owner_id
        self.ongoing.append((owner_id, self.sim.now(), int(duration_us)))

    def end_tx(self):
        """매체 점유 종료."""
        self.tx_owner = None
        self.ongoing.clear()
        self.last_end_t = self.sim.now()

    def request_tx_shared(self, contenders: List[Tuple[object, object, int]]):
        """
        공유버스에서 동시 경쟁 후보들 중 승자 결정.
        contenders: [(mac, frame, airtime_us), ...]

        규칙:
        - 가장 높은 CAP 우선순위(frame.prio.value) 집합만 남김
        - 동순위 후보가 2개 이상이면 '충돌(None)'로 처리하여 호출측 로직에 위임
        - 단일 후보면 그 MAC이 승자
        """
        if not contenders:
            return None, []

        max_prio = max(fr.prio.value for (_, fr, _) in contenders)
        same = [(m, fr, a) for (m, fr, a) in contenders if fr.prio.value == max_prio]

        if len(same) >= 2:
            # 동순위 >=2 → 충돌 유도(호출 측에서 airtime 점유/실패처리)
            return None, [x[0] for x in same]
        else:
            winner_mac = same[0][0]
            losers = [m for (m, fr, a) in contenders if m is not winner_mac]
            return winner_mac, losers


# === Stage-2: Beacon scheduling ===
class BeaconScheduler:
    """주기적 비콘 트래픽을 매체에 주입하여 점유 시간을 강제한다."""
    def __init__(self, sim, medium: Medium, period_us=100_000, duration_us=2_000):
        self.sim, self.medium = sim, medium
        self.period_us = int(period_us)
        self.duration_us = int(duration_us)
        self.enabled = False

    def start(self):
        self.enabled = True
        self._schedule_next(self.sim.now())

    def _schedule_next(self, from_t):
        if not self.enabled:
            return
        # 다음 주기 시점을 계산하여 상대 지연으로 예약
        now = self.sim.now()
        t0 = from_t + (self.period_us - (from_t % self.period_us))
        delay = max(0, t0 - now)

        def begin():
            if not self.enabled:
                return
            if self.medium.is_idle():
                # 비콘 점유 시작
                self.medium.start_tx("BEACON", self.duration_us)
                # 제어 오버헤드 회계
                if getattr(self.medium, 'metrics', None) is not None:
                    self.medium.metrics.add_control_time("BEACON", self.duration_us)
                # 종료 예약
                self.sim.at(self.duration_us, end)
            else:
                # 바쁘면 다음 주기 시도
                self._schedule_next(self.sim.now() + self.period_us)

        def end():
            self.medium.end_tx()
            self._schedule_next(self.sim.now())

        self.sim.at(delay, begin)


# === Stage-2: PRS handshake timing ===
class PRSManager:
    """PRS(우선순위 해상) 단계의 시간 점유를 모델링."""
    def __init__(self, sim, medium: Medium, prs_symbols=3, symbol_us=10):
        self.sim, self.medium = sim, medium
        self.prs_symbols = int(prs_symbols)
        self.symbol_us = int(symbol_us)
        self.in_progress = False

    def run(self, contenders, choose_fn):
        """
        PRS를 실행하고 끝난 후 콜백으로 승자를 반환한다.
        contenders: [(mac, frame, airtime)]
        choose_fn: function(winner_mac or None, losers_list)
        """
        # 이미 PRS 중이거나 매체가 바쁘면 약간 지연 후 재시도(충돌 콜백 즉시 호출 X)
        if self.in_progress or not contenders or not self.medium.is_idle():
            self.sim.at(self.symbol_us, lambda: self.run(contenders, choose_fn))
            return

        duration = self.prs_symbols * self.symbol_us
        self.in_progress = True
        self.medium.start_tx("PRS", duration)
        # 제어 오버헤드 회계
        if getattr(self.medium, 'metrics', None) is not None:
            self.medium.metrics.add_control_time("PRS", duration)

        def end_prs():
            self.medium.end_tx()
            self.in_progress = False
            # 승자/패자 판정
            winner, losers = self.medium.request_tx_shared(contenders)
            choose_fn(winner, losers)

        self.sim.at(duration, end_prs)
