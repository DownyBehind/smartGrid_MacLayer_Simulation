import re, sys
from pathlib import Path
TOL=1e-6
pat = re.compile(r"^ES\s+id\s+\d+.*\bn\s+(prs1Timer|txTimer)\b.*\bsm\s+(\d+)\b.*\bat\s+([0-9eE+\-\.]+)")

def read(elog):
    prs1=[]; tx=[]
    with open(elog, errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            n, sm, at = m.groups(); sm=int(sm); at=float(at)
            (prs1 if n=='prs1Timer' else tx).append((sm, at))
    return prs1, tx

def main():
    elog = 'results/General-#0.elog'
    prs1, tx = read(elog)
    if not prs1 or not tx:
        print('NG: missing prs1/tx events')
        sys.exit(1)
    t0 = min(at for _,at in prs1)
    contenders = {sm for sm,at in prs1 if abs(at-t0)<=TOL}
    tx_after = sorted([(sm,at) for sm,at in tx if at>=t0], key=lambda x:x[1])
    if not tx_after:
        print('NG: no tx after prs1 window')
        sys.exit(1)
    if tx_after[0][0] not in contenders:
        print('NG: winner not among first-window contenders')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()
