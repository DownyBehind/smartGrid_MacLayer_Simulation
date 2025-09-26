import re, sys
from pathlib import Path

SLOT = 35.84e-6
TOL = 1e-6  # 1us

def parse_prs_cycles(cmdenv: Path):
    start_pat = re.compile(r"\[PRS_SCHED\] start cycle gen=(\d+) start=([0-9eE+\-\.]+) prs0Duration=([0-9eE+\-\.]+) prs1Duration=([0-9eE+\-\.]+)")
    end_pat   = re.compile(r"\[PRS_SCHED\] event=(PRS0_END|PRS1_END) gen=(\d+) t=([0-9eE+\-\.]+)")
    cyc = {}
    with cmdenv.open(errors='ignore') as f:
        for line in f:
            m = start_pat.search(line)
            if m:
                g = int(m.group(1)); st=float(m.group(2)); d0=float(m.group(3)); d1=float(m.group(4))
                cyc[g]={'start':st,'prs0End':None,'prs1End':None,'d0':d0,'d1':d1}
                continue
            m = end_pat.search(line)
            if m:
                which=m.group(1); g=int(m.group(2)); t=float(m.group(3))
                if g in cyc:
                    if which=='PRS0_END': cyc[g]['prs0End']=t
                    else: cyc[g]['prs1End']=t
    ordered=[cyc[g] for g in sorted(cyc.keys()) if cyc[g]['prs0End'] and cyc[g]['prs1End']]
    return ordered

def parse_timers(elog: Path):
    pat = re.compile(r"^(ES)\s+id\s+\d+.*\bn\s+(backoffTimer|txTimer|sifsTimer|difsTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    E={'bo':[],'tx':[],'rifs':[],'cifs':[]}
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            _, name, sm, st, at = m.groups()
            sm=int(sm); st=float(st); at=float(at)
            if name=='backoffTimer': E['bo'].append((sm,st,at))
            elif name=='txTimer': E['tx'].append((sm,st,at))
            elif name in ('sifsTimer',): E['rifs'].append((sm,st,at))
            elif name in ('difsTimer',): E['cifs'].append((sm,st,at))
    return E

def main():
    elog = Path('results/General-#0.elog')
    cmdenv = Path('results/cmdenv.log')
    if not elog.exists() or not cmdenv.exists():
        print('NG: logs not found')
        sys.exit(1)
    cycles = parse_prs_cycles(cmdenv)
    if not cycles:
        print('NG: missing PRS cycles')
        sys.exit(1)
    first = cycles[0]
    # duration checks
    d0 = first['prs0End'] - first['start']
    d1 = first['prs1End'] - first['prs0End']
    if not (abs(d0-SLOT)<=TOL and abs(d1-SLOT)<=TOL):
        print(f'NG: PRS durations off (d0={d0}, d1={d1})')
        sys.exit(1)
    # timers path
    E = parse_timers(elog)
    if not E['tx']:
        print('NG: missing TX')
        sys.exit(1)
    txs = sorted([t for t in E['tx'] if t[2]>=first['prs1End']], key=lambda x:x[2])
    if not txs:
        print('NG: no TX after PRS1')
        sys.exit(1)
    tx = txs[0]
    bos = [b for b in E['bo'] if first['prs1End'] <= b[2] <= tx[2]]
    if not bos:
        print('NG: no backoff between PRS1 and TX')
        sys.exit(1)
    rifs = min([s for s in E['rifs'] if s[2]>=tx[2]], key=lambda x:x[2]) if E['rifs'] else None
    cifs = min([d for d in E['cifs'] if d[2]>= (rifs[2] if rifs else tx[2])], key=lambda x:x[2]) if E['cifs'] else None
    if not rifs or not cifs:
        print('NG: missing RIFS/CIFS after TX')
        sys.exit(1)
    # ensure next PRS cycle starts after CIFS
    has_next = any(c['start'] >= cifs[2] for c in cycles[1:])
    if not has_next:
        print('NG: no next PRS cycle after CIFS')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()


