"""
mac_hpgp.py
===========
역할
- HomePlug Green PHY(HPGP) MAC의 핵심 동작을 간이 모델로 구현한다.
- **DC/BPC**(Deferral/Backoff Procedure Counter) 기반의 '지연 유발 CW 증가'를 반영한다.
- **CAP0~3 + PRS** 우선순위 해석으로 긴급 트래픽 선점을 모델링한다.
- 슬롯 시간(σ), 백오프 단계(stage), CW_i, 재전송, 충돌 처리 로직을 포함한다.
- shared_bus 모드에서는 동일 시각 경쟁 시 Medium이 승자를 선정하고 동률은 충돌로 처리한다.

주의
- 실제 IEEE 1901/HPGP 전체 규격을 단순화한 연구용 모델이므로, 파라미터 튜닝이 중요하다.
"""

import math                                  # 에어타임 계산
from enum import Enum                        # 우선순위 열거형
from dataclasses import dataclass            # 프레임 기록용
from .utils import Sim                       # 시뮬레이터
from .medium import Medium                   # 매체
from .channel import GEChannel               # 채널

class Priority(Enum):
    CAP0=0; CAP1=1; CAP2=2; CAP3=3          # 우선순위(숫자 클수록 높음)

@dataclass
class Frame:
    src: str                                 # 송신 노드 ID
    dst: str                                 # 수신 노드 ID(데모에서는 미사용)
    bits: int                                # 프레임 길이(bit)
    prio: Priority                           # 프레임 우선순위(CAP)
    deadline_us: int|None=None               # 데드라인(us)
    born_t: int=0                            # 생성 시각(us)
    kind: str="DATA"                         # 프레임 종류(예: SLAC 단계)
    app_id: str="default"                    # 트랜잭션/앱 식별자

