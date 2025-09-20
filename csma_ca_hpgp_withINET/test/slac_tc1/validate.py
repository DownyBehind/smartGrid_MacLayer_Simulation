import re, sys
from pathlib import Path

def parse_seq_simout(simout: Path):
    order=[]
    # capture node for filtering; focus on EV node events only
    pat = re.compile(r"^\[INFO\]\s+SLAC_LOG\s+stage=([A-Z_]+)\s+node=([^\s]+).*t=([0-9eE+\-\.]+)")
    if not simout.exists():
        return []
    with simout.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if m:
                stg, node, t = m.groups()
                if node.startswith('ev['):
                    order.append((float(t), stg))
    # preserve original appearance order (do not sort by time; ties may scramble)
    return [n for _,n in order]

def parse_seq(elog: Path):
    names = {"START_ATTEN","M_SOUND","ATTEN_CHAR","VALIDATE","SLAC_DONE"}
    order=[]
    pat = re.compile(r"^ES\s+id\s+\d+.*\bn\s+([A-Z_]+)\b.*\bat\s+([0-9eE+\-\.]+)")
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            n, at = m.groups(); at=float(at)
            if n in names:
                order.append((at, n))
    return [n for _,n in sorted(order)]

def main():
    # Prefer sim.out SLAC_LOG; fallback to .elog token names if available
    simout = Path('results/sim.out')
    seq = parse_seq_simout(simout)
    if not seq:
        elog = Path('results/General-#0.elog')
        if not elog.exists():
            print('NG: neither sim.out nor eventlog has SLAC markers')
            sys.exit(1)
        seq = parse_seq(elog)
    # collapse consecutive duplicates (e.g., multiple START_ATTEN)
    collapsed = []
    for n in seq:
        if not collapsed or collapsed[-1] != n:
            collapsed.append(n)
    want = ["START_ATTEN","M_SOUND","ATTEN_CHAR","VALIDATE","SLAC_DONE"]
    # trim leading until first START_ATTEN
    s0 = [n for n in collapsed if n in set(want)]
    if 'START_ATTEN' in s0:
        i0 = s0.index('START_ATTEN')
        s = s0[i0:]
    else:
        s = s0
    # check subsequence order
    ok = True
    it = iter(s)
    for w in want:
        for x in it:
            if x == w:
                break
        else:
            ok = False
            break
    if not ok:
        print('NG: wrong SLAC sequence order')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()

