"""
app_15118.py
============
역할
- ISO 15118/SLAC과 유사한 **트랜잭션 기반 트래픽**을 생성한다.
- DISCOVERY → MEAS → MATCH 단계와 각 단계의 **타임아웃/데드라인**을 시뮬레이션한다.
- 저우선 배경 트래픽(CAP0 등) 생성기도 제공한다.

주의
- 실제 메시지 포맷/상태머신을 단순화한 연구용 생성기이며, 시간 파라미터는 설정 파일로 조정한다.
"""

from .mac_hpgp import Priority, Frame  # 우선순위/프레임 타입

class App15118:
    def __init__(self, sim, mac, role="EV", timers:dict=None, metrics=None, app_id="default"):
        self.sim, self.mac, self.role = sim, mac, role                # 의존성
        self.timers = timers or {"DISCOVERY_TO":50_000, "MEAS_TO":60_000, "MATCH_TO":80_000}  # 타이머
        self.metrics = metrics                                        # 메트릭 핸들
        self.app_id = app_id                                          # 트랜잭션 식별자

    def start_slac(self, start_us=0):
        """SLAC 유사 트랜잭션을 start_us 시점부터 시작."""
        self.sim.at(start_us, self._send_discovery)

    def _send_discovery(self):
        """탐색 단계 프레임 송신 및 타임아웃 스케줄."""
        f = Frame(src=self.mac.id, dst="peer", bits=400*8, prio=Priority.CAP3, deadline_us=self.timers["DISCOVERY_TO"], kind="DISCOVERY", app_id=self.app_id)
        self.mac.enqueue(f)
        self.sim.at(self.timers["DISCOVERY_TO"], lambda: self.metrics.on_timeout(self.app_id, "DISCOVERY"))
        self.sim.at(20_000, self._send_measurement)  # 다음 단계 예약(예시)

    def _send_measurement(self):
        """측정 단계 프레임 및 타임아웃."""
        f = Frame(src=self.mac.id, dst="peer", bits=600*8, prio=Priority.CAP3, deadline_us=self.timers["MEAS_TO"], kind="MEAS", app_id=self.app_id)
        self.mac.enqueue(f)
        self.sim.at(self.timers["MEAS_TO"], lambda: self.metrics.on_timeout(self.app_id, "MEAS"))
        self.sim.at(20_000, self._send_match)

    def _send_match(self):
        """매칭 단계 프레임 및 타임아웃."""
        f = Frame(src=self.mac.id, dst="peer", bits=500*8, prio=Priority.CAP3, deadline_us=self.timers["MATCH_TO"], kind="MATCH", app_id=self.app_id)
        self.mac.enqueue(f)
        self.sim.at(self.timers["MATCH_TO"], lambda: self.metrics.on_timeout(self.app_id, "MATCH"))

    def start_background(self, rate_pps=0, bits=12000, prio=Priority.CAP0):
        """저우선 배경 트래픽 발생기(포아송이 아닌 등간격 단순 모델)."""
        if rate_pps<=0: return
        period = int(1e6/rate_pps)  # 평균 간격(us)
        def gen():
            f = Frame(src=self.mac.id, dst="peer", bits=bits, prio=prio, deadline_us=None, kind="BG", app_id=self.app_id)
            self.mac.enqueue(f)
            self.sim.at(period, gen)  # 다음 배경 프레임 예약
        self.sim.at(0, gen)
