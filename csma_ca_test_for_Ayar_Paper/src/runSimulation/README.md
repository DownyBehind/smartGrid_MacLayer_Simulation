# Batch Runner — Usage Guide

This README shows how to use `run_simulation.py` to launch **node-count sweeps** for two experiment modes without touching your C++/INI:

* **Scale mode (default):** effective `sendInterval = base_ms × (N / 5)`
* **Fixed mode:** effective `sendInterval = fixed_ms` for all `N` (the script pre-compensates the N-scaling by rewriting `cfg.baseInterval` in the NED before each run)

It also covers where results go and how to analyze them.

---

## Prerequisites

* OMNeT++ 6.1 available as `opp_run` in your PATH
* INET built (e.g., `~/study/workspace/research/inet`)
* TimeSlot shared library built (you already did this earlier)
* Repository layout (relevant parts):

```
csma_ca_test_for_Ayar_Paper/
├─ ini/
│  ├─ omnetpp.ini
│  └─ results/                 # output folder (created if missing)
├─ ned/
│  └─ csma_ca_test_for_Ayar_Paper/FakeWireCsmaCaNetwork.ned
└─ src/runSimulation/
   └─ run_simulation.py
```

> The script edits `FakeWireCsmaCaNetwork.ned` before each run and keeps a one-time backup `FakeWireCsmaCaNetwork.ned.bak`.

---

## Environment variables (optional)

If your INET path is different, set:

```bash
export INET_DIR=/home/kimdawoon/study/workspace/research/inet
```

If `INET_DIR` is not set, the script defaults to the path above.

---

## Quick start

From the project’s `src/runSimulation/` folder:

```bash
./run_simulation.py
```

* Runs **Scale mode** with default `base_ms=1.5` for `N = 5..150 (step 5)`
* Writes outputs into `csma_ca_test_for_Ayar_Paper/ini/results/n{N}/`
* Logs a batch summary under `ini/results/batch-scale-<timestamp>.txt`

---

## Modes & options

### 1) Scale mode (default)

Effective `sendInterval = base_ms × (N / 5)`.

```bash
# default sweep: N = 5,10,15,...,150 and base_ms = 1.5
./run_simulation.py

# specify a custom base and custom N list
./run_simulation.py --mode scale --base-ms 0.5 --runs 5 10 20 40 80 120
```

### 2) Fixed mode

Effective `sendInterval = fixed_ms` for all N.
The script computes `cfg.baseInterval = fixed_ms × 5 / N` and writes it into the NED prior to each run so the existing configurator still works as-is.

```bash
# keep 1.5 ms effective interval for all N in the sweep
./run_simulation.py --mode fixed --fixed-ms 1.5

# custom fixed interval and a custom node set
./run_simulation.py --mode fixed --fixed-ms 0.8 --runs 5 10 20 50 100
```

### Restore the original NED

To restore `FakeWireCsmaCaNetwork.ned` from the backup after all runs:

```bash
./run_simulation.py --restore-ned
```

You can also combine with other options, e.g.:

```bash
./run_simulation.py --mode fixed --fixed-ms 1.5 --runs 5 20 50 --restore-ned
```

---

## What the script does

1. **Backs up** `FakeWireCsmaCaNetwork.ned` once as `*.ned.bak` (if not present).
2. For each `N`:

   * Rewrites `int numHosts = default(N);` in the NED.
   * Rewrites `cfg.baseInterval = ...;` in the NED:

     * **Scale:** `baseInterval = base_ms` (seconds)
     * **Fixed:** `baseInterval = fixed_ms × 5 / N` (seconds)
   * Runs OMNeT++:

     ```bash
     opp_run -u Cmdenv \
       -n "<INET/src>;<project>/ned;<project>/TimeSlot" \
       -c Paper_Baseline \
       <project>/ini/omnetpp.ini
     ```
   * Moves `Paper_Baseline-*.{sca,vec,vci,elog,log}` to `ini/results/n{N}/`.
3. Writes a batch log file in `ini/results/`.

---

## Outputs

* Per-run files in:
  `csma_ca_test_for_Ayar_Paper/ini/results/n{N}/Paper_Baseline-#0.{sca,vec,vci,elog,log}`
* Batch logs:
  `csma_ca_test_for_Ayar_Paper/ini/results/batch-<mode>-<timestamp>.txt`

---

## Tips & troubleshooting

* If you change INET location, update `INET_DIR` env var.
* If you want to revert the NED manually, copy back:

  ```
  cp csma_ca_test_for_Ayar_Paper/ned/csma_ca_test_for_Ayar_Paper/FakeWireCsmaCaNetwork.ned.bak \
     csma_ca_test_for_Ayar_Paper/ned/csma_ca_test_for_Ayar_Paper/FakeWireCsmaCaNetwork.ned
  ```
* If you see regex errors when rewriting the NED, make sure you’re using the latest `run_simulation.py` (it uses safe `\g<1>` backreferences).

---

## (Optional) Post-processing

If you also use `efficiency_analysis.py`, run it after a batch to aggregate MAC efficiency, collision probability, and throughput across `n{N}` folders and export CSV/plots into `ini/results/`.

```bash
cd csma_ca_test_for_Ayar_Paper/src/runSimulation
./efficiency_analysis.py
```

---

That’s it. Ping me if you want a ready-made shell wrapper to launch **Scale** and **Fixed** batches back-to-back and label their output folders automatically.
