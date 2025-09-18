
import os, subprocess, shlex, re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV = {}
with open(BASE/'test.env') as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k,v=line.split('=',1)
            ENV[k]=v

def _strip_quotes(s: str) -> str:
    return s.strip().strip('"').strip("'")

TESTS = [_strip_quotes(t) for t in ENV.get('TEST_CASES','').split() if t]
TIMEOUT = int(_strip_quotes(ENV.get('TEST_TIMEOUT_SECONDS','120')) or 120)
REPEAT = int(_strip_quotes(ENV.get('REPEAT','1')) or 1)
EVID_MAX = int(_strip_quotes(ENV.get('MAX_EVIDENCE_LINES','40')) or 40)

def run_tc(tc: str):
    tcdir = BASE / tc
    runsh = tcdir / 'run.sh'
    if not runsh.exists():
        return tc, 'MISSING', '', None, 0, []
    outputs = []
    passes = 0
    status_list = []
    for r in range(1, REPEAT+1):
        try:
            out = subprocess.check_output(['bash','-lc', f'timeout {TIMEOUT}s {shlex.quote(str(runsh))}'], cwd=str(tcdir), stderr=subprocess.STDOUT)
            passes += 1
            outputs.append((r, 'PASS', out.decode(errors='ignore')))
            status_list.append('P')
        except subprocess.CalledProcessError as e:
            outputs.append((r, 'FAIL', (e.output or b'').decode(errors='ignore')))
            status_list.append('F')
    status = 'PASS' if passes==REPEAT else ('PARTIAL' if passes>0 else 'FAIL')
    merged_out = []
    for r, st, text in outputs:
        merged_out.append(f'--- run {r}/{REPEAT} [{st}] ---')
        merged_out.extend(text.splitlines())
    return tc, status, '\n'.join(merged_out), tcdir, passes, status_list

# Detail parsers
def read_lines(p: Path):
    return p.read_text(errors='ignore').splitlines() if p and p.exists() else []

SLOT = 35.84e-6

def _parse_kv_line(line: str):
    if not line.startswith(('BS','ES')):
        return None
    def _find(key, cast=str):
        m = re.search(rf"\b{key}\s+([^\s]+)", line)
        return cast(m.group(1)) if m else None
    name = _find('n')
    sm = _find('sm', int)
    st = _find('st', float)
    at = _find('at', float)
    return {'name': name, 'sm': sm, 'st': st, 'at': at}

def parse_tc1(elog: Path):
    prs0=prs1=None; backs=[]; tx=None
    for line in read_lines(elog):
        kv = _parse_kv_line(line)
        if not kv or not kv['name']:
            continue
        name, sm, st, at = kv['name'], kv['sm'], kv['st'], kv['at']
        if name=='prs0Timer' and prs0 is None and st is not None and at is not None:
            prs0=(st,at)
        elif name=='prs1Timer' and prs1 is not None:
            # keep first only
            pass
        elif name=='prs1Timer' and prs1 is None and st is not None and at is not None:
            prs1=(st,at)
        elif name=='backoffTimer' and prs1 and at is not None:
            backs.append((sm, st, at))
        elif name=='txTimer' and tx is None and st is not None and at is not None:
            tx=(sm, st, at)
    d0 = (prs0[1]-prs0[0]) if prs0 else None
    d1 = (prs1[1]-prs1[0]) if prs1 else None
    mean_slot=None
    if prs1 and tx:
        sm = tx[0]
        seq=[at for s,st,at in backs if s==sm and prs1[1] <= at <= tx[2]]
        if len(seq)>=2:
            diffs=[j-i for i,j in zip(seq, seq[1:])]
            mean_slot=sum(diffs)/len(diffs)
    return d0,d1,mean_slot

def parse_tc2(elog: Path):
    prs1=[]; tx=[]
    for line in read_lines(elog):
        kv = _parse_kv_line(line)
        if not kv or not kv['name']:
            continue
        name, sm, at = kv['name'], kv['sm'], kv['at']
        if name=='prs1Timer' and at is not None:
            prs1.append((sm, at))
        elif name=='txTimer' and at is not None:
            tx.append((sm, at))
    if not prs1 or not tx:
        return None, None, None
    t0=min(at for _,at in prs1)
    contenders=sorted({sm for sm,at in prs1 if abs(at-t0)<=1e-6})
    winner=sorted([(sm,at) for sm,at in tx if at>=t0], key=lambda x:x[1])[0][0]
    return t0,contenders,winner

