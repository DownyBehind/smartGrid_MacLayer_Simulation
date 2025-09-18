import re, sys
from pathlib import Path

TOL = 1e-6

pat = re.compile(r"^ES\s+id\s+\d+.*\bn\s+(prs1Timer|txTimer)\b.*\bsm\s+(\d+)\b.*\bat\s+([0-9eE+\-\.]+)")

def parse(elog: Path):
    prs1=[]; tx=[]
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            n, sm, at = m.groups(); sm=int(sm); at=float(at)
            if n=='prs1Timer': prs1.append((sm, at))
            else: tx.append((sm, at))
    return prs1, tx

def windows(prs1, tx, max_windows=50):
    if not prs1: return []
    prs1_sorted = sorted(prs1, key=lambda x:x[1])
    wins=[]; i=0
    while i < len(prs1_sorted) and len(wins) < max_windows:
        t0 = prs1_sorted[i][1]
        j=i
        while j < len(prs1_sorted) and abs(prs1_sorted[j][1]-t0) <= TOL:
            j+=1
        t_next = prs1_sorted[j][1] if j < len(prs1_sorted) else float('inf')
        tx_in = sorted([(sm,at) for sm,at in tx if t0 <= at < t_next], key=lambda x:x[1])
        win = tx_in[0][0] if tx_in else None
        wins.append((t0, win))
        i=j
    return wins

def main():
    elog = Path('results/General-#0.elog')
    if not elog.exists():
        print('NG: eventlog not found')
        sys.exit(1)
    prs1, tx = parse(elog)
    if not prs1 or not tx:
        print('NG: missing prs1/tx')
        sys.exit(1)
    wins = windows(prs1, tx, max_windows=30)
    if len(wins) < 5:
        print('NG: insufficient windows')
        sys.exit(1)
    winners = [w for _,w in wins if w is not None]
    if not winners:
        print('NG: no winners detected')
        sys.exit(1)
    distinct = len(set(winners))
    # Expect at least variability due to CAP cycling
    if distinct < 2:
        print('NG: winners not varying enough')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()


