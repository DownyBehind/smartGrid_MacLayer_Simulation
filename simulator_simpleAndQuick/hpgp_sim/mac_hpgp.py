"""
mac_hpgp.py
===========
역할
- HomePlug Green PHY(HPGP) MAC의 핵심 동작 간이 모델
- HPGP/IEEE1901 스타일의 **CAP별 CW 테이블**을 사용해 백오프 폭을 결정
- **BPC(Backoff Procedure Counter)**: 디퍼럴/실패 시 증가, 성공 시 0으로 리셋
- **DC(Deferral Counter)**: (논문 정합 옵션) BPC 단계별 초기값을 사용
- **CAP0~3 + PRS(우선순위 해상)** 타이밍, (옵션) CAP별 IFS 가중치
- Retry limit & Drop 집계 지원

주의
- PRS/IFS/Beacon 타이밍은 파라미터화 근사 모델
- 1901의 PRS 상세 절차(3 슬롯 타이브레이크)는 간략화
"""

import math
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from .utils import Sim                # 시뮬레이터
from .medium import Medium            # 매체
from .channel import GEChannel        # 채널

class Priority(Enum):
    CAP0=0; CAP1=1; CAP2=2; CAP3=3

@dataclass
class Frame:
    src: str
    dst: str
    bits: int
    prio: Priority
    deadline_us: Optional[int] = None
    born_t: int = 0
    kind: str = "DATA"
    app_id: str = "default"
    attempts: int = 0                 # 재시도 횟수