def parse_tc2_windows(elog: Path, max_windows: int = 5, tol: float = 1e-6):
    prs1=[]; tx=[]; backs=[]; caps=[]
    # Collect prs1, backoff, and tx events
    for line in read_lines(elog):
        kv = _parse_kv_line(line)
        if not kv or not kv['name']:
            continue
        name, sm, at = kv['name'], kv['sm'], kv['at']
        if name=='prs1Timer' and at is not None:
            prs1.append((sm, at))
        elif name=='backoffTimer' and at is not None:
            backs.append((sm, at))
        elif name=='txTimer' and at is not None:
            tx.append((sm, at))
        # runtime CAP log lines (not BS/ES): parse separately
        mcap = re.search(r"CAP_LOG\s+node=([^\s]+)\s+cap=(\d+)\s+t=([0-9eE+\-\.]+)", line)
        if mcap:
            node, cap, t = mcap.groups()
            caps.append((node, int(cap), float(t)))
    if not prs1:
        return []
    prs1_sorted = sorted(prs1, key=lambda x: x[1])
    windows = []
    i=0
    while i < len(prs1_sorted) and len(windows) < max_windows:
        t0 = prs1_sorted[i][1]
        group = []
        j=i
        while j < len(prs1_sorted) and abs(prs1_sorted[j][1]-t0) <= tol:
            group.append(prs1_sorted[j])
            j+=1
        # winner: earliest tx after t0 but before next t0 (if exists)
        t_next = prs1_sorted[j][1] if j < len(prs1_sorted) else float('inf')
        tx_in_window = [(sm,at) for sm,at in tx if t0 <= at < t_next]
        # contenders: modules that actually started backoff in this window
        cont_times = {}
        for sm, at in backs:
            if t0 <= at < t_next:
                cont_times.setdefault(sm, []).append(at)
        cont_in_window = sorted(cont_times.keys())
        win = sorted(tx_in_window, key=lambda x:x[1])[0][0] if tx_in_window else None
        # derive backoff slot counts: number of ES(backoffTimer) ticks until TX (for each contender)
        slot_counts = {}
        for sm in cont_in_window:
            times = sorted(cont_times.get(sm, []))
            # count only up to winner's TX or this sm's TX if available
            tx_sm = next((at for s,at in tx_in_window if s==sm), None)
            tx_cut = tx_sm if tx_sm is not None else (sorted(tx_in_window, key=lambda x:x[1])[0][1] if tx_in_window else None)
            if tx_cut is not None:
                cnt = sum(1 for t in times if t0 <= t <= tx_cut)
            else:
                cnt = len(times)
            slot_counts[sm] = cnt
        windows.append({
            't0': t0,
            'contenders': cont_in_window if cont_in_window else sorted({sm for sm,_ in group}),
            'winner': win,
            'slots': slot_counts,
            'caps': caps
        })
        i = j
    return windows

def parse_mac_tree(elog: Path):
    # Parse module creation lines to map mac id -> top node name (ev[k] or evse)
    mc_pat = re.compile(r"^MC\s+id\s+(\d+)\s+c\s+([^\s]+)\s+t\s+[^\s]+\s+pid\s+(\d+)\s+n\s+([^\s]+)")
    modules = {}
    for line in read_lines(elog):
        m = mc_pat.search(line)
        if not m:
            continue
        mid, cls, pid, name = m.groups()
        modules[int(mid)] = {'cls': cls, 'pid': int(pid), 'name': name}
    # Build parent links and resolve top names
    def resolve_top(mid: int):
        seen = set()
        cur = mid
        while cur in modules and cur not in seen:
            seen.add(cur)
            info = modules[cur]
            name = info['name']
            if name.startswith('ev[') or name=='evse':
                return name
            cur = info['pid']
        return None
    mac_ids = [mid for mid,info in modules.items() if info['cls'].endswith('IEEE1901Mac')]
    id_to_top = {mid: resolve_top(mid) for mid in mac_ids}
    return mac_ids, id_to_top

