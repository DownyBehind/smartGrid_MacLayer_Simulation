# SLAC Baseline Integration (HPGP1.1/ISO 15118-3)

This patch wires the "Baseline SLAC modeling guide" into the simulator.
Focus: Message-level timeout (2s), process-level timeout (60s), fail-fast + retry, all SLAC frames on CAP3.

## Files
- `updated_app_15118.py` — drop in to replace `hpgp_sim/app_15118.py`
- `slac_timers_baseline.json` — config snippet to merge into your JSON

## What changed (high level)
- **Message-level timeout (2s)** for steps 1,4,5 via `_await_response()` and `SLAC_TIMEOUT_MSG`.
- **Process-level timeout (60s)** via `_arm_process_timeout()` and `SLAC_TIMEOUT_PROC`.
- **Immediate abort + retry (max 3)** on any timeout: logs `SLAC_DONE(ok=0)` then `SLAC_RETRY` and restarts from the beginning.
- **Baseline delivery of responses to the app**: when EVSE enqueues CAP3 response, EV app marks it received (`SLAC_MSG_OK`).
- Keeps your existing detailed SLAC sequencing & CAP3 use; no changes to DC loop logic.

## New/updated config keys
Add under `traffic.slac_timers` (values shown are defaults if omitted):
```json
{
  "V2G_EVCC_Msg_Timeout_ms": 2000,
  "TT_EV_SLAC_matching_ms": 60000,
  "SLAC_MAX_RETRY": 3,
  "SLAC_RETRY_BACKOFF_us": 150000
}
```
Also set session timeout for reporting:
```json
{ "traffic": { "slac_session": { "TT_session_s": 60.0 } } }
```

## New debug tags
- `SLAC_TIMEOUT_MSG {expect}`
- `SLAC_TIMEOUT_PROC`
- `SLAC_MSG_OK {kind}`
- `SLAC_RETRY {count, delay_us}`
- `SLAC_DONE {ok=0, reason}`

## How to use
1. Replace `hpgp_sim/app_15118.py` with `updated_app_15118.py`.
2. Merge `slac_timers_baseline.json` into your config.
3. Run your existing sweep; the above timeouts will only fire on abnormal conditions (baseline has no contention).
