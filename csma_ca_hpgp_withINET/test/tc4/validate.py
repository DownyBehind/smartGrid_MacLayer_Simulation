import re, sys
from pathlib import Path

SLOT = 35.84e-6
TOL = 1e-6  # 1us

pat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs0Timer|prs1Timer|backoffTimer|txTimer|rifsTimer|cifsTimer|sifsTimer|difsTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")

def parse(elog: Path):
    E = { 'prs0':[], 'prs1':[], 'bo':[], 'tx':[], 'rifs':[], 'cifs':[] }
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            ph, name, sm, st, at = m.groups()
            sm = int(sm); st = float(st); at = float(at)
            if ph!='ES':
                continue
            if name=='prs0Timer':
                E['prs0'].append((sm,st,at))
            elif name=='prs1Timer':
                E['prs1'].append((sm,st,at))
            elif name=='backoffTimer':
                E['bo'].append((sm,st,at))
            elif name=='txTimer':
                E['tx'].append((sm,st,at))
            elif name in ('rifsTimer','sifsTimer'):
                E['rifs'].append((sm,st,at))
            elif name in ('cifsTimer','difsTimer'):
                E['cifs'].append((sm,st,at))
    return E

def main():
    elog = Path('results/General-#0.elog')
    if not elog.exists():
        print('NG: eventlog not found')
        sys.exit(1)
    E = parse(elog)
    if not E['prs0'] or not E['prs1'] or not E['tx']:
        print('NG: missing core events')
        sys.exit(1)
    # Check first full cycle
    t0 = min(at for _,_,at in E['prs0'])
    # nearest sequence boundaries
    prs0 = min([p for p in E['prs0'] if abs(p[2]-t0)<=SLOT], key=lambda x:x[2])
    prs1 = min([p for p in E['prs1'] if p[2]>=prs0[2]], key=lambda x:x[2])
    txs = sorted([t for t in E['tx'] if t[2]>=prs1[2]], key=lambda x:x[2])
    if not txs:
        print('NG: no TX after PRS1')
        sys.exit(1)
    tx = txs[0]
    # Backoff existence between PRS1 and TX
    bos = [b for b in E['bo'] if prs1[2] <= b[2] <= tx[2]]
    if not bos:
        print('NG: no backoff between PRS1 and TX')
        sys.exit(1)
    # Durations checks for PRS0/PRS1 ~ SLOT
    d0 = prs0[2]-prs0[1]
    d1 = prs1[2]-prs1[1]
    if not (abs(d0-SLOT)<=TOL and abs(d1-SLOT)<=TOL):
        print(f'NG: PRS durations off (d0={d0}, d1={d1})')
        sys.exit(1)
    # Post-TX: RIFS, then CIFS
    rifs = min([s for s in E['rifs'] if s[2]>=tx[2]], key=lambda x:x[2]) if E['rifs'] else None
    cifs = min([d for d in E['cifs'] if rifs and d[2]>=rifs[2] or (not rifs and d[2]>=tx[2])], key=lambda x:x[2]) if E['cifs'] else None
    if not rifs or not cifs:
        print('NG: missing RIFS/CIFS after TX')
        sys.exit(1)
    # Next cycle PRS0 after CIFS
    next_prs0s = [p for p in E['prs0'] if p[2] >= cifs[2]]
    if not next_prs0s:
        print('NG: no PRS0 after DIFS')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()