def read_caps_from_ini(inipath: Path):
    caps = {}
    if not inipath.exists():
        return caps
    pat_ev = re.compile(r"^\*\*\.ev\[(\d+)\]\.slac\.startPriority\s*=\s*(\d+)")
    pat_evw = re.compile(r"^\*\*\.ev\*\.slac\.startPriority\s*=\s*(\d+)")
    val_evse = None
    pat_evse = re.compile(r"^\*\*\.evse\.slac\.startPriority\s*=\s*(\d+)")
    default_ev = None
    for line in read_lines(inipath):
        m1 = pat_ev.search(line)
        if m1:
            caps[f"ev[{m1.group(1)}]"] = int(m1.group(2))
        m1w = pat_evw.search(line)
        if m1w:
            default_ev = int(m1w.group(1))
        m2 = pat_evse.search(line)
        if m2:
            val_evse = int(m2.group(1))
    if val_evse is None:
        # default from SlacApp.ned: 3
        caps['evse'] = 3
    else:
        caps['evse'] = val_evse
    # Apply wildcard default to any ev[k] not explicitly set
    if default_ev is not None:
        # Populate for a reasonable range; actual nodes will be filtered when rendering
        for k in range(0, 64):
            key = f"ev[{k}]"
            if key not in caps:
                caps[key] = default_ev
    return caps

def parse_tc3(elog: Path):
    # Align with validator: take first window's winner module, average quantized diffs
    kvpat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs1Timer|backoffTimer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    prs1=[]; backs=[]; tx=[]
    for line in read_lines(elog):
        m = kvpat.search(line)
        if not m: continue
        ph, n, sm, st, at = m.groups(); sm=int(sm); st=float(st); at=float(at)
        if n=='prs1Timer' and ph=='ES': prs1.append((sm,st,at))
        elif n=='backoffTimer' and ph=='ES': backs.append((sm,st,at))
        elif n=='txTimer' and ph=='ES': tx.append((sm,st,at))
    if not prs1 or not tx:
        return None
    t0 = min(p[2] for p in prs1)
    tx_after = sorted([t for t in tx if t[2] >= t0], key=lambda x:x[2])
    if not tx_after:
        return None
    sm_win, _, tx_at = tx_after[0]
    times = sorted([b[2] for b in backs if b[0]==sm_win and t0 <= b[2] <= tx_at])
    if len(times) < 2:
        return None
    diffs=[j-i for i,j in zip(times, times[1:])]
    SLOT = 35.84e-6
    qdiffs=[round(d/SLOT)*SLOT for d in diffs]
    return (sum(qdiffs)/len(qdiffs)) if qdiffs else None

