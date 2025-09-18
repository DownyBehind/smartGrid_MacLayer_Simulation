import re, sys
from pathlib import Path

SLOT = 35.84e-6
TOL = 1e-6  # 1us

pat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs1Timer|backoffTimer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")

def parse(elog: Path):
    prs1=[]; backs=[]; tx=[]
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            phase, name, sm, st, at = m.groups()
            sm = int(sm); st = float(st); at = float(at)
            if name=='prs1Timer' and phase=='ES': prs1.append((sm, st, at))
            elif name=='backoffTimer' and phase=='ES': backs.append((sm, st, at))
            elif name=='txTimer' and phase=='ES': tx.append((sm, st, at))
    return prs1, backs, tx

def main():
    elog = Path('results/General-#0.elog')
    if not elog.exists():
        print('NG: no eventlog')
        sys.exit(1)
    prs1, backs, tx = parse(elog)
    if not prs1 or not tx:
        print('NG: missing prs1/tx events')
        sys.exit(1)
    prs1_at = min(p[2] for p in prs1)
    tx_after = sorted([t for t in tx if t[2] >= prs1_at], key=lambda x:x[2])
    if not tx_after:
        print('NG: no tx after prs1')
        sys.exit(1)
    win_sm, _, tx_at = tx_after[0]
    times = sorted([b[2] for b in backs if b[0]==win_sm and prs1_at <= b[2] <= tx_at])
    if len(times) < 2:
        print('NG: insufficient backoff ticks')
        sys.exit(1)
    diffs = [j-i for i,j in zip(times, times[1:])]
    qdiffs = [round(d/SLOT)*SLOT for d in diffs]
    mean_q = sum(qdiffs)/len(qdiffs)
    if abs(mean_q - SLOT) > TOL:
        print(f'NG: mean slot off (mean_q={mean_q}, SLOT={SLOT})')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()
