"""
app_15118.py
============
Detailed SLAC sequence (ISO 15118-3 Annex A inspired, research-grade simplification)
- Frames are scheduled as CAP3 during SLAC.
- Sequence per EV (peer is EVSE):
  1) CM_SLAC_PARM.REQ  -> (EVSE) CM_SLAC_PARM.CNF
  2) CM_START_ATTEN_CHAR.IND  (x N_start)  [EV]
  3) CM_MNBC_SOUND.IND        (x N_msound) [EV]
  4) CM_ATTEN_CHAR.IND  -> (EV) CM_ATTEN_CHAR.RSP
  5) CM_SLAC_MATCH.REQ  -> (EVSE) CM_SLAC_MATCH.CNF
- After SLAC done: start random traffic with CAP0/1/2 (configurable).

[NEW in this version]
- Session-timeout based ABORT: If (SLAC_SEQ_START → now) exceeds metrics.tt_session_us
  before completion, the EV aborts the sequence, suppresses further SLAC frames,
  logs SLAC_DONE(ok=0), and does NOT start post-SLAC traffic.
  (No changes required in sim.py — timeout value is read from metrics.)

Note:
- Per-message "deadline_us" were used previously for DMR; those are kept as optional,
  but metrics may ignore them. Session timeout is authoritative for success/failure.
"""

from .mac_hpgp import Priority, Frame

