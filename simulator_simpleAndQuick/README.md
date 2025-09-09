
# ISO 15118 CP-based HPGP Simulator (Python, Discrete-Event)

Research-friendly discrete-event simulator for HomePlug Green PHY (HPGP) MAC over the ISO 15118 Control Pilot (CP) link.
- HPGP MAC with **DC/BPC**, **PRS**, **CAP0–3** (simplified but parameterized)
- Channel with **Gilbert–Elliott** + **periodic 50/60 Hz noise overlay**
- ISO 15118/SLAC-style app generator with **timeouts/deadlines**
- Metrics: utilization (eta), throughput, deadline miss ratio, p95/p99.9 delays, timeouts
- Configurable via **JSON** in `config/defaults.json`
- Topology: `cp_point_to_point` (default), optional `shared_bus` for research extensions

## Quick start
```bash
python /mnt/data/scripts/run_demo.py
```

### Override simulation time without editing JSON
- Use CLI on scripts:
	- `scripts/run_demo.py --sim-time-s 60`
	- `scripts/sweep_nodes.py --sim-time-s 60`
	- `scripts/sweep_rate_eta90.py --sim-time-s 60`
- Or set env var for any entry point:
	- `SIM_TIME_S=60` (respected inside `hpgp_sim/sim.py`)

## Files
- `hpgp_sim/utils.py` – discrete-event engine
- `hpgp_sim/medium.py` – medium model, PRS helper
- `hpgp_sim/channel.py` – Gilbert–Elliott + periodic modulation
- `hpgp_sim/mac_hpgp.py` – HPGP MAC (DC/BPC/PRS/CAP)
- `hpgp_sim/app_15118.py` – SLAC-like traffic generator + timeouts
- `hpgp_sim/metrics.py` – logs (`tx_log.csv`, `deadlines.csv`, `timeouts.csv`) and summary
- `config/defaults.json` – all rules/sequence params
- `scripts/run_demo.py` – run and print summary

## Notes
- This is a compact baseline suitable for extension. For publication-grade accuracy, calibrate parameters to the IEEE 1901/HPGP specs or measurement.
- All rules (CW, DC thresholds, timers, PER, etc.) are in `config/defaults.json` so you can run sweeps.
