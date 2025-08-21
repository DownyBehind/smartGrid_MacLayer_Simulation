"""
utils.py
========
역할
- 이산 사건(Discrete-Event) 시뮬레이터의 최소 코어를 제공한다.
- 이벤트(Event) 구조와 우선순위 큐(힙)를 이용해 시뮬레이션 시계를 전진시킨다.
- 난수 시드 고정, 훅(on_tick) 지원으로 채널 상태 갱신 등 반복 작업을 처리한다.

구성
- Event: 시간 t, 우선순위 prio, 실행 함수 fn 을 담는 데이터 클래스.
- Sim  : 이벤트 큐, 전역 시계, 난수 발생기, 이벤트 스케줄 API(at/call_later_abs/run) 제공.
"""

from dataclasses import dataclass, field  # 데이터 클래스 사용
import heapq  # 최소 힙을 이용한 우선순위 큐
from typing import Callable  # 콜러블 타입 힌트

@dataclass(order=True)  # 비교 가능(order=True)한 데이터 클래스
class Event:
    t: int                      # 이벤트 발생 절대 시각(마이크로초 단위)
    prio: int                   # 동일 시각일 때 실행 순서를 위한 우선순위(작을수록 먼저)
    fn: Callable = field(compare=False)  # 실행할 함수(비교에서 제외)

class Sim:
    def __init__(self, seed=1):
        self.t = 0                                  # 시뮬레이터 현재 시각(us)
        self.q = []                                 # 이벤트 힙(우선순위 큐)
        self.rng = __import__("random").Random(seed) # 재현 가능한 난수 발생기
        self.hooks = {"on_tick":[]}                 # 매 틱마다 호출할 훅 목록

    def at(self, dt, fn, prio=0):
        """현재 시각에서 dt(us) 뒤에 이벤트를 스케줄링."""
        heapq.heappush(self.q, Event(self.t+int(dt), prio, fn))

    def call_later_abs(self, t_abs, fn, prio=0):
        """절대 시각 t_abs(us)에 이벤트를 스케줄링."""
        heapq.heappush(self.q, Event(int(t_abs), prio, fn))

    def run(self, until=None, max_events=None):
        """이벤트를 시간 순서로 처리. until(us)까지 또는 max_events개 처리."""
        n=0
        while self.q:
            ev = heapq.heappop(self.q)             # 가장 이른/높은 우선순위 이벤트 팝
            if until is not None and ev.t > until: # 종료조건: until을 넘으면 중단
                heapq.heappush(self.q, ev)         # 다시 넣어 다음 실행을 위해 보존
                break
            self.t = ev.t                          # 시계 전진
            for h in self.hooks["on_tick"]:        # 틱 훅 호출(채널 갱신 등)
                h(self)
            ev.fn()                                # 이벤트 함수 실행
            n+=1
            if max_events is not None and n>=max_events: # 이벤트 수 제한
                break

    def now(self): 
        """현재 시각(us) 반환."""
        return self.t
