#!/usr/bin/env python3
import os, csv, time, yaml, random, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ENV_PATH = BASE/"env"/"research.env"
RESULTS = BASE/"results"
RAW = RESULTS/"raw"
LOG = RESULTS/"log"

# Ensure dirs
RESULTS.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
LOG.mkdir(parents=True, exist_ok=True)

# Load env (read-only for now)
ENV = {}
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        ENV[k] = v

# Useful paths (will be used in next steps)
SCEN = BASE/"scenarios"/"worstcase_slac_dc"/"omnetpp.ini"
MATRIX = BASE/"matrix"/"experiments.yaml"

# Minimal summary header: create if missing/empty
summary_csv = RESULTS/"summary.csv"
if (not summary_csv.exists()) or summary_csv.stat().st_size == 0:
    with open(summary_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run","numEvs","seed","repeat","status","dcMissRate","dcDelayAvg","dcDelayP95","slacDoneRate"]) 

# Single-run preparation (no execution yet)
M = yaml.safe_load(MATRIX.read_text()) if MATRIX.exists() else {"numEvs":[8],"seedSet":[1],"simTimeS":10}
# 단일 실행: ENV(NUM_EVS) 우선, 없으면 matrix, 없으면 기본 8
env_num_evs = os.environ.get('NUM_EVS') or ENV.get('NUM_EVS')
if env_num_evs:
    try:
        num_evs = int(env_num_evs)
    except Exception:
        num_evs = int(max(M.get('numEvs',[8])))
else:
    num_evs = int(max(M.get('numEvs',[8])))
seed_cfg = M.get('seedSet',[1])[0]
try:
    seed = int(seed_cfg)
except Exception:
    seed = None
# Allow ENV override for auto/random seed
seed_override_raw = os.environ.get('SEED_SET', ENV.get('SEED_SET','')).strip()
seed_override = seed_override_raw.lower()
if seed_override in ('auto','random'):
    seed = int(time.time() * 1000) ^ os.getpid() ^ random.randint(1, 2**31-1)
else:
    # If numeric provided, use it
    try:
        if seed_override_raw:
            seed = int(seed_override_raw)
    except Exception:
        pass
if seed is None:
    seed = int(time.time() * 1000) & 0x7fffffff

# Support fractional SIM_TIME_S
sim_time_s_str = os.environ.get('SIM_TIME_S', ENV.get('SIM_TIME_S', str(M.get('simTimeS', 100))))
try:
    sim_time_s = float(sim_time_s_str)
except Exception:
    sim_time_s = float(M.get('simTimeS', 100))

run_id = f"ne{num_evs}_seed{seed}_r1_{int(time.time())}"
# Requested log folder format: time_date_mm_year_ev수_evse수
tm = time.localtime()
folder_name = f"{tm.tm_hour:02d}{tm.tm_min:02d}{tm.tm_sec:02d}_{tm.tm_mday:02d}_{tm.tm_mon:02d}_{tm.tm_year}_ev{num_evs}_evse1"
RUN_RAW = LOG/folder_name
RUN_RAW.mkdir(parents=True, exist_ok=True)
run_ini = RUN_RAW/"omnetpp_run.ini"
RUN_RESULTS = (RUN_RAW/"results").resolve()
RUN_RESULTS.mkdir(parents=True, exist_ok=True)

# Project/library roots
PR_RAW = ENV.get('PROJECT_ROOT','')
IR_RAW = ENV.get('INET_ROOT','')
PROJECT_ROOT = os.path.abspath(PR_RAW)
INET_ROOT = os.path.abspath(IR_RAW)

# Helper: build sanitized NED paths (exclude '.' and doc paths and non-existing)
def build_sanitized_ned_paths():
    candidates = [
        PROJECT_ROOT,
        str(Path(INET_ROOT)/"src"),
        str(Path(PROJECT_ROOT)/"test"/"common"),
        str(BASE/"scenarios"/"worstcase_slac_dc"),
    ]
    env_np = ENV.get('NED_PATHS', '')
    if env_np:
        for p in env_np.split(':'):
            p = os.path.expandvars(p)
            if not p or p == '.' or '/doc/' in p:
                continue
            if p not in candidates:
                candidates.append(p)
    # Filter non-existing paths
    candidates = [p for p in candidates if p and os.path.isdir(p)]
    # De-dup keep order
    seen = set()
    safe = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            safe.append(p)
    return ":".join(safe)


def write_run_ini(base_ini: Path, out_ini: Path, num_evs: int, seed: int, sim_time_s: float):
    # Load scenario and override in-place to avoid multiple [General] sections
    lines = base_ini.read_text().splitlines()
    new_lines = []
    abs_results_dir = (out_ini.parent/"results").resolve()
    sanitized_ned = build_sanitized_ned_paths()
    had_ned = False
    for ln in lines:
        s = ln.strip()
        if s.startswith('**.numEvs'):
            new_lines.append(f"**.numEvs = {num_evs}")
        elif s.startswith('sim-time-limit'):
            new_lines.append(f"sim-time-limit = {sim_time_s}s")
        elif s.startswith('result-dir'):
            new_lines.append(f"result-dir = {abs_results_dir}")
        elif s.startswith('ned-path'):
            new_lines.append(f"ned-path = {sanitized_ned.replace(':',';')}")
            had_ned = True
        elif s.startswith('record-scalar'):
            # OMNeT++ 6: unknown option; drop if present
            continue
        elif s.startswith('scalar-recording'):
            # Replace global with per-object rule later
            continue
        else:
            new_lines.append(ln)
    if not had_ned:
        new_lines.append(f"ned-path = {sanitized_ned.replace(':',';')}")
    # Ensure seed-set and dcRspDelay overrides exist (append once)
    new_lines.append("# --- orchestrator overrides ---")
    new_lines.append(f"seed-set = {seed}")
    new_lines.append("**.evse.slac.dcRspDelay = 5ms")
    # Assign deterministic EV nodeIds for per-destination accounting
    new_lines.append("**.evse.slac.nodeId = 1")
    for i in range(num_evs):
        new_lines.append(f"**.ev[{i}].slac.nodeId = {i+2}")
    # Ensure recording flags present
    if not any(l.strip().startswith('**.statistic-recording') for l in new_lines):
        new_lines.append("**.statistic-recording = true")
    if not any(l.strip().startswith('record-eventlog') for l in new_lines):
        new_lines.append("record-eventlog = true")
    # OMNeT++ 6.1 requires per-object form
    if not any(l.strip().startswith('**.scalar-recording') for l in new_lines):
        new_lines.append("**.scalar-recording = true")
    # Also force global recording modes to include scalars
    if not any(l.strip().startswith('**.result-recording-modes') for l in new_lines):
        new_lines.append("**.result-recording-modes = all")
    # Enforce absolute result-dir again at the end to win precedence
    new_lines.append(f"result-dir = {abs_results_dir}")
    # Strong enabling for modules we own (per-object form, OMNeT++ 6.1)
    new_lines.append("**.slac.scalar-recording = true")
    new_lines.append("**.plc.mac.scalar-recording = true")
    new_lines.append("**.plc.phy.scalar-recording = true")
    new_lines.append("**.slac.result-recording-modes = all")
    new_lines.append("**.plc.mac.result-recording-modes = all")
    new_lines.append("**.plc.phy.result-recording-modes = all")
    # Optional: enable explicit collision model via ENV or default(false)
    enable_collision = os.environ.get('ENABLE_COLLISION_MODEL', ENV.get('ENABLE_COLLISION_MODEL','false')).strip().lower() in ('1','true','yes','on')
    new_lines.append(f"**.plc.phy.enableCollisionModel = {'true' if enable_collision else 'false'}")
    # Do not override output-scalar-file (avoid '#' comment confusion)
    # Add more concrete module paths for recording
    new_lines.append("TestBus.ev[*].slac.scalar-recording = true")
    new_lines.append("TestBus.evse.slac.scalar-recording = true")
    new_lines.append("TestBus.ev[*].plc.mac.scalar-recording = true")
    new_lines.append("TestBus.ev[*].plc.phy.scalar-recording = true")
    new_lines.append("TestBus.evse.plc.mac.scalar-recording = true")
    new_lines.append("TestBus.evse.plc.phy.scalar-recording = true")
    # Make Cmdenv print status so tail shows termination progress
    new_lines.append("cmdenv-status-frequency = 1s")
    out_ini.write_text("\n".join(new_lines) + "\n")

write_run_ini(SCEN, run_ini, num_evs, seed, sim_time_s)

print(str(summary_csv))

# Cleanup old raw directories (requested: remove unnecessary)
try:
    if RAW.exists():
        for d in RAW.iterdir():
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
except Exception:
    pass

# Execute one short run and append one-line summary
NED_PATHS_RAW = ENV.get('NED_PATHS','')
LIB_PATH = ENV.get('LIB_PATH','')
INET_LIB = ENV.get('INET_LIB','')
TIMEOUT = int(ENV.get('TEST_TIMEOUT_SECONDS','600') or 600)

import os
# Expand library paths using ENV-style placeholders
LIB_PATH_RAW = ENV.get('LIB_PATH','')
INET_LIB_RAW = ENV.get('INET_LIB','')
LIB_PATH = os.path.abspath(LIB_PATH_RAW.replace('$PROJECT_ROOT', PROJECT_ROOT).replace('$INET_ROOT', INET_ROOT))
INET_LIB = os.path.abspath(INET_LIB_RAW.replace('$PROJECT_ROOT', PROJECT_ROOT).replace('$INET_ROOT', INET_ROOT))
if not os.path.isfile(LIB_PATH):
    # fallback to default project path
    LIB_PATH = str(Path(PROJECT_ROOT)/'libcsma_ca_hpgp_withINET.so')
if not os.path.isfile(INET_LIB):
    INET_LIB = str(Path(INET_ROOT)/'out'/'clang-release'/'src'/'libINET.so')

NED_PATHS = build_sanitized_ned_paths()

lib_dir = str(Path(LIB_PATH).parent)
inet_dir = str(Path(INET_LIB).parent)
ABS_RESULTS = (RUN_RAW/"results").resolve()
cmd = (
    f"cd {RUN_RAW} && "
    f"export LD_LIBRARY_PATH=\"{lib_dir}:{inet_dir}:$LD_LIBRARY_PATH\"; "
    f"timeout {TIMEOUT}s opp_run -u Cmdenv -c General -r 0 --result-dir {ABS_RESULTS} -n \"{NED_PATHS}\" -l \"{LIB_PATH}\" -l \"{INET_LIB}\" -f \"{run_ini.name}\" > sim.out 2>&1"
)
status = 'OK'
import subprocess
heartbeat_path = RUN_RAW/"heartbeat.log"
start_ts = time.time()
def _heartbeat_loop():
    while True:
        try:
            with open(heartbeat_path, 'a') as hf:
                hf.write(f"{time.time()} RUNNING\n")
        except Exception:
            pass
        time.sleep(1)
        if time.time() - start_ts > TIMEOUT + 5:
            break

import threading
hb = threading.Thread(target=_heartbeat_loop, daemon=True)
hb.start()

try:
    subprocess.check_output(['bash','-lc', cmd], stderr=subprocess.STDOUT)
except subprocess.CalledProcessError:
    status = 'ERR'

# If .sca exists, treat as OK regardless of exit code
sca_exists = (RUN_RAW/"results").exists() and any((RUN_RAW/"results").glob("*.sca"))
if sca_exists:
    status = 'OK'

def parse_metrics(run_dir: Path):
    # Parse .sca totals for DC and sim.out for SLAC_DONE (EV modules only)
    results_dir = run_dir/"results"
    req_total = rsp_total = 0
    delays = []
    p95s = []
    if results_dir.exists():
        for p in results_dir.glob("*.sca"):
            for raw in p.read_text(errors='ignore').splitlines():
                s = raw.strip()
                # Expect lines like: scalar <module> <name> <value>
                if not s.startswith('scalar '):
                    continue
                parts = s.split()
                if len(parts) < 4:
                    continue
                module = parts[1]
                name = parts[2].strip('"')
                # Merge the case when name has spaces (not used for our dc* metrics)
                try:
                    val = float(parts[3])
                except Exception:
                    continue
    # EV-only aggregation (legacy fields retained for compatibility)
                if '.ev[' not in module:
                    continue
                if name == 'dcReqSent':
                    req_total += int(val)
                elif name == 'dcRspRecv':
                    rsp_total += int(val)
                elif name == 'dcLatencyAvg(s)':
                    delays.append(val)
                elif name == 'dcLatencyP95(s)':
                    p95s.append(val)
    # Miss rate
    miss_rate = 0.0
    if req_total > 0:
        miss_rate = max(0.0, 1.0 - (rsp_total / req_total))
    # Avg delay
    delay_avg = sum(delays)/len(delays) if delays else ''
    delay_p95 = sum(p95s)/len(p95s) if p95s else ''
    # SLAC done rate from sim.out
    done_nodes = set()
    total_nodes = set()
    simout = run_dir/"sim.out"
    if simout.exists():
        import re
        pat = re.compile(r"SLAC_LOG\s+stage=SLAC_DONE\s+node=([^\s]+)")
        evpat = re.compile(r"SLAC_LOG\s+stage=START_ATTEN\s+node=([^\s]+)")
        for line in simout.read_text(errors='ignore').splitlines():
            m = pat.search(line)
            if m:
                done_nodes.add(m.group(1))
            m2 = evpat.search(line)
            if m2:
                total_nodes.add(m2.group(1))
    slac_done_rate = ''
    if total_nodes:
        slac_done_rate = len(done_nodes)/len(total_nodes)
    return miss_rate, delay_avg, delay_p95, slac_done_rate


dcMissRate, dcDelayAvg, dcDelayP95, slacDoneRate = parse_metrics(RUN_RAW)

# Replace legacy summary.csv with v2 content (rename requested)
summary_csv.unlink(missing_ok=True)

# Extended summary_v2 with new metrics
summary_v2 = RESULTS/"summary_v2.csv"
if (not summary_v2.exists()) or summary_v2.stat().st_size == 0:
    with open(summary_v2, 'w', newline='') as f2:
        w2 = csv.writer(f2)
        w2.writerow(["run","numEvs","seed","repeat","status","dcDeadlineMissRate","DcDeadlineMissCount","DcReqCnt","DcResCnt","DcAirtimeAvg","DcAirtimeP95","dcReqDelayRate","slacDoneRate","SlacAllDoneTime(s)","BackoffContentionCount"]) 

def parse_extended(run_dir: Path, expected_evs: int):
    results_dir = run_dir/"results"
    missRate = airtimeAvg = airtimeP95 = reqDelayRate = ''
    missCount = reqCnt = resCnt = 0
    collisions_total = 0
    slac_all_done_time = ''
    if results_dir.exists():
        for p in results_dir.glob("*.sca"):
            for raw in p.read_text(errors='ignore').splitlines():
                s = raw.strip()
                if not s.startswith('scalar '):
                    continue
                parts = s.split()
                if len(parts) < 4:
                    continue
                module = parts[1]
                name = parts[2].strip('"')
                try:
                    val = float(parts[3])
                except Exception:
                    continue
                # EV-only metrics
                if '.ev[' in module:
                    if name == 'DcDeadlineMissRate': missRate = val
                    elif name == 'DcDeadlineMissCount': missCount += int(val)
                    elif name == 'DcReqCnt': reqCnt += int(val)
                    elif name == 'DcResCnt': resCnt += int(val)
                    elif name == 'DcAirtimeAvg(s)': airtimeAvg = val if airtimeAvg=='' else (airtimeAvg+val)/2
                    elif name == 'DcAirtimeP95(s)': airtimeP95 = val if airtimeP95=='' else (airtimeP95+val)/2
                    elif name == 'dcReqDelayRate': reqDelayRate = val if reqDelayRate=='' else (reqDelayRate+val)/2
                # Collisions from all MACs (EV and EVSE)
                if module.endswith('.plc.mac') and name == 'collisions':
                    collisions_total += int(val)
    # Parse SLAC all-done time from sim.out
    simout = run_dir/"sim.out"
    if simout.exists():
        import re
        pat = re.compile(r"SLAC_LOG\s+stage=SLAC_DONE\s+node=([^\s]+).*?t=([0-9eE+\.-]+)")
        macdel = re.compile(r"Delivering frame up to upper layer: mod=([^\s]+).*?name=SLAC_MATCH_CNF.*?dest=(\d+).+t=([0-9eE+\.-]+)")
        bc0 = re.compile(r"OBS\s+MAC_BC0\s+node=.*?t=([0-9eE+\.-]+)")
        intent = re.compile(r"OBS\s+PRS_INTENT\s+node=([^\s]+)\s+ca=(\d)\s+send0=(\d)\s+send1=(\d)\s+t=([0-9eE+\.-]+)")
        done_times = {}
        bc0_times = []
        prs_intents = []
        for line in simout.read_text(errors='ignore').splitlines():
            m = pat.search(line)
            if m:
                node = m.group(1)
                try:
                    t = float(m.group(2))
                except Exception:
                    continue
                done_times[node] = t
            m4 = macdel.search(line)
            if m4:
                mod = m4.group(1)  # e.g., TestBus.ev[2].plc.mac
                dest = m4.group(2)
                try:
                    tcnf = float(m4.group(3))
                except Exception:
                    continue
                # Extract ev index from mod and map to nodeId (index+2)
                import re as _re
                mm = _re.search(r"ev\[(\d+)\]", mod)
                if mm:
                    evidx = int(mm.group(1))
                    nodeId = evidx + 2
                    if str(nodeId) == dest:
                        # This CNF is addressed to this EV → use CNF time as SLAC_DONE time
                        done_times[f"ev[{evidx}]"] = tcnf
            m2 = bc0.search(line)
            if m2:
                try:
                    bc0_times.append(float(m2.group(1)))
                except Exception:
                    pass
            m3 = intent.search(line)
            if m3:
                try:
                    node_i = m3.group(1)
                    ca_i = int(m3.group(2))
                    t_i = float(m3.group(5))
                    prs_intents.append((t_i, ca_i, node_i))
                except Exception:
                    pass
        ev_nodes = [k for k in done_times.keys() if 'ev[' in k]
        if len(ev_nodes) == expected_evs:
            slac_all_done_time = max(done_times[k] for k in ev_nodes)
        # PRS-based contention: bin PRS intents into PRS window (PRS0+PRS1) and count bins with >=2 participants
        prs_window = 2 * 35.84e-6  # seconds
        prs_bins = {}
        for t_i, ca_i, node_i in prs_intents:
            b = int(t_i / prs_window)
            prs_bins.setdefault(b, set()).add(node_i)
        prs_contention = sum(1 for b, nodes in prs_bins.items() if len(nodes) >= 2)
        # Use PRS-based contention instead of BC0 heuristic
        collisions_total = prs_contention
    return missRate, missCount, reqCnt, resCnt, airtimeAvg, airtimeP95, reqDelayRate, slac_all_done_time, collisions_total

mRate, mCount, rReq, rRes, atAvg, atP95, reqDelay, slacAllDone, dcCollisions = parse_extended(RUN_RAW, num_evs)
with open(summary_v2, 'a', newline='') as f2:
    w2 = csv.writer(f2)
    w2.writerow([run_id, num_evs, seed, 1, status, mRate, mCount, rReq, rRes, atAvg, atP95, reqDelay, slacDoneRate, slacAllDone, dcCollisions])

print(str(RUN_RAW/"sim.out"))
