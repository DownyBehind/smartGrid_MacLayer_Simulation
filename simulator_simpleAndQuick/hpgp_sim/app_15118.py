"""
app_15118.py
============
Detailed SLAC sequence (ISO 15118-3 Annex A inspired) + DC CurrentDemand loop (100 ms default)
- SLAC frames are CAP3. DC loop frames (CurrentDemand) are CAP0 (per user assumption).
- After SLAC done (EV), start a periodic CurrentDemand Req/Res loop.
- Metrics emits:
  * debug: "SLAC_SEQ_START", "SLAC_DONE", "DC_START"
  * DC loop frames kinds: "CD_REQ_<EVNODE>_<CID>", "CD_RSP_<EVNODE>_<CID>"
    (metrics parses tx_log to compute latency & deadline violations)

Configuration (via sim.py):
- SLAC timers & details: unchanged
- DC loop: enabled, period_ms, deadline_ms, rsp_delay_us, rsp_jitter_us

Note:
- To keep model simple, EV schedules EVSE response (peer enqueue) with a small processing delay.
- Periodic scheduler drives Req schedule; channel/MAC contention determines actual air times.
"""

from .mac_hpgp import Priority, Frame

class App15118:
    def __init__(self, sim, mac, role, timers, metrics, app_id="node"):
        self.sim = sim
        self.mac = mac
        self.role = role            # "EV" | "EVSE"
        self.metrics = metrics
        self.app_id = app_id

        # -------- SLAC timers (phase-level deadlines) --------
        self.timers = timers or {}
        self.ddl_parm = int(self.timers.get("DISCOVERY_TO", 50_000))
        self.ddl_meas = int(self.timers.get("MEAS_TO",      60_000))
        self.ddl_match= int(self.timers.get("MATCH_TO",     80_000))

        # -------- Detailed SLAC params (defaults; overridable) --------
        self.N_start_atten = 3
        self.N_msound      = 10
        self.gap_start_us  = 2_000     # gap between StartAtten
        self.gap_msound_us = 2_000     # gap between MNBC sounds
        self.delay_evse_rsp_us = 1_000 # EVSE processing→response delay
        self.gap_attn_us   = 2_000     # gap before/after atten-char
        self.gap_match_us  = 2_000     # gap before/after match

        # -------- Post-SLAC traffic (legacy random); keep but bypass if DC loop enabled --------
        self.post_slac_cfg = None

        # -------- DC loop (CurrentDemand) params --------
        self.dc_enabled = False
        self.dc_period_us = 100_000     # 100 ms
        self.dc_deadline_us = 100_000   # 100 ms
        self.dc_rsp_delay_us = 1_500    # EVSE processing delay (us)
        self.dc_rsp_jitter_us = 0       # ±jitter around rsp_delay

        # State
        self._slac_done = False
        self._peer = None

        # DC loop state
        self._dc_next_cid = 0

    # ---------------- wiring ----------------
    def set_peer(self, peer_app):
        """Set counterpart (EV <-> EVSE)."""
        self._peer = peer_app

    # ---------------- SLAC detail config ----------------
    def configure_slac_detail(self, N_start_atten=None, N_msound=None,
                              gap_start_us=None, gap_msound_us=None,
                              delay_evse_rsp_us=None, gap_attn_us=None, gap_match_us=None):
        if N_start_atten is not None: self.N_start_atten = int(N_start_atten)
        if N_msound is not None:      self.N_msound      = int(N_msound)
        if gap_start_us is not None:  self.gap_start_us  = int(gap_start_us)
        if gap_msound_us is not None: self.gap_msound_us = int(gap_msound_us)
        if delay_evse_rsp_us is not None: self.delay_evse_rsp_us = int(delay_evse_rsp_us)
        if gap_attn_us is not None:   self.gap_attn_us   = int(gap_attn_us)
        if gap_match_us is not None:  self.gap_match_us  = int(gap_match_us)

    # ---------------- Post-SLAC random traffic ----------------
    def configure_post_slac_traffic(self, rate_mean_pps=50, bytes_min=300, bytes_max=1500, cap_choices=None, start_delay_us=0):
        from .mac_hpgp import Priority
        if cap_choices is None:
            cap_choices = [Priority.CAP0, Priority.CAP1, Priority.CAP2]
        self.post_slac_cfg = dict(rate_mean_pps=float(rate_mean_pps),
                                  bytes_min=int(bytes_min),
                                  bytes_max=int(bytes_max),
                                  cap_choices=list(cap_choices),
                                  start_delay_us=int(start_delay_us))

    # ---------------- DC loop config ----------------
    def configure_dc_loop(self, enabled=False, period_ms=100, deadline_ms=100, rsp_delay_us=1500, rsp_jitter_us=0):
        self.dc_enabled = bool(enabled)
        self.dc_period_us = int(float(period_ms) * 1e3)
        self.dc_deadline_us = int(float(deadline_ms) * 1e3)
        self.dc_rsp_delay_us = int(rsp_delay_us)
        self.dc_rsp_jitter_us = int(rsp_jitter_us)

    # ---------------- External trigger ----------------
    def start_slac(self, start_us=0):
        if self.role != "EV":  # EV triggers the sequence in this simplified model
            return
        self.sim.at(start_us, self._slac_sequence)

    # ---------------- enqueue helper ----------------
    def _enqueue(self, bits, prio, kind, ddl_us):
        fr = Frame(src=self.mac.id, dst="peer", bits=bits,
                   prio=prio, deadline_us=ddl_us, kind=kind, app_id=self.app_id)
        # record born time for deadline accounting
        fr.born_t = self.sim.now()
        self.mac.enqueue(fr)

    # EVSE-simulated responders (CAP3 for SLAC, CAP0 for DC)
    def _evse_rsp(self, kind, bits, ddl_us, prio):
        """Schedule a response frame from EVSE peer (if any)."""
        if self._peer is None: return
        fr = Frame(src=self._peer.mac.id, dst="peer", bits=bits,
                   prio=prio, deadline_us=ddl_us, kind=kind, app_id=self._peer.app_id)
        fr.born_t = self.sim.now()
        self._peer.mac.enqueue(fr)

    # ---------------- SLAC full sequence ----------------
    def _slac_sequence(self):
        # 1) Parameter exchange
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_SEQ_START", node=self.mac.id, role=self.role)
        # EV: CM_SLAC_PARM.REQ
        self._enqueue(bits=300*8, prio=Priority.CAP3, kind="SLAC_PARM_REQ", ddl_us=self.ddl_parm)
        # EVSE: CM_SLAC_PARM.CNF after delay
        self.sim.at(self.delay_evse_rsp_us, lambda: self._evse_rsp(kind="SLAC_PARM_CNF", bits=300*8, ddl_us=self.ddl_parm, prio=Priority.CAP3))

        # 2) StartAtten series
        t = 0
        for i in range(self.N_start_atten):
            t += self.gap_start_us if i>0 else self.gap_attn_us
            self.sim.at(t, lambda idx=i: self._enqueue(bits=400*8, prio=Priority.CAP3, kind=f"START_ATTEN_{idx+1}", ddl_us=self.ddl_meas))

        # 3) MNBC sound series
        base = t
        for j in range(self.N_msound):
            dt = base + (j+1)*self.gap_msound_us
            self.sim.at(dt, lambda idx=j: self._enqueue(bits=500*8, prio=Priority.CAP3, kind=f"MNBC_SOUND_{idx+1}", ddl_us=self.ddl_meas))

        # 4) Attenuation report (EVSE IND -> EV RSP)
        attn_ind_t = base + self.N_msound*self.gap_msound_us + self.gap_attn_us
        self.sim.at(attn_ind_t + self.delay_evse_rsp_us,
                    lambda: self._evse_rsp(kind="ATTEN_CHAR_IND", bits=200*8, ddl_us=self.ddl_meas, prio=Priority.CAP3))
        self.sim.at(attn_ind_t + self.delay_evse_rsp_us + self.gap_attn_us,
                    lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="ATTEN_CHAR_RSP", ddl_us=self.ddl_meas))

        # 5) Match (EV REQ -> EVSE CNF)
        match_t = attn_ind_t + self.delay_evse_rsp_us + 2*self.gap_attn_us
        self.sim.at(match_t, lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="SLAC_MATCH_REQ", ddl_us=self.ddl_match))
        self.sim.at(match_t + self.delay_evse_rsp_us,
                    lambda: self._evse_rsp(kind="SLAC_MATCH_CNF", bits=200*8, ddl_us=self.ddl_match, prio=Priority.CAP3))

        # Finalize
        self.sim.at(match_t + self.delay_evse_rsp_us + self.gap_match_us,
                    lambda: self._on_slac_done(success=True))

    # ---------------- on SLAC done ----------------
    def _on_slac_done(self, success=True):
        if self._slac_done: return
        self._slac_done = True
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_DONE", node=self.mac.id, role=self.role, ok=int(success))

        # EV: start DC loop if enabled, else legacy random traffic
        if self.role == "EV" and success and self.dc_enabled:
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("DC_START", node=self.mac.id)
            # kick off periodic loop immediately
            self._dc_next_cid = 0
            self.sim.at(0, self._dc_tick)
        elif self.post_slac_cfg and success:
            self.sim.at(self.post_slac_cfg["start_delay_us"], self._start_random_traffic)

    # ---------------- DC loop generator ----------------
    def _dc_tick(self):
        # schedule EV Req now
        cid = self._dc_next_cid
        self._dc_next_cid += 1
        ev_id = self.mac.id

        # EV sends CAP0 CurrentDemand Req
        kind_req = f"CD_REQ_{ev_id}_{cid}"
        self._enqueue(bits=320*8, prio=Priority.CAP0, kind=kind_req, ddl_us=None)
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("DC_CYCLE_START", node=ev_id, cid=cid)

        # EVSE sends CAP0 CurrentDemand Res after processing delay + jitter
        delay = self.dc_rsp_delay_us
        if self.dc_rsp_jitter_us > 0:
            # uniform +/- jitter
            j = self.sim.rng.randrange(-self.dc_rsp_jitter_us, self.dc_rsp_jitter_us + 1)
            delay = max(0, delay + j)

        kind_rsp = f"CD_RSP_{ev_id}_{cid}"
        self.sim.at(delay, lambda: self._evse_rsp(kind=kind_rsp, bits=320*8, ddl_us=None, prio=Priority.CAP0))

        # schedule next cycle at fixed period
        self.sim.at(self.dc_period_us, self._dc_tick)

    # ---------------- legacy random traffic ----------------
    def _start_random_traffic(self):
        cfg = self.post_slac_cfg
        if not cfg or cfg["rate_mean_pps"] <= 0:
            return

        def gen():
            lam = cfg["rate_mean_pps"]
            gap_s = self.sim.rng.expovariate(lam)   # seconds
            gap_us = max(1, int(gap_s * 1e6))
            size_bytes = self.sim.rng.randrange(cfg["bytes_min"], cfg["bytes_max"] + 1)
            pr = self.sim.rng.choice(cfg["cap_choices"])

            fr = Frame(src=self.mac.id, dst="peer",
                       bits=size_bytes * 8,
                       prio=pr, deadline_us=None,
                       kind="POST", app_id=self.app_id)
            fr.born_t = self.sim.now()
            self.mac.enqueue(fr)

            self.sim.at(gap_us, gen)

        gen()
