import re, sys
from pathlib import Path

TOL = 1e-6

def parse_prs1_windows(cmdenv: Path, max_windows=50):
    # Build windows from PRS_SCHED end markers only (flexible)
    ends = []
    end_pat = re.compile(r"PRS1_END.*?t=([0-9eE+\-\.]+)")
    with cmdenv.open(errors='ignore') as f:
        for line in f:
            m = end_pat.search(line)
            if m:
                try:
                    ends.append(float(m.group(1)))
                except ValueError:
                    continue
    prs1_ends = ends[:max_windows]
    return prs1_ends

def parse_tx(elog: Path):
    pat = re.compile(r"^ES\s+id\s+\d+.*\bn\s+txTimer\b.*\bsm\s+(\d+)\b.*\bat\s+([0-9eE+\-\.]+)")
    pat2 = re.compile(r"txTimer.*sm\s+(\d+).*at\s+([0-9eE+\-\.]+)")
    tx=[]
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m:
                m = pat2.search(line)
            if not m:
                continue
            sm, at = m.groups(); tx.append((int(sm), float(at)))
    return tx

def windows(prs1_ends, tx):
    if not prs1_ends: return []
    wins=[]
    for i, t0 in enumerate(prs1_ends):
        t_next = prs1_ends[i+1] if i+1 < len(prs1_ends) else float('inf')
        tx_in = sorted([(sm,at) for sm,at in tx if t0 <= at < t_next], key=lambda x:x[1])
        win = tx_in[0][0] if tx_in else None
        wins.append((t0, win))
    return wins

def main():
    cmdenv = Path('results/cmdenv.log')
    elog = Path('results/General-#0.elog')
    if not cmdenv.exists() or not elog.exists():
        print('NG: logs not found')
        sys.exit(1)
    prs1_ends = parse_prs1_windows(cmdenv, max_windows=30)
    tx = parse_tx(elog)
    # debug counters
    print(f'DBG: prs1_ends_count={len(prs1_ends)} tx_count={len(tx)}')
    if not prs1_ends or not tx:
        print('NG: missing prs1/tx')
        sys.exit(1)
    wins = windows(prs1_ends, tx)
    if len(wins) < 5:
        print('NG: insufficient windows')
        sys.exit(1)
    winners = [w for _,w in wins if w is not None]
    if not winners:
        print('NG: no winners detected')
        sys.exit(1)
    distinct = len(set(winners))
    if distinct < 2:
        print('NG: winners not varying enough')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()


