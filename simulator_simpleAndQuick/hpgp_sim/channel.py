"""
channel.py
==========
역할
- PLC 채널의 오류를 **Gilbert–Elliott** 모델로 근사하고, 50/60 Hz 주기성 잡음을 오버레이한다.
- good/bad 상태 전이 확률(p_bg, p_bb)과 상태별 PER(per_good, per_bad)을 사용한다.
- 상태 업데이트는 step_us 그리드로 이루어지며, per() 호출 시 지난 시간만큼 상태를 전진시킨다.

설정 파라미터
- p_bg: good→bad로 진입할 확률(스텝당)
- p_bb: bad 상태 유지 확률(스텝당)
- per_good/per_bad: 상태별 프레임 오류 확률
- step_us: 상태 업데이트 시간 해상도(us)
- periodic: {"freq_hz":f, "amp":A, "bias":B} → PER = base * (1 + bias + A*sin(2π f t))
"""

import math  # 삼각함수, 파이

class GEChannel:
    def __init__(self, sim, p_bg=1e-5, p_bb=0.98, per_good=1e-6, per_bad=0.05, step_us=1000, periodic=None):
        self.sim = sim
        self.p_bg = p_bg                         # good→bad 진입 확률
        self.p_bb = p_bb                         # bad 유지 확률
        self.per_good = per_good                 # good 상태 PER
        self.per_bad = per_bad                   # bad 상태 PER
        self.step_us = step_us                   # 상태 업데이트 해상도
        self.bad = False                         # 현재 채널 상태 플래그(False=good, True=bad)
        self.periodic = periodic or {"freq_hz":0, "amp":0.0, "bias":0.0}  # 주기성 잡음 파라미터
        # on_tick 훅은 등록만(여기선 per() 호출 때 상태 전진)

    def _advance_state(self, steps, rng):
        """지정된 스텝 수만큼 감마르코프 상태를 전진시킨다."""
        for _ in range(steps):
            if self.bad:
                # bad 상태 유지 여부 결정
                self.bad = rng.random() < self.p_bb
            else:
                # good에서 bad로 진입 여부 결정
                self.bad = rng.random() < self.p_bg

    def per(self, last_t, rng):
        """
        마지막 질의 시각 last_t 이후 경과한 시간만큼 상태를 전진시키고,
        현재 상태와 주기성 잡음을 반영한 PER를 반환한다.
        """
        dt = max(0, self.sim.now() - last_t)             # 경과 시간(us)
        steps = dt // self.step_us if self.step_us>0 else 0  # 전진할 스텝 수
        if steps>0:
            self._advance_state(int(steps), rng)         # 숨은 상태 전진
        base = self.per_bad if self.bad else self.per_good  # 기본 PER
        # 주기성(라인 주파수 등) 가중
        f = self.periodic.get("freq_hz",0.0)
        amp = self.periodic.get("amp",0.0)
        bias = self.periodic.get("bias",0.0)
        if f>0 and amp!=0.0:
            t_sec = self.sim.now() * 1e-6               # 현재 시각(초)
            base = base * max(0.0, 1.0 + bias + amp*math.sin(2*math.pi*f*t_sec))
        return min(1.0, max(0.0, base))                 # 0~1로 클램핑