class HPGPMac:
    def __init__(self, sim:Sim, medium:Medium, channel:GEChannel, node_id:str, params:dict, metrics):
        # 의존성/상태 초기화
        self.sim, self.medium, self.ch = sim, medium, channel
        self.id = node_id                    # 노드 식별자
        self.p = params                      # MAC 파라미터(W0, m, sigma_us 등)
        self.metrics = metrics               # 지표 수집기
        self.stage = 0                       # 백오프 단계 i
        self.BC = 0                          # 백오프 카운터
        self.DC = 0                          # 지연 카운터(매체 busy 시 증가)
        self.BPC = 0                         # 백오프 절차 카운터(여기선 예시로만 증가)
        self.tx_queue:list[Frame] = []       # 송신 큐
        self.medium.subscribe(self)          # 매체에 등록
        self.last_per_t = self.sim.now()     # 채널 PER 질의 기준 시각
        self.pending_tx = None               # 진행 중 전송(미사용)
        self.sim.at(self.slot_time(), self._tick)  # 첫 틱 예약

    # 도우미
    def CW(self):
        """현재 단계의 CW 크기(CW_i) 계산."""
        W0, m, CWmax = self.p["W0"], self.p["m"], self.p["CWmax"]
        return min(W0*(2**self.stage), CWmax)
    def slot_time(self): return self.p["sigma_us"]   # 슬롯 시간 σ(us)
    def rate_bps(self): return self.p["phy_bps"]     # PHY 비트레이트
    def head_prio(self):
        """큐 헤드 프레임의 우선순위 반환(없으면 CAP0)."""
        return self.tx_queue[0].prio if self.tx_queue else Priority.CAP0

    # 외부 API
    def enqueue(self, fr:Frame):
        """프레임을 큐에 삽입."""
        fr.born_t = self.sim.now()
        self.tx_queue.append(fr)

    def ready_now(self):
        """지금 당장 전송 가능? (큐 있음, BC=0, 매체 유휴)"""
        return self.tx_queue and self.BC==0 and self.medium.is_idle()

    # 핵심 틱 루프
    def _tick(self):
        # 1) 트래픽 없으면 다음 틱으로
        if not self.tx_queue:
            self.sim.at(self.slot_time(), self._tick)
            return

        # 2) 매체 busy → DC 증가 및 임계 시 단계 상승(HPGP 고유 동작)
        if not self.medium.is_idle():
            self.DC += 1
            idx = min(self.stage, len(self.p["DC_thresh"])-1)  # 단계별 임계 인덱스
            if self.DC >= self.p["DC_thresh"][idx]:
                self.stage = min(self.stage+1, self.p["m"])    # 충돌 없어도 CW 확장
                self.DC = 0
            self.sim.at(self.slot_time(), self._tick)
            return

        # 3) 유휴이면 BC 없을 때 샘플링
        if self.BC == 0:
            self.BC = int(self.sim.rng.randrange(0, self.CW()))
        # 4) 카운트다운
        if self.BC>0:
            self.BC -= 1
            self.sim.at(self.slot_time(), self._tick)
            return

        # 5) 공유 버스 모드의 경쟁 해결(PRS/동률 충돌)
        if self.medium.topology == "shared_bus":
            cands = []
            for m in self.medium.listeners:
                if m.tx_queue and m.BC==0 and self.medium.is_idle():
                    fr = m._select_head()           # 헤드 프레임 미리 확인
                    m.tx_queue.insert(0, fr)        # 다시 되돌려놓기
                    air_time = math.ceil(fr.bits / (m.rate_bps()/1e6))
                    cands.append((m, fr, air_time))
            winner, losers = self.medium.request_tx_shared(cands)
            if winner is None and cands:
                # 최고 CAP 동률 → 충돌로 처리
                air_time = max(a for _,_,a in cands)
                self.medium.start_tx(self.id, air_time)
                def end_coll():
                    self.medium.end_tx()
                    for (m, fr, a) in cands:
                        m._on_tx_done(False, fr, self.sim.now()-air_time, air_time)  # 모두 실패
                    self.sim.at(self.slot_time(), self._tick)
                self.sim.at(air_time, end_coll)
                return
            elif winner is not None:
                if winner is not self:
                    # 승자가 내가 아니면 재백오프
                    self.BC = int(self.sim.rng.randrange(0, self.CW()))
                    self.sim.at(self.slot_time(), self._tick)
                    return
                # 승자가 나이면 아래 송신으로 진행

        # 6) 1:1(PR S 비교) 또는 shared_bus 승자: 실제 송신
        f = self._select_head()                         # 헤드 프레임 선택(우선순위 우선)
        air_time = math.ceil(f.bits / (self.rate_bps()/1e6))  # 에어타임(us)
        self.medium.start_tx(self.id, air_time)         # 매체 점유 시작
        start_t = self.sim.now()                        # 시작 시각 기록

        def end_tx():
            self.medium.end_tx()                        # 점유 해제
            per = self.ch.per(self.last_per_t, self.sim.rng) # 채널 PER 조회
            self.last_per_t = self.sim.now()            # PER 기준 시각 갱신
            success = (self.sim.rng.random()>per)       # 성공 여부
            self._on_tx_done(success, f, start_t, air_time)  # 상태 업데이트/지표 기록
            self.sim.at(self.slot_time(), self._tick)   # 다음 틱 예약

        self.sim.at(air_time, end_tx)                   # 전송 종료 이벤트 스케줄

    def _select_head(self):
        """큐에서 우선순위(CAP) 높은 프레임을 먼저, 동순위는 FIFO로 선택."""
        self.tx_queue.sort(key=lambda fr:(fr.prio.value, -fr.born_t), reverse=True)
        return self.tx_queue.pop(0)

    def _on_tx_done(self, success, frame:Frame, start_t=None, air_time=None):
        """전송 종료 후 MAC 상태 갱신 및 메트릭 기록."""
        if success:
            self.stage = 0; self.DC = 0; self.BPC = 0; self.BC = 0  # 성공 시 리셋
        else:
            self.stage = min(self.stage+1, self.p["m"])             # 실패 시 단계 상승
            self.BPC += 1
            self.tx_queue.insert(0, frame)                          # 재전송을 위해 헤드에 삽입
            self.BC = int(self.sim.rng.randrange(0, self.CW()))     # 새로운 백오프 샘플

        if start_t is not None:
            end_t = start_t + (air_time or 0)                       # 종료 시각
            self.metrics.on_tx(frame, success, start_t, end_t, self.id, self.medium)  # 로그 기록
