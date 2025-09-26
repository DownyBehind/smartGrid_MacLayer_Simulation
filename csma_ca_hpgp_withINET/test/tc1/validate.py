import re, sys
from pathlib import Path

TOL = 1e-6  # 1us
SLOT = 35.84e-6

def parse_events(elog: Path):
    prs = []  # (slot, st, at) -- kept for backward compat, may be empty now
    back = [] # (st, at, sm)
    tx = []   # (st, at, sm)
    pat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs0Timer|prs1Timer|backoffTimer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            phase, name, sm, st, at = m.groups()
            sm = int(sm); st = float(st); at = float(at)
            if name in ('prs0Timer','prs1Timer') and phase=='ES':
                prs.append((name, st, at))
            elif name=='backoffTimer' and phase=='ES':
                back.append((st, at, sm))
            elif name=='txTimer' and phase=='ES':
                tx.append((st, at, sm))
    return prs, back, tx

def parse_prs_from_cmdenv(cmdenv: Path):
    # Extract PRS cycle start and PRS0/PRS1 end timestamps from [PRS_SCHED] lines
    start_pat = re.compile(r"\[PRS_SCHED\] start cycle gen=(\d+) start=([0-9eE+\-\.]+) prs0Duration=([0-9eE+\-\.]+) prs1Duration=([0-9eE+\-\.]+)")
    end_pat   = re.compile(r"\[PRS_SCHED\] event=(PRS0_END|PRS1_END) gen=(\d+) t=([0-9eE+\-\.]+)")
    cycles = {}
    with cmdenv.open(errors='ignore') as f:
        for line in f:
            m = start_pat.search(line)
            if m:
                gen = int(m.group(1)); st = float(m.group(2)); d0 = float(m.group(3)); d1 = float(m.group(4))
                cycles[gen] = { 'start': st, 'prs0Dur': d0, 'prs1Dur': d1, 'prs0End': None, 'prs1End': None }
                continue
            m = end_pat.search(line)
            if m:
                which = m.group(1); gen = int(m.group(2)); t = float(m.group(3))
                if gen in cycles:
                    if which=='PRS0_END': cycles[gen]['prs0End'] = t
                    else: cycles[gen]['prs1End'] = t
    # pick first complete cycle
    for gen in sorted(cycles.keys()):
        c = cycles[gen]
        if c['prs0End'] is not None and c['prs1End'] is not None:
            return c
    return None

def main():
    elog = Path('results/General-#0.elog')
    cmdenv = Path('results/cmdenv.log')
    if not elog.exists():
        print('NG: eventlog not found')
        sys.exit(1)
    if not cmdenv.exists():
        print('NG: cmdenv.log not found')
        sys.exit(1)

    prs, back, tx = parse_events(elog)
    # PRS: prefer scheduler-driven evidence from cmdenv.log
    cyc = parse_prs_from_cmdenv(cmdenv)
    if not cyc:
        # fallback to legacy timer evidence, but allow empty prs list
        print('NG: missing PRS scheduler evidence')
        sys.exit(1)

    # Check PRS durations against scheduler-reported durations
    d0 = cyc['prs0End'] - cyc['start']
    d1 = cyc['prs1End'] - cyc['prs0End']
    if not (abs(d0 - SLOT) <= TOL and abs(d1 - SLOT) <= TOL):
        print(f'NG: PRS durations off (d0={d0}, d1={d1})')
        sys.exit(1)

    # Backoff/tx path checks (from eventlog)
    if not back or not tx:
        print('NG: missing backoff/tx events')
        sys.exit(1)
    # pick first PRS1 completion time
    prs1_at = cyc['prs1End']
    tx_after = [t for t in tx if t[1] >= prs1_at]
    if not tx_after:
        print('NG: no TX after PRS1')
        sys.exit(1)
    tx0 = tx_after[0]
    sm = tx0[2]
    backs = [b for b in back if prs1_at <= b[1] <= tx0[1] and b[2]==sm]
    if not backs:
        print('NG: no backoff on path to TX')
        sys.exit(1)
    times = [b[1] for b in backs]
    ok = all(abs((t2 - t1) - SLOT) <= TOL for t1,t2 in zip(times, times[1:]))
    if not ok:
        print('NG: backoff slot increments not matching slotTime')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()