class HPGPMac:
    def __init__(self, sim:Sim, medium:Medium, channel:GEChannel, node_id:str, params:dict, metrics):
        self.sim, self.medium, self.ch = sim, medium, channel
        self.id = node_id
        self.p = params
        self.metrics = metrics

        # HPGP 절차 상태
        self.BC = 0                   # Backoff Counter
        self.DC = 0                   # Deferral Counter
        self.BPC = 0                  # Backoff Procedure Counter (CW 단계 인덱스)
        self.tx_queue:list[Frame] = []

        self.medium.subscribe(self)
        self.last_per_t = self.sim.now()
        self.pending_tx = None
        self.retry_limit = self.p.get('retry_limit', None)  # None이면 무제한

        # CAP별 CW 테이블(설정 없을 시 None)
        # 예시 기본(HPGP 근사): CA0/1: [8,16,32,64], CA2/3: [8,16,16,32]
        self.cw_table = self.p.get("cw_table", None)

        # (구 방식) 디퍼럴 임계: 누적이 임계 초과하면 단계 상승
        self.dc_thresh = self.p.get("DC_thresh", [2,3,4])

        # (신 방식) 논문 정합: BPC 단계별 DC 초기값 테이블
        # 존재 시 이를 우선 사용 (busy 슬롯마다 DC -= 1; DC<0 => BPC++, DC 재초기화)
        self.dc_init_table = self.p.get("dc_init_per_bpc", None)
        self.use_dc_init_mode = self.dc_init_table is not None

        if self.use_dc_init_mode:
            self.DC = self._dc_init_value(0)  # BPC=0 단계의 DC 초기값으로 설정

        # 첫 틱 예약
        self.sim.at(self.slot_time(), self._tick)

    # ---- 파라미터/도우미 ----
    def slot_time(self): 
        return int(self.p.get("sigma_us", 20))

    def rate_bps(self): 
        return int(self.p.get("phy_bps", 10_000_000))

    def head_prio(self):
        return self.tx_queue[0].prio if self.tx_queue else Priority.CAP0

    def ifs_us(self):
        """CAP별 IFS/MAIFS 시간(us). 논문 정합 시엔 모두 0으로 둘 것을 권장(PRS-only)."""
        tbl = self.p.get("ifs_us", {"CAP0":0,"CAP1":0,"CAP2":0,"CAP3":0})
        return int(tbl.get(self.head_prio().name, 0))

    def _cw_from_table(self) -> int:
        """
        CAP별 CW 테이블에서 현재 BPC에 해당하는 CW를 선택.
        - 테이블 길이를 넘어서는 BPC는 마지막 원소를 사용(>=마지막 단계 버킷).
        - 테이블이 없으면 None 반환.
        """
        if not self.cw_table:
            return None
        prio = self.head_prio().name  # "CAP0".."CAP3"
        arr = self.cw_table.get(prio, None)
        if not arr:
            return None
        idx = min(self.BPC, len(arr)-1)
        return int(arr[idx])

    def _cw_fallback(self) -> int:
        """
        테이블 미지정 시의 일반화 CW (802.11식 근사): W0 * 2^BPC, 상한 CWmax
        - HPGP와 완전 동일하진 않음. 연구 편의용 백업 경로.
        """
        W0 = int(self.p.get("W0", 16))
        CWmax = int(self.p.get("CWmax", 1024))
        cw = W0 * (2 ** self.BPC)
        return min(cw, CWmax)

    def CW(self) -> int:
        """현재 사용 CW 크기 산출(테이블 우선, 없으면 폴백)."""
        cw = self._cw_from_table()
        return cw if cw is not None else self._cw_fallback()

    def _dc_init_value(self, bpc:int) -> int:
        """BPC 단계별 DC 초기값을 반환. 테이블 길이를 넘으면 마지막 값을 사용."""
        arr = self.dc_init_table or [0,1,3,15]
        idx = min(max(bpc, 0), len(arr)-1)
        return int(arr[idx])

    def _cap_bpc_limit(self) -> int:
        """최대 BPC 단계 인덱스(0 기반). max_bpc=4이면 0..3."""
        return max(0, int(self.p.get("max_bpc", 4)) - 1)

    # ---- 외부 API ----
    def enqueue(self, fr:Frame):
        fr.born_t = self.sim.now()
        self.tx_queue.append(fr)

    # ---- 핵심 루프 ----
    def _tick(self):
        # 1) 큐 없음
        if not self.tx_queue:
            self.sim.at(self.slot_time(), self._tick)
            return

        # 2) 매체 busy 처리
        if not self.medium.is_idle():
            if self.use_dc_init_mode:
                # 논문 정합: busy마다 DC -= 1; DC<0면 단계 상승 및 DC 재초기화
                self.DC -= 1
                if self.DC < 0:
                    self.BPC = min(self.BPC + 1, self._cap_bpc_limit())
                    self.DC = self._dc_init_value(self.BPC)
                    # 단계가 바뀌면 CW도 바뀌므로 백오프 카운터 재샘플
                    self.BC = int(self.sim.rng.randrange(0, self.CW()))
            else:
                # 폴백: 누적 임계 기반
                self.DC += 1
                idx = min(self.BPC, len(self.dc_thresh)-1)
                if self.DC >= self.dc_thresh[idx]:
                    self.BPC += 1
                    self.DC = 0
            self.sim.at(self.slot_time(), self._tick)
            return

        # 3) 유휴면 BC 샘플/카운트다운
        if self.BC == 0:
            self.BC = int(self.sim.rng.randrange(0, self.CW()))
        if self.BC > 0:
            self.BC -= 1
            self.sim.at(self.slot_time(), self._tick)
            return

        # 4) IFS/MAIFS 보장: 마지막 종료 이후 필요한 IFS 확보
        need = self.ifs_us()
        if need > 0:
            idle_since = max(0, self.sim.now() - getattr(self.medium, 'last_end_t', 0))
            if idle_since < need:
                self.sim.at(need - idle_since, self._tick)
                return

        # 5) 공유 버스 경쟁 처리 (PRS 사용 시)
        if self.medium.topology == "shared_bus":
            cands = []
            for m in self.medium.listeners:
                if m.tx_queue and m.BC==0 and self.medium.is_idle():
                    fr = m._select_head()            # 헤드 프레임 미리 선택
                    m.tx_queue.insert(0, fr)         # 원위치
                    air_time = math.ceil(fr.bits / (m.rate_bps()/1e6))
                    cands.append((m, fr, air_time))

            # PRS 경로
            if hasattr(self.medium, "prs") and self.medium.prs is not None and cands:
                def after_prs(winner, losers):
                    # (가드) PRS 직후 다른 전송/비콘이 점유했을 수 있음
                    if winner is None:
                        if not self.medium.is_idle():
                            self.sim.at(self.slot_time(), self._tick)
                            return
                        air_time = max(a for _,_,a in cands)
                        try:
                            self.medium.start_tx(self.id, air_time)
                        except RuntimeError:
                            self.sim.at(self.slot_time(), self._tick)
                            return
                        # 충돌 airtime은 1회만 회계
                        if getattr(self.metrics, 'add_collision_time', None):
                            self.metrics.add_collision_time(air_time)
                        def end_coll():
                            self.medium.end_tx()
                            for (m, fr, a) in cands:
                                # 충돌은 '실패'로 취급 → 각 노드 BPC 증가 트리거는 _on_tx_done에서 수행
                                m._on_tx_done(False, fr, self.sim.now()-air_time, air_time)
                            self.sim.at(self.slot_time(), self._tick)
                        self.sim.at(air_time, end_coll)
                        return

                    if winner is not self:
                        # 패자: 재백오프
                        self.BC = int(self.sim.rng.randrange(0, self.CW()))
                        self.sim.at(self.slot_time(), self._tick)
                        return

                    # 승자: 실제 송신
                    self._transmit_head()
                self.medium.prs.run(cands, after_prs)
                return
            else:
                # PRS 미사용 폴백
                winner, losers = self.medium.request_tx_shared(cands)
                if winner is None and cands:
                    if not self.medium.is_idle():
                        self.sim.at(self.slot_time(), self._tick)
                        return
                    air_time = max(a for _,_,a in cands)
                    try:
                        self.medium.start_tx(self.id, air_time)
                    except RuntimeError:
                        self.sim.at(self.slot_time(), self._tick)
                        return
                    if getattr(self.metrics, 'add_collision_time', None):
                        self.metrics.add_collision_time(air_time)
                    def end_coll():
                        self.medium.end_tx()
                        for (m, fr, a) in cands:
                            m._on_tx_done(False, fr, self.sim.now()-air_time, air_time)
                        self.sim.at(self.slot_time(), self._tick)
                    self.sim.at(air_time, end_coll)
                    return
                elif winner is not None and winner is not self:
                    self.BC = int(self.sim.rng.randrange(0, self.CW()))
                    self.sim.at(self.slot_time(), self._tick)
                    return
                # else: 승자=나 → 전송

        # 6) 전송
        self._transmit_head()

    def _select_head(self):
        """우선순위(CAP) 먼저, 동순위는 FIFO(생성시각 역순 pop)"""
        self.tx_queue.sort(key=lambda fr: (fr.prio.value, -fr.born_t), reverse=True)
        return self.tx_queue.pop(0)

    def _transmit_head(self):
        f = self._select_head()
        air_time = math.ceil(f.bits / (self.rate_bps()/1e6))

        # 송신 시작
        self.medium.start_tx(self.id, air_time)
        start_t = self.sim.now()

        def end_tx():
            self.medium.end_tx()
            # 채널 PER 평가(프레임 오류)
            per = self.ch.per(self.last_per_t, self.sim.rng)
            self.last_per_t = self.sim.now()
            success = (self.sim.rng.random() > per)
            self._on_tx_done(success, f, start_t, air_time)
            self.sim.at(self.slot_time(), self._tick)

        self.sim.at(air_time, end_tx)

    def _on_tx_done(self, success, frame:Frame, start_t=None, air_time=None):
        """전송 종료 후 MAC 상태 갱신 및 메트릭 기록."""
        if success:
            # 성공: 절차 단계/디퍼럴/BO 리셋
            self.BPC = 0
            self.DC = self._dc_init_value(0) if self.use_dc_init_mode else 0
            self.BC = 0
        else:
            # 실패(충돌/프레임에러): 절차 단계 상승 + 재시도/백오프
            self.BPC = min(self.BPC + 1, self._cap_bpc_limit())
            frame.attempts += 1
            # 재시도 한계 초과 시 드롭
            if self.retry_limit is not None and frame.attempts > int(self.retry_limit):
                if getattr(self.metrics, 'on_drop', None):
                    self.metrics.on_drop(self.id, frame, frame.attempts)
                # 드롭: 큐 재삽입 없음
            else:
                # 재전송 위해 헤드에 재삽입
                self.tx_queue.insert(0, frame)
                # NEW: 단계 상승에 따른 DC 재초기화 + BC 재샘플
                self.DC = self._dc_init_value(self.BPC) if self.use_dc_init_mode else 0
                self.BC = int(self.sim.rng.randrange(0, self.CW()))

        if start_t is not None:
            end_t = start_t + (air_time or 0)
            self.metrics.on_tx(frame, success, start_t, end_t, self.id, self.medium)
