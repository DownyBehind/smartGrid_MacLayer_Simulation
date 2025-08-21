"""
medium.py
=========
역할
- 매체(채널)의 점유 상태를 관리한다.
- 토폴로지에 따라 1:1 전용(cp_point_to_point) 또는 공유 버스(shared_bus)로 동작한다.
- shared_bus 모드에선 PRS(우선순위) 규칙에 따라 같은 시각에 준비된 노드들 중 승자를 결정하고,
  동률이면 충돌로 처리한다.

주요 메서드
- subscribe(mac): MAC 객체 등록
- is_idle(): 매체 유휴 여부
- start_tx/end_tx: 전송 시작/종료 시각 갱신
- request_tx_shared(contenders): shared_bus에서 승자/패자/충돌 판정
"""

class Medium:
    """매체 추상화. topology: 'cp_point_to_point' | 'shared_bus'"""
    def __init__(self, sim, topology="cp_point_to_point"):
        self.sim = sim                       # 시뮬레이터 핸들
        self.topology = topology             # 토폴로지 모드
        self.busy_until = 0                  # 매체가 바쁜 상태의 종료 시각(us)
        self.tx_owner = None                 # 현재 전송 소유 MAC의 ID
        self.listeners = []                  # 등록된 MAC 목록
        self.ongoing = []                    # 진행 중 전송(진단용)

    def subscribe(self, mac):
        """MAC 등록."""
        self.listeners.append(mac)

    def is_idle(self):
        """매체 유휴인지 판정."""
        return self.sim.now() >= self.busy_until

    def start_tx(self, node_id, air_time_us):
        """전송 시작: 소유자와 종료 시각 기록."""
        if not self.is_idle():
            raise RuntimeError("Medium busy")
        self.tx_owner = node_id
        self.busy_until = self.sim.now() + int(air_time_us)
        self.ongoing = [(node_id, self.busy_until)]

    def end_tx(self):
        """전송 종료: 소유자 해제."""
        self.tx_owner = None
        self.ongoing.clear()

    def request_tx_shared(self, contenders):
        """
        shared_bus에서 같은 시각에 준비된 후보들(contenders: [(mac, frame, airtime)])이 있을 때
        PRS 규칙으로 승자를 고른다.
        - 가장 높은 CAP(우선순위) 보유자가 승자
        - 최고 CAP가 여러 명이면 충돌 반환(winner=None)
        """
        if not contenders:
            return None, []
        # 각 후보의 CAP 추출
        caps = [ (m.head_prio().value, i) for i,(m,fr,at) in enumerate(contenders) ]
        top_cap = max(caps)[0]               # 최고 CAP
        idxs = [i for (cap,i) in caps if cap==top_cap]
        if len(idxs)==1:                     # 단일 승자
            return contenders[idxs[0]][0], [c[0] for i,c in enumerate(contenders) if i!=idxs[0]]
        else:                                # 다수 최고 CAP → 충돌
            return None, [contenders[i][0] for i in idxs]
