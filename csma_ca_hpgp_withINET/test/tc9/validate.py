import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
elog = TC_DIR/"results"/"General-#0.elog"
lines = elog.read_text(errors='ignore').splitlines() if elog.exists() else []

# find first PRS1 end time
prs1=[]
kvpat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs1Timer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
for ln in lines:
    m = kvpat.search(ln)
    if not m: continue
    ph,n,sm,st,at = m.groups(); sm=int(sm); at=float(at)
    if n=='prs1Timer' and ph=='ES': prs1.append((sm,at))
if not prs1:
    print('No PRS1 events found: FAIL')
    sys.exit(1)

t0 = min(at for _,at in prs1)
# earliest tx after t0
tx=[]
for ln in lines:
    m = kvpat.search(ln)
    if not m: continue
    ph,n,sm,st,at = m.groups(); sm=int(sm); at=float(at)
    if n=='txTimer' and ph=='ES' and at>=t0:
        tx.append((sm,at))
if not tx:
    print('No TX after first PRS1 window: FAIL')
    sys.exit(1)
win_sm = sorted(tx, key=lambda x:x[1])[0][0]

# map to top node
mc_pat = re.compile(r"^MC\s+id\s+(\d+)\s+c\s+([^\s]+)\s+t\s+[^\s]+\s+pid\s+(\d+)\s+n\s+([^\s]+)")
mods={}
for ln in lines:
    m = mc_pat.search(ln)
    if m:
        mid, cls, pid, name = m.groups()
        mods[int(mid)]={'cls':cls,'pid':int(pid),'name':name}

def resolve_top(mid:int):
    seen=set(); cur=mid
    while cur in mods and cur not in seen:
        seen.add(cur); info=mods[cur]; name=info['name']
        if name.startswith('ev[') or name=='evse': return name
        cur=info['pid']
    return None

win_top = resolve_top(win_sm)
if win_top == 'ev[0]':
    print('Winner is CA3 as expected: PASS')
    sys.exit(0)
print(f'Winner is not CA3 (winner={win_top}): FAIL')
sys.exit(1)
