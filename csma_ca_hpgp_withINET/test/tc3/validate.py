import re, sys
from pathlib import Path

SLOT = 35.84e-6
TOL = 1e-6  # 1us

def parse_prs1_end_from_cmdenv(cmdenv: Path):
    pat = re.compile(r"PRS1_END.*?t=([0-9eE+\-\.]+)")
    with cmdenv.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    continue
    return None

def parse_backoff_tx(elog: Path):
    pat = re.compile(r"^(ES)\s+id\s+\d+.*\bn\s+(backoffTimer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    backs=[]; tx=[]
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            _, name, sm, st, at = m.groups()
            sm = int(sm); st = float(st); at = float(at)
            if name=='backoffTimer': backs.append((sm, st, at))
            else: tx.append((sm, st, at))
    return backs, tx

def main():
    elog = Path('results/General-#0.elog')
    cmdenv = Path('results/cmdenv.log')
    if not elog.exists() or not cmdenv.exists():
        print('NG: missing logs')
        sys.exit(1)
    prs1_at = parse_prs1_end_from_cmdenv(cmdenv)
    if prs1_at is None:
        print('NG: missing PRS1_END')
        sys.exit(1)
    backs, tx = parse_backoff_tx(elog)
    if not backs or not tx:
        print('NG: missing backoff/tx events')
        sys.exit(1)
    tx_after = sorted([t for t in tx if t[2] >= prs1_at], key=lambda x:x[2])
    if not tx_after:
        print('NG: no tx after PRS1_END')
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
