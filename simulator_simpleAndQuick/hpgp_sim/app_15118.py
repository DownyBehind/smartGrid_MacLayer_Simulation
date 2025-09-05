"""
app_15118.py
============
- SLAC 상세 시퀀스 (CAP3)
- SLAC 완료 이후: DC 루프(Req, 100ms 주기 등) + EVSE 응답자(Res)
- DC 주기 위반/응답지연/타임아웃 로깅은 metrics.debug(...)로 남긴다.
"""

from .mac_hpgp import Priority, Frame

class App15118:
    def __init__(self, sim, mac, role, timers, metrics, app_id="node"):
        self.sim = sim
        self.mac = mac
        self.role = role            # "EV" | "EVSE"
        self.metrics = metrics
        self.app_id = app_id

        # --- SLAC 타이머 (프레임 데드라인은 사용하지 않고, 세션 타임아웃은 metrics에서 처리) ---
        self.timers = timers or {}
        self.ddl_parm  = int(self.timers.get("DISCOVERY_TO", 50_000))
        self.ddl_meas  = int(self.timers.get("MEAS_TO",      60_000))
        self.ddl_match = int(self.timers.get("MATCH_TO",     80_000))

        # Baseline timeouts per SLAC modeling guide
        self.msg_to_us   = int(self.timers.get("V2G_EVCC_Msg_Timeout_ms", 2000)) * 1000   # default 2000 ms
        self.proc_to_us  = int(self.timers.get("TT_EV_SLAC_matching_ms", 60000)) * 1000   # default 60000 ms
        self.max_retries = int(self.timers.get("SLAC_MAX_RETRY", 3))
        self.retry_backoff_us = int(self.timers.get("SLAC_RETRY_BACKOFF_us", 150_000))    # 150 ms

        # Internal state
        self._awaiting = None
        self._slac_done = False
        self._retry_count = 0
        self._proc_timer_armed = False
        self._slac_rx = set()       # (NEW) 실제 성공 전파된 응답 kind 집합

        # --- SLAC 상세 파라미터 ---
        self.N_start_atten   = 3
        self.N_msound        = 10
        self.gap_start_us    = 2_000
        self.gap_msound_us   = 2_000
        self.delay_evse_rsp  = 1_000
        self.gap_attn_us     = 2_000
        self.gap_match_us    = 2_000

        # --- Post-SLAC 랜덤 트래픽(비활성화 가능) ---
        self.post_slac_cfg = None

        # --- DC 루프/응답 관련 (config에서 주입됨) ---
        self.dc_loop_enabled   = False
        self.dc_period_us      = 100_000  # 기본 100ms
        self.dc_deadline_us    = 100_000  # 기본 100ms
        self.dc_rsp_delay_us   = 1_500
        self.dc_rsp_jitter_us  = 0

        # 상태
        self._peer         = None
        self._dc_started   = False
        self._dc_req_seq   = 0
        self._last_req_us  = None
        self._pending_rsp  = {}   # seq -> (req_t, deadline_t)

    # -------- wiring --------
    def set_peer(self, peer_app):
        self._peer = peer_app

    def configure_slac_detail(self, N_start_atten=None, N_msound=None,
                              gap_start_us=None, gap_msound_us=None,
                              delay_evse_rsp_us=None, gap_attn_us=None, gap_match_us=None):
        if N_start_atten is not None: self.N_start_atten = int(N_start_atten)
        if N_msound is not None:      self.N_msound      = int(N_msound)
        if gap_start_us is not None:  self.gap_start_us  = int(gap_start_us)
        if gap_msound_us is not None: self.gap_msound_us = int(gap_msound_us)
        if delay_evse_rsp_us is not None: self.delay_evse_rsp = int(delay_evse_rsp_us)
        if gap_attn_us is not None:   self.gap_attn_us   = int(gap_attn_us)
        if gap_match_us is not None:  self.gap_match_us  = int(gap_match_us)

    def configure_post_slac_traffic(self, rate_mean_pps=0, bytes_min=300, bytes_max=1500, cap_choices=None, start_delay_us=0):
        if cap_choices is None:
            cap_choices = [Priority.CAP0, Priority.CAP1, Priority.CAP2]
        self.post_slac_cfg = dict(rate_mean_pps=float(rate_mean_pps),
                                  bytes_min=int(bytes_min),
                                  bytes_max=int(bytes_max),
                                  cap_choices=list(cap_choices),
                                  start_delay_us=int(start_delay_us))

    def configure_dc_loop(self, enabled=False, period_ms=100, deadline_ms=100, rsp_delay_us=1500, rsp_jitter_us=0):
        self.dc_loop_enabled  = bool(enabled)
        self.dc_period_us     = int(period_ms * 1_000)
        self.dc_deadline_us   = int(deadline_ms * 1_000)
        self.dc_rsp_delay_us  = int(rsp_delay_us)
        self.dc_rsp_jitter_us = int(rsp_jitter_us)

    # -------- SLAC main entry --------
    def start_slac(self, start_us=0):
        if self.role != "EV":  # EV가 트리거
            return
        def _go():
            self._retry_count = 0
            self._reset_for_retry()
            self._slac_sequence()
        self.sim.at(start_us, _go)

    # -------- 공통 헬퍼 --------
    def _enqueue(self, bits, prio, kind, ddl_us=None):
        fr = Frame(src=self.mac.id, dst="peer", bits=bits,
                   prio=prio, deadline_us=ddl_us, kind=kind, app_id=self.app_id)
        self.mac.enqueue(fr)

    # (NEW) EVSE 응답을 실제 MAC 경합을 통해 성공 전파시킨 뒤에만 EV 상위에 도달로 처리
    def _evse_rsp_cap3(self, kind, bits, ddl_us):
        if self._peer is None:
            return
        # 응답 프레임은 SECC 쪽 MAC 큐를 통해 송신
        fr = Frame(src=self._peer.mac.id, dst="peer", bits=bits,
                   prio=Priority.CAP3, deadline_us=ddl_us, kind=kind, app_id=self._peer.app_id)

        def _delivered(k=kind):
            # 실제 성공 전파된 시점에서만 EV 상위에 수신 처리 + 대기 해제
            self._on_slac_rsp_delivered(k)

        def _dropped(k=kind):
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("SLAC_RSP_DROPPED", node=self.mac.id, kind=k)

        fr.on_success = _delivered
        fr.on_drop    = _dropped

        self._peer.mac.enqueue(fr)

    # -------- SLAC-process helpers for timeouts/retry --------
    def _await_response(self, kind, timeout_us):
        """Arm a message-level timeout for the given expected response kind."""
        self._awaiting = kind
        def _check(kind=kind):
            if self._slac_done:
                return
            if self._awaiting == kind:
                if hasattr(self.metrics, "debug"):
                    self.metrics.debug("SLAC_TIMEOUT_MSG", node=self.mac.id, expect=kind)
                self._fail_and_maybe_retry(reason=f"msg:{kind}")
        self.sim.at(timeout_us, _check)

    def _on_slac_rsp_delivered(self, kind):
        """(NEW) SECC 응답이 실제 성공 전파되어 EV가 수신했다고 기록 + 대기 해제."""
        self._slac_rx.add(str(kind).upper())
        if self._awaiting == kind:
            self._awaiting = None
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("SLAC_MSG_OK", node=self.mac.id, kind=kind)
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_RX", node=self.mac.id, kind=kind)

    def _arm_process_timeout(self):
        if self._proc_timer_armed:
            return
        self._proc_timer_armed = True
        def _check():
            if self._slac_done:
                return
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("SLAC_TIMEOUT_PROC", node=self.mac.id)
            self._fail_and_maybe_retry(reason="process")
        self.sim.at(self.proc_to_us, _check)

    def _reset_for_retry(self):
        self._awaiting = None
        self._slac_done = False
        self._proc_timer_armed = False
        self._slac_rx.clear()

    def _fail_and_maybe_retry(self, reason=""):
        if self._slac_done:
            return
        self._slac_done = True
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_DONE", node=self.mac.id, ok=0, reason=reason)
        if self._retry_count < self.max_retries:
            cnt = self._retry_count + 1
            backoff = self.retry_backoff_us
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("SLAC_RETRY", node=self.mac.id, count=cnt, delay_us=backoff)
            def _again():
                self._reset_for_retry()
                self._retry_count = cnt
                self._slac_sequence()
            self.sim.at(backoff, _again)
        # else give up (no DC)

    # -------- whole SLAC sequence --------
    def _slac_sequence(self):
        # 1) Parm
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_SEQ_START", node=self.mac.id, role=self.role)
        self._arm_process_timeout()

        self._enqueue(bits=300*8, prio=Priority.CAP3, kind="SLAC_PARM_REQ", ddl_us=self.ddl_parm)
        self._await_response("SLAC_PARM_CNF", self.msg_to_us)
        self.sim.at(self.delay_evse_rsp, lambda: self._evse_rsp_cap3(kind="SLAC_PARM_CNF", bits=300*8, ddl_us=self.ddl_parm))

        # 2) StartAtten
        t = 0
        for i in range(self.N_start_atten):
            t += self.gap_start_us if i>0 else self.gap_attn_us
            self.sim.at(t, lambda idx=i: self._enqueue(bits=400*8, prio=Priority.CAP3, kind=f"START_ATTEN_{idx+1}", ddl_us=self.ddl_meas))

        # 3) MNBC
        base = t
        for j in range(self.N_msound):
            dt = base + (j+1)*self.gap_msound_us
            self.sim.at(dt, lambda idx=j: self._enqueue(bits=500*8, prio=Priority.CAP3, kind=f"MNBC_SOUND_{idx+1}", ddl_us=self.ddl_meas))

        # 4) AttenChar
        attn_ind_t = base + self.N_msound*self.gap_msound_us + self.gap_attn_us
        self._await_response("ATTEN_CHAR_IND", self.msg_to_us)
        self.sim.at(attn_ind_t + self.delay_evse_rsp, lambda: self._evse_rsp_cap3(kind="ATTEN_CHAR_IND", bits=200*8, ddl_us=self.ddl_meas))
        self.sim.at(attn_ind_t + self.delay_evse_rsp + self.gap_attn_us, lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="ATTEN_CHAR_RSP", ddl_us=self.ddl_meas))

        # 5) Match
        match_t = attn_ind_t + self.delay_evse_rsp + 2*self.gap_attn_us
        self.sim.at(match_t, lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="SLAC_MATCH_REQ", ddl_us=self.ddl_match))
        self._await_response("SLAC_MATCH_CNF", self.msg_to_us)
        self.sim.at(match_t + self.delay_evse_rsp, lambda: self._evse_rsp_cap3(kind="SLAC_MATCH_CNF", bits=200*8, ddl_us=self.ddl_match))

        # (NEW) 최종 성공 판정: 필수 응답 3종이 실제로 전파되었는지 확인
        final_t = match_t + self.delay_evse_rsp + self.gap_match_us
        def _check_and_finish():
            required = {"SLAC_PARM_CNF", "ATTEN_CHAR_IND", "SLAC_MATCH_CNF"}
            ok = required.issubset(self._slac_rx)
            self._on_slac_done(success=ok)
        self.sim.at(final_t, _check_and_finish)

    # -------- SLAC done -> start DC loop --------
    def _on_slac_done(self, success=True):
        if self._slac_done:
            return
        self._slac_done = True
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_DONE", node=self.mac.id, role=self.role, ok=int(success))

        # DC 루프를 EV에서 시작
        if self.role == "EV" and self.dc_loop_enabled and success:
            self.sim.at(0, self._start_dc_loop)

        # (선택) post-SLAC 랜덤 트래픽은 기본 OFF로 두거나 필요 시 사용
        if self.post_slac_cfg and success and self.post_slac_cfg.get("rate_mean_pps", 0) > 0:
            self.sim.at(self.post_slac_cfg["start_delay_us"], self._start_random_traffic)

    # -------- DC loop (EV) & responder (EVSE) --------
    def _start_dc_loop(self):
        if self._dc_started: return
        self._dc_started = True
        now = self.sim.now()
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("DC_START", node=self.mac.id, role=self.role, t_us=now)

        def tick():
            # Req 생성
            self._dc_req_seq += 1
            seq = self._dc_req_seq
            now_req = self.sim.now()

            # 주기 위반 체크(Req 사이 간격)
            gap_violation = 0
            if self._last_req_us is not None and (now_req - self._last_req_us) > self.dc_period_us:
                gap_violation = 1
            self._last_req_us = now_req

            # Req 전송 (CAP0 가정)
            kind_req = f"DC_CUR_DEM_REQ_{seq}"
            self._enqueue(bits=300*8, prio=Priority.CAP0, kind=kind_req, ddl_us=None)

            if hasattr(self.metrics, "debug"):
                self.metrics.debug("DC_REQ", node=self.mac.id, seq=seq, t_us=now_req, gap_violation=gap_violation)

            # 워치독 (Rsp 타임아웃 여부)
            deadline_t = now_req + self.dc_deadline_us
            self._pending_rsp[seq] = (now_req, deadline_t)
            def watchdog(s=seq, due=deadline_t, req_t=now_req):
                # 만약 아직 응답이 안찍혔다면 타임아웃 기록
                if s in self._pending_rsp:
                    self._pending_rsp.pop(s, None)
                    if hasattr(self.metrics, "debug"):
                        self.metrics.debug("DC_TIMEOUT", node=self.mac.id, seq=s, req_us=req_t, due_us=due)
            self.sim.at(self.dc_deadline_us, watchdog)

            # EVSE 응답자 스케줄
            if self._peer and self._peer.role == "EVSE":
                delay = self.dc_rsp_delay_us
                if self.dc_rsp_jitter_us > 0:
                    # 간단한 균등 지터
                    jitter = self.sim.rng.randrange(-self.dc_rsp_jitter_us, self.dc_rsp_jitter_us+1)
                    delay = max(0, delay + jitter)
                def do_rsp(s=seq, req_node=self.mac.id):
                    # RSP 전송
                    kind_rsp = f"DC_CUR_DEM_RSP_{s}"
                    fr = Frame(src=self._peer.mac.id, dst="peer", bits=200*8,
                               prio=Priority.CAP0, deadline_us=None, kind=kind_rsp, app_id=self._peer.app_id)
                    self._peer.mac.enqueue(fr)
                    # 로깅
                    if hasattr(self.metrics, "debug"):
                        self.metrics.debug("DC_RSP", node=req_node, seq=s, t_us=self.sim.now())
                    # 타임아웃 해제
                    self._pending_rsp.pop(s, None)
                self.sim.at(delay, do_rsp)

            # 다음 주기
            self.sim.at(self.dc_period_us, tick)

        # 첫 틱 즉시 시작
        tick()

    # -------- random traffic generator (optional) --------
    def _start_random_traffic(self):
        cfg = self.post_slac_cfg
        if not cfg or cfg["rate_mean_pps"] <= 0:
            return
        def gen():
            lam = cfg["rate_mean_pps"]
            gap_s = self.sim.rng.expovariate(lam)
            gap_us = max(1, int(gap_s * 1e6))
            size_bytes = self.sim.rng.randrange(cfg["bytes_min"], cfg["bytes_max"] + 1)
            pr = self.sim.rng.choice(cfg["cap_choices"])
            fr = Frame(src=self.mac.id, dst="peer", bits=size_bytes*8, prio=pr, deadline_us=None, kind="POST", app_id=self.app_id)
            self.mac.enqueue(fr)
            self.sim.at(gap_us, gen)
        gen()
