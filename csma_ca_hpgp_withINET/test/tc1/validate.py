import re, sys
from pathlib import Path

TOL = 1e-6  # 1us
SLOT = 35.84e-6

def parse_events(elog: Path):
    prs = []  # (slot, st, at)
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

def main():
    elog = Path('results/General-#0.elog')
    if not elog.exists():
        print('NG: eventlog not found')
        sys.exit(1)
    prs, back, tx = parse_events(elog)
    if len(prs) < 2 or not back or not tx:
        print('NG: missing events')
        sys.exit(1)
    # Check PRS durations
    p0 = next((p for p in prs if p[0]=='prs0Timer'), None)
    p1 = next((p for p in prs if p[0]=='prs1Timer'), None)
    if not p0 or not p1:
        print('NG: missing PRS0/PRS1')
        sys.exit(1)
    d0 = p0[2]-p0[1]
    d1 = p1[2]-p1[1]
    if not (abs(d0-SLOT) <= TOL and abs(d1-SLOT) <= TOL):
        print(f'NG: PRS durations off (d0={d0}, d1={d1})')
        sys.exit(1)
    # Find first PRS1 completion time and subsequent backoff sequence for same module
    prs1_at = p1[2]
    # pick first tx after PRS1
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
    # Check each backoff ES at increments of SLOT from previous ES
    times = [b[1] for b in backs]
    ok = all(abs((t2 - t1) - SLOT) <= TOL for t1,t2 in zip(times, times[1:]))
    if not ok:
        print('NG: backoff slot increments not matching slotTime')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()