class App15118:
    def __init__(self, sim, mac, role, timers, metrics, app_id="node"):
        self.sim = sim
        self.mac = mac
        self.role = role            # "EV" | "EVSE"
        self.metrics = metrics
        self.app_id = app_id

        # SLAC timers (phase-level deadlines; optional, may be ignored by metrics)
        self.timers = timers or {}
        self.ddl_parm = int(self.timers.get("DISCOVERY_TO", 50_000))
        self.ddl_meas = int(self.timers.get("MEAS_TO",      60_000))
        self.ddl_match= int(self.timers.get("MATCH_TO",     80_000))

        # Detailed SLAC params (defaults; can be overridden)
        self.N_start_atten = 3
        self.N_msound      = 10
        self.gap_start_us  = 2_000     # gap between StartAtten
        self.gap_msound_us = 2_000     # gap between MNBC sounds
        self.delay_evse_rsp_us = 1_000 # EVSE processing→response delay
        self.gap_attn_us   = 2_000     # gap before/after atten-char
        self.gap_match_us  = 2_000     # gap before/after match

        # Random traffic after SLAC (configured separately)
        self.post_slac_cfg = None

        # State
        self._slac_done = False
        self._slac_aborted = False
        self._peer = None
        self._slac_started_at = None
        self._session_timeout_us = None  # read from metrics if available

    # -------- wiring --------
    def set_peer(self, peer_app):
        """Set counterpart (EV <-> EVSE)."""
        self._peer = peer_app

    def configure_slac_detail(self, N_start_atten=None, N_msound=None,
                              gap_start_us=None, gap_msound_us=None,
                              delay_evse_rsp_us=None, gap_attn_us=None, gap_match_us=None):
        """Override detailed SLAC parameters."""
        if N_start_atten is not None: self.N_start_atten = int(N_start_atten)
        if N_msound is not None:      self.N_msound      = int(N_msound)
        if gap_start_us is not None:  self.gap_start_us  = int(gap_start_us)
        if gap_msound_us is not None: self.gap_msound_us = int(gap_msound_us)
        if delay_evse_rsp_us is not None: self.delay_evse_rsp_us = int(delay_evse_rsp_us)
        if gap_attn_us is not None:   self.gap_attn_us   = int(gap_attn_us)
        if gap_match_us is not None:  self.gap_match_us  = int(gap_match_us)

    # Optional explicit setter (not required if metrics has tt_session_us)
    def configure_session_timeout_us(self, us):
        self._session_timeout_us = int(us) if us is not None else None

    # -------- post-SLAC random traffic --------
    def configure_post_slac_traffic(self, rate_mean_pps=50, bytes_min=300, bytes_max=1500, cap_choices=None, start_delay_us=0):
        if cap_choices is None:
            cap_choices = [Priority.CAP0, Priority.CAP1, Priority.CAP2]
        self.post_slac_cfg = dict(rate_mean_pps=float(rate_mean_pps),
                                  bytes_min=int(bytes_min),
                                  bytes_max=int(bytes_max),
                                  cap_choices=list(cap_choices),
                                  start_delay_us=int(start_delay_us))

    # -------- SLAC main entry --------
    def start_slac(self, start_us=0):
        if self.role != "EV":  # EV triggers the sequence in this simplified model
            return
        # record start & (optionally) install session timeout watchdog
        def do_start():
            self._slac_started_at = self.sim.now()
            if hasattr(self.metrics, "debug"):
                self.metrics.debug("SLAC_SEQ_START", node=self.mac.id, role=self.role)
            # install watchdog
            to_us = self._session_timeout_us
            if to_us is None:
                # try to read from metrics if available
                to_us = getattr(self.metrics, "tt_session_us", None)
            if to_us and to_us > 0:
                self.sim.at(to_us, self._watchdog_timeout)  # relative to start (now)
            # launch the sequence
            self._slac_sequence()
        self.sim.at(start_us, do_start)

    # -------- sequence helpers --------
    def _alive(self):
        return (not self._slac_done) and (not self._slac_aborted)

    def _enqueue(self, bits, prio, kind, ddl_us):
        if not self._alive():
            return
        fr = Frame(src=self.mac.id, dst="peer", bits=bits,
                   prio=prio, deadline_us=ddl_us, kind=kind, app_id=self.app_id)
        self.mac.enqueue(fr)

    # EVSE-simulated responders
    def _evse_rsp(self, kind, bits, ddl_us):
        """Schedule a CAP3 response frame from EVSE peer (if any)."""
        if not self._alive():
            return
        if self._peer is None:
            return
        # If peer has aborted/done, don't inject EVSE response
        if getattr(self._peer, "_slac_aborted", False) or getattr(self._peer, "_slac_done", False):
            return
        fr = Frame(src=self._peer.mac.id, dst="peer", bits=bits,
                   prio=Priority.CAP3, deadline_us=ddl_us, kind=kind, app_id=self._peer.app_id)
        self._peer.mac.enqueue(fr)

    # -------- whole sequence --------
    def _slac_sequence(self):
        # 1) Parameter exchange
        # EV: CM_SLAC_PARM.REQ
        self._enqueue(bits=300*8, prio=Priority.CAP3, kind="SLAC_PARM_REQ", ddl_us=self.ddl_parm)
        # EVSE: CM_SLAC_PARM.CNF after delay
        self.sim.at(self.delay_evse_rsp_us, lambda: self._evse_rsp(kind="SLAC_PARM_CNF", bits=300*8, ddl_us=self.ddl_parm))

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
                    lambda: self._evse_rsp(kind="ATTEN_CHAR_IND", bits=200*8, ddl_us=self.ddl_meas))
        self.sim.at(attn_ind_t + self.delay_evse_rsp_us + self.gap_attn_us,
                    lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="ATTEN_CHAR_RSP", ddl_us=self.ddl_meas))

        # 5) Match (EV REQ -> EVSE CNF)
        match_t = attn_ind_t + self.delay_evse_rsp_us + 2*self.gap_attn_us
        self.sim.at(match_t, lambda: self._enqueue(bits=200*8, prio=Priority.CAP3, kind="SLAC_MATCH_REQ", ddl_us=self.ddl_match))
        self.sim.at(match_t + self.delay_evse_rsp_us,
                    lambda: self._evse_rsp(kind="SLAC_MATCH_CNF", bits=200*8, ddl_us=self.ddl_match))

        # Finalize
        self.sim.at(match_t + self.delay_evse_rsp_us + self.gap_match_us,
                    lambda: self._on_slac_done(success=True))

    # -------- watchdog / abort --------
    def _watchdog_timeout(self):
        """Abort SLAC if session timeout exceeded before completion."""
        if self._slac_done or self._slac_aborted:
            return
        # Check elapsed from start; be robust if start wasn't recorded
        if self._slac_started_at is None:
            elapsed = None
        else:
            elapsed = self.sim.now() - self._slac_started_at
        # Abort
        self._slac_aborted = True
        if hasattr(self.metrics, "debug"):
            # ok=0 to mark failure; this also closes the session window in metrics
            self.metrics.debug("SLAC_DONE", node=self.mac.id, role=self.role, ok=0)

    # -------- on SLAC done --------
    def _on_slac_done(self, success=True):
        if self._slac_done or self._slac_aborted:
            return
        self._slac_done = True
        if hasattr(self.metrics, "debug"):
            self.metrics.debug("SLAC_DONE", node=self.mac.id, role=self.role, ok=int(success))
        # Start post-SLAC random traffic (if configured)
        if self.post_slac_cfg and success:
            self.sim.at(self.post_slac_cfg["start_delay_us"], self._start_random_traffic)

    # -------- random traffic generator --------
    def _start_random_traffic(self):
        if self._slac_aborted:  # do not start traffic after abort
            return
        cfg = self.post_slac_cfg
        if not cfg or cfg["rate_mean_pps"] <= 0:
            return

        def gen():
            if self._slac_aborted:
                return
            lam = cfg["rate_mean_pps"]
            gap_s = self.sim.rng.expovariate(lam)   # seconds
            gap_us = max(1, int(gap_s * 1e6))
            size_bytes = self.sim.rng.randrange(cfg["bytes_min"], cfg["bytes_max"] + 1)
            pr = self.sim.rng.choice(cfg["cap_choices"])

            fr = Frame(src=self.mac.id, dst="peer",
                       bits=size_bytes * 8,
                       prio=pr, deadline_us=None,
                       kind="POST", app_id=self.app_id)
            self.mac.enqueue(fr)

            self.sim.at(gap_us, gen)

        gen()