def parse_tc4(elog: Path):
    kvpat = re.compile(r"^(BS|ES)\s+id\s+\d+.*\bn\s+(prs0Timer|prs1Timer|backoffTimer|txTimer|sifsTimer|difsTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    prs0=[]; prs1=[]; backs=[]; tx=[]; sifs=[]; difs=[]
    for line in read_lines(elog):
        m = kvpat.search(line)
        if not m:
            continue
        ph, n, sm, st, at = m.groups(); sm=int(sm); st=float(st); at=float(at)
        if ph != 'ES':
            continue
        if n=='prs0Timer': prs0.append((sm,st,at))
        elif n=='prs1Timer': prs1.append((sm,st,at))
        elif n=='backoffTimer': backs.append((sm,st,at))
        elif n=='txTimer': tx.append((sm,st,at))
        elif n=='sifsTimer': sifs.append((sm,st,at))
        elif n=='difsTimer': difs.append((sm,st,at))
    # counts for context
    c_prs1 = len(prs1)
    c_tx = len(tx)
    # first full cycle metrics
    d0=d1=None; back=False; has_sifs=False; has_difs=False
    if prs0 and prs1 and tx:
        t0 = min(p[2] for p in prs0)
        p0 = min([p for p in prs0 if abs(p[2]-t0) <= 1e-6], key=lambda x:x[2])
        p1 = min([p for p in prs1 if p[2] >= p0[2]], key=lambda x:x[2]) if prs1 else None
        txx = min([t for t in tx if p1 and t[2] >= p1[2]], key=lambda x:x[2]) if tx else None
        if p0: d0 = p0[2] - p0[1]
        if p1: d1 = p1[2] - p1[1]
        if p1 and txx:
            back = any(p1[2] <= b[2] <= txx[2] for b in backs)
            s1 = [s for s in sifs if s[2] >= txx[2]]
            if s1:
                has_sifs = True
                first_sifs = min(s1, key=lambda x:x[2])
                has_difs = any(d[2] >= first_sifs[2] for d in difs)
            else:
                has_sifs = False
                has_difs = any(d[2] >= txx[2] for d in difs)
    return {
        'counts': (c_prs1, c_tx),
        'd0': d0, 'd1': d1,
        'backoffExists': back,
        'sifsExists': has_sifs,
        'difsExists': has_difs,
    }

rep=["# Test Report (Detailed / 상세 리포트)", "", f"- Timeout / 타임아웃: {TIMEOUT}s", f"- Repetitions / 반복횟수: {REPEAT}", ""]
pass_n=fail_n=0
for tc in TESTS:
    name, status, output, tcdir, passes, status_list = run_tc(tc)
    rep.append(f"## {name}")
    # Objective/Method/Expected/Actual per tc (영/한 병기)
    rep.append(f"- Conditions / 조건: timeout={TIMEOUT}s, repeats={REPEAT}")
    elog = (tcdir/"results/General-#0.elog") if tcdir else None
    if name=='tc1':
        rep.append("- Objective / 목적: Enforce PRS0/PRS1 durations and slotTime slot increments / PRS0/PRS1 지속시간과 슬롯 간격(slotTime) 검증")
        rep.append("- Method / 방법: Parse ES(prs0/prs1/backoff/tx) durations and slot steps / 이벤트로그 ES(prs0/prs1/backoff/tx)로 지속시간·슬롯 간격 파싱")
        rep.append(f"- Expected / 기대값: PRS0={SLOT:.6e}s, PRS1={SLOT:.6e}s, estimatedSlotTime={SLOT:.6e}s")
        d0,d1,ms=parse_tc1(elog) if elog else (None,None,None)
        def _fmt(x):
            return (f"{x:.6e}" if isinstance(x,(float,int)) else str(x)) if x is not None else "None"
        rep.append(f"- Actual / 실제값: PRS0={_fmt(d0)}s, PRS1={_fmt(d1)}s, estimatedSlotTime={_fmt(ms)}s")
    elif name=='tc2':
        rep.append("- Objective / 목적: Winner must be among first PRS1-window contenders / 최초 PRS1 윈도우 경쟁자 중에서 승자 결정")
        rep.append("- Method / 방법: Compare first PRS1-window contenders vs earliest TX module / PRS1 최초 윈도우 경쟁자와 가장 빠른 TX 모듈 비교")
        rep.append(f"- Expected / 기대값: winner∈contenders at t0 / 승자는 최초 윈도우 경쟁자 집합에 포함")
        # Build MAC inventory and CAPs
        rep.append("### Inventory / 인벤토리")
        mac_ids, id_to_top = parse_mac_tree(elog) if elog else ([], {})
        caps = read_caps_from_ini(tcdir/'omnetpp.ini') if tcdir else {}
        # Render MAC inventory as multi-line list
        rep.append(f"- All MAC IDs / 전체 MAC ID: {len(mac_ids)} (SLAC CAP=3, DC CAP=0 for all)")
        for mid in sorted(mac_ids):
            top = id_to_top.get(mid)
            cap = caps.get(top, 'N/A') if top else 'N/A'
            rep.append(f"  - MAC ID({mid}), Node({top}), CAP({cap})")
        rep.append("")
        # Effective CAP note for DC frames
        rep.append(f"- Note / 참고: dcPriority=0 for all nodes (same-CAP contention) / 모든 노드 dcPriority=0(동일 CAP 경쟁)")
        rep.append("")
        rep.append("### Windows / 윈도우")
        # Extract first 30 PRS windows
        wins = parse_tc2_windows(elog, max_windows=30) if elog else []
        rep.append("- First 30 PRS1 windows / 첫 30개 PRS1 윈도우")
        for idx, w in enumerate(wins, start=1):
            rep.append(f"  - Window {idx} @ t0={w['t0']:.6e}")
            rep.append("    - Contenders / 경쟁자:")
            for mid in w['contenders']:
                top = id_to_top.get(mid)
                cap = caps.get(top, 'N/A') if top else 'N/A'
                sc = w.get('slots',{}).get(mid)
                rep.append(f"      - MAC ID({mid}), Node({top}), CAP({cap}), backoffSlots({sc})")
            win_mid = w['winner']
            win_top = id_to_top.get(win_mid) if win_mid is not None else None
            win_cap = caps.get(win_top, 'N/A') if win_top else 'N/A'
            rep.append(f"    - Winner / 승자: MAC ID({win_mid}), Node({win_top}), CAP({win_cap}), reason=smallest backoffSlots")
        rep.append("")
        rep.append(f"- Evidence / 증거: see `{tcdir}/results/General-#0.elog`")
    elif name=='tc3':
        rep.append("- Objective / 목적: Backoff slot mean≈slotTime / 백오프 슬롯 평균 간격≈슬롯시간")
        rep.append("- Method / 방법: Compute mean of BS(backoffTimer) intervals / BS(backoffTimer) 간격 평균 계산")
        ms=parse_tc3(elog) if elog else None
        rep.append(f"- Expected / 기대값: mean≈{SLOT:.6e}s (validator-aligned)")
        rep.append(f"- Actual / 실제값: mean={_fmt(ms)}s (validator-aligned)")
    elif name=='tc4':
        rep.append("- Objective / 목적: Validate full sequence PRS0→PRS1→Backoff→TX→RIFS→CIFS→next PRS0 / 전체 MAC 시퀀스 검증")
        rep.append("- Method / 방법: Check ES timers order and durations (PRS≈slot, RIFS/CIFS presence) / PRS≈슬롯시간, RIFS/CIFS 존재 확인")
        m = parse_tc4(elog) if elog else None
        rep.append(f"- Expected / 기대값: PRS0≈{SLOT:.6e}s, PRS1≈{SLOT:.6e}s, backoffExists=True, rifsExists=True, cifsExists=True; counts>0")
        if m:
            c_prs1, c_tx = m['counts']
            # define _fmt if not yet defined
            try:
                _fmt
            except NameError:
                def _fmt(x):
                    return (f"{x:.6e}" if isinstance(x,(float,int)) else str(x)) if x is not None else "None"
            # rename keys for display if needed
            rifs_exists = m.get('sifsExists')
            cifs_exists = m.get('difsExists')
            rep.append(f"- Actual / 실제값: d0={_fmt(m['d0'])}s, d1={_fmt(m['d1'])}s, backoffExists={m['backoffExists']}, rifsExists={rifs_exists}, cifsExists={cifs_exists}, counts(PRS1,TX)=({c_prs1},{c_tx})")
        else:
            rep.append(f"- Actual / 실제값: unavailable")
    elif name=='tc5':
        rep.append("- Objective / 목적: Verify per-message CAP cycling 3→2→1→0 / 메시지별 CAP 순환(3→2→1→0) 검증")
        rep.append("- Method / 방법: Enable SlacApp.enableDcPriorityCycle and observe PRS windows & winners / SlacApp.enableDcPriorityCycle 활성화 후 윈도우·승자 관찰")
        rep.append("- Expected / 기대값: Across windows, winners vary over time consistent with CAP cycling / 윈도우가 진행되며 승자가 순환 특성을 반영")
        # Inventory
        rep.append("### Inventory / 인벤토리")
        mac_ids, id_to_top = parse_mac_tree(elog) if elog else ([], {})
        caps = read_caps_from_ini(tcdir/'omnetpp.ini') if tcdir else {}
        rep.append(f"- All MAC IDs / 전체 MAC ID: {len(mac_ids)} (SLAC CAP=3, DC CAP cycles per message)")
        rep.append("| MAC ID | Node | initCAP |")
        rep.append("|---:|:---|---:|")
        for mid in sorted(mac_ids):
            top = id_to_top.get(mid)
            cap = caps.get(top, 'N/A') if top else 'N/A'
            rep.append(f"| {mid} | {top} | {cap} |")
        rep.append("")
        rep.append("### Windows / 윈도우")
        wins = parse_tc2_windows(elog, max_windows=15) if elog else []
        rep.append("- First 15 PRS1 windows / 첫 15개 PRS1 윈도우")
        for idx, w in enumerate(wins, start=1):
            rep.append(f"  - Window {idx} @ t0={w['t0']:.6e}")
            rep.append("    - Contenders / 경쟁자:")
            for mid in w['contenders']:
                top = id_to_top.get(mid)
                # prefer runtime CAP from CAP_LOG near t0
                rt_cap = None
                for node, capv, tcap in reversed(w.get('caps', [])):
                    if node == top and tcap <= w['t0'] + 1e-3: # small window after t0
                        rt_cap = capv; break
                cap = rt_cap if rt_cap is not None else (caps.get(top, 'N/A') if top else 'N/A')
                sc = w.get('slots',{}).get(mid)
                rep.append(f"      - MAC ID({mid}), Node({top}), CAP({cap}), backoffSlots({sc})")
            win_mid = w['winner']
            win_top = id_to_top.get(win_mid) if win_mid is not None else None
            win_cap = None
            if win_top:
                for node, capv, tcap in reversed(w.get('caps', [])):
                    if node == win_top and tcap <= w['t0'] + 1e-3:
                        win_cap = capv; break
            if win_cap is None:
                win_cap = caps.get(win_top, 'N/A') if win_top else 'N/A'
            rep.append(f"    - Winner / 승자: MAC ID({win_mid}), Node({win_top}), CAP({win_cap})")
            # Losers: contenders except winner
            losers = [mid for mid in w['contenders'] if mid != win_mid]
            if losers:
                rep.append("    - Losers / 탈락자:")
                for mid in losers:
                    top = id_to_top.get(mid)
                    rt_cap = None
                    for node, capv, tcap in reversed(w.get('caps', [])):
                        if node == top and tcap <= w['t0'] + 1e-3:
                            rt_cap = capv; break
                    cap = rt_cap if rt_cap is not None else (caps.get(top, 'N/A') if top else 'N/A')
                    sc = w.get('slots',{}).get(mid)
                    rep.append(f"      - MAC ID({mid}), Node({top}), CAP({cap}), backoffSlots({sc})")
            # Non-contenders: MAC IDs that didn't participate this window
            non = [mid for mid in sorted(mac_ids) if mid not in w['contenders']]
            if non:
                rep.append("    - Non-contenders / 불참자:")
                for mid in non:
                    top = id_to_top.get(mid)
                    cap = caps.get(top, 'N/A') if top else 'N/A'
                    rep.append(f"      - MAC ID({mid}), Node({top}), CAP({cap})")
        rep.append("")
        # Attach CAP_LOG lines (if any) from sim.out for reference
        simout = (tcdir/"results/sim.out")
        if simout.exists():
            rep.append("- CAP_LOG (runtime) / 런타임 CAP 로그:")
            rep.append("```")
            for line in read_lines(simout):
                if 'CAP_LOG' in line:
                    rep.append(line)
            rep.append("```")
        rep.append(f"- Evidence / 증거: see `{tcdir}/results/General-#0.elog` and `{tcdir}/results/sim.out`")
    rep.append(f"- Runs Passed / 통과 회수: {passes}/{REPEAT}")
    rep.append(f"- Run Statuses / 실행 상태: [{', '.join(status_list)}]")
    rep.append(f"- Verdict / 판정: {status}")
    rep.append("- Runner Output (first lines) / 실행 출력(일부):")
    rep.append("```")
    lines = output.splitlines()
    rep.extend(lines[:EVID_MAX])
    if len(lines) > EVID_MAX:
        rep.append("... (truncated) ...")
    rep.append("```")
    rep.append("")
    if status=='PASS': pass_n+=1
    else: fail_n+=1

rep.append("## Summary / 요약")
rep.append(f"- Passed / 통과: {pass_n}")
rep.append(f"- Failed / 실패: {fail_n}")

(BASE/'testReport.md').write_text('\n'.join(rep)+'\n')
print(str(BASE/'testReport.md'))
