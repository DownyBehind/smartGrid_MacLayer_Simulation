import os, subprocess, shlex, re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV = {}
with open(BASE/'test_slac.env') as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k,v=line.split('=',1)
            ENV[k]=v

def _strip_quotes(s: str) -> str:
    return s.strip().strip('"').strip("'")

TESTS = [_strip_quotes(t) for t in ENV.get('SLAC_TEST_CASES','').split() if t]
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

# Minimal parsers (observer)
def read_lines(p: Path):
    return p.read_text(errors='ignore').splitlines() if p and p.exists() else []

def parse_seq(elog: Path, names):
    order=[]
    for line in read_lines(elog):
        m = re.search(r"^ES\\s+id\\s+\\d+.*\\bn\\s+([A-Z_]+)\\b.*\\bat\\s+([0-9eE+\\-\\.]+)", line)
        if not m: continue
        n, at = m.groups(); at=float(at)
        if n in names: order.append((at, n))
    return [n for _,n in sorted(order)]

def parse_slac_log(simout: Path):
    # Returns (ordered_stages_ev_only, counts)
    stages=[]
    counts={}
    if not simout.exists():
        return stages, counts
    pat = re.compile(r"^\[INFO\]\s+SLAC_LOG\s+stage=([A-Z_]+)\s+node=([^\s]+).*")
    for line in read_lines(simout):
        m = pat.search(line)
        if not m: continue
        stage, node = m.groups()
        if node.startswith('ev['):
            stages.append(stage)
            counts[stage] = counts.get(stage, 0) + 1
    return stages, counts

def read_slac_params(inipath: Path):
    params = { 'numMsound': None, 'numStartAtten': 3 }
    if not inipath.exists():
        return params
    for line in read_lines(inipath):
        m = re.search(r"^\*\*\.slac\.numMsound\s*=\s*(\d+)", line)
        if m:
            params['numMsound'] = int(m.group(1))
        m2 = re.search(r"^\*\*\.slac\.numStartAtten\s*=\s*(\d+)", line)
        if m2:
            params['numStartAtten'] = int(m2.group(1))
    return params

def parse_slac_timeout(simout: Path):
    has_start=False; has_done=False; start_count=0; done_count=0
    if not simout or not simout.exists():
        return has_start, has_done, start_count, done_count
    for line in read_lines(simout):
        if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=START_ATTEN' in line:
            has_start=True; start_count+=1
        if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=SLAC_DONE' in line:
            has_done=True; done_count+=1
    return has_start, has_done, start_count, done_count

rep=["# SLAC Test Report / SLAC 상세 리포트", f"- Timeout / 타임아웃: {TIMEOUT}s", f"- Repetitions / 반복횟수: {REPEAT}", ""]
pass_n=fail_n=0
for tc in TESTS:
    name, status, output, tcdir, passes, status_list = run_tc(tc)
    rep.append(f"## {name}")
    rep.append(f"- Conditions / 조건: timeout={TIMEOUT}s, repeats={REPEAT}")
    elog = (tcdir/"results/General-#0.elog") if tcdir else None
    if name=='slac_tc1':
        rep.append("- Objective / 목적: Nominal SLAC sequence order / SLAC 순서 검증")
        rep.append("- Method / 방법: Observe ES logs of SLAC messages / SLAC 메시지 ES 로그 관찰")
        # Expected based on ini (numMsound, numStartAtten) and NED defaults
        params = read_slac_params(tcdir/'omnetpp.ini') if tcdir else {'numMsound': None, 'numStartAtten': 3}
        num_ms = params.get('numMsound') if params.get('numMsound') is not None else 5
        num_sa = params.get('numStartAtten', 3)
        expected_desc = f"START_ATTEN×{num_sa+1} → M_SOUND×{num_ms} → ATTEN_CHAR → VALIDATE → SLAC_DONE"
        rep.append(f"- Expected / 기대값: {expected_desc}")
        # Actual from sim.out SLAC_LOG
        simout = tcdir/'results/sim.out' if tcdir else None
        stages, counts = parse_slac_log(simout) if simout else ([], {})
        actual_seq = []
        if stages:
            # collapse consecutive duplicates for readability
            for s in stages:
                if not actual_seq or actual_seq[-1] != s:
                    actual_seq.append(s)
        rep.append(f"- Actual / 실제 순서: {' → '.join(actual_seq) if actual_seq else 'None'}")
        if counts:
            rep.append(f"- Actual counts / 실제 횟수: START_ATTEN={counts.get('START_ATTEN',0)}, M_SOUND={counts.get('M_SOUND',0)}, ATTEN_CHAR={counts.get('ATTEN_CHAR',0)}, VALIDATE={counts.get('VALIDATE',0)}, SLAC_DONE={counts.get('SLAC_DONE',0)}")
    elif name=='slac_tc2':
        rep.append("- Objective / 목적: No-EVSE timeout handling / EVSE 무응답 타임아웃")
        rep.append("- Method / 방법: Observe timeout and retry logs / 타임아웃 및 재시도 로그 관찰")
        rep.append("- Note / 비고: simulateNoEvse=true로 EV 노드의 SLAC_DONE 기록만 억제하여 '응답 부재' 상태를 관찰합니다 (EVSE는 실제로 응답할 수 있음). / With simulateNoEvse=true, we suppress only EV-side SLAC_DONE logging to emulate 'no response' while EVSE may still transmit.")
        # Expected/Actual based on SLAC_LOG
        rep.append("- Expected / 기대값: EV node has START_ATTEN, no SLAC_DONE within run / EV 노드 START_ATTEN 발생, SLAC_DONE 미발생")
        simout = tcdir/'results/sim.out' if tcdir else None
        has_start, has_done, sc, dc = parse_slac_timeout(simout)
        rep.append(f"- Actual / 실제값: hasStart={has_start}, hasDone={has_done}, startCount={sc}, doneCount={dc}")
    elif name=='slac_tc3':
        rep.append("- Objective / 목적: High BER timeout (no SLAC completion) / 고BER 타임아웃(완료 미수신)")
        rep.append("- Method / 방법: Enable PHY BER/noise and observe EV SLAC_DONE absence / PHY BER/노이즈로 EV SLAC_DONE 부재 관찰")
        rep.append("- Expected / 기대값: EV node has START_ATTEN, no SLAC_DONE within run / EV 노드 START_ATTEN 발생, SLAC_DONE 미발생")
        simout = tcdir/'results/sim.out' if tcdir else None
        has_start, has_done, sc, dc = parse_slac_timeout(simout)
        rep.append(f"- Actual / 실제값: hasStart={has_start}, hasDone={has_done}, startCount={sc}, doneCount={dc}")
    elif name=='slac_tc4':
        rep.append("- Objective / 목적: Partial M-SOUND loss recovery / 일부 손실 복구")
    elif name=='slac_tc5':
        rep.append("- Objective / 목적: VALIDATE timeout / VALIDATE 타임아웃")
    elif name=='slac_tc6':
        rep.append("- Objective / 목적: StartAtten attempts / 재시도 횟수 검증")
    elif name=='slac_tc7':
        rep.append("- Objective / 목적: CAP usage during SLAC / SLAC CAP 사용 검증")
    elif name=='slac_tc8':
        rep.append("- Objective / 목적: End-to-end timing budget / 전체 지연 예산")
    elif name=='slac_tc9':
        rep.append("- Objective / 목적: Abort-and-retry hygiene / 중단-재시작 위생")
    elif name=='slac_tc10':
        rep.append("- Objective / 목적: Reproducibility with fixed RNG / 고정 시드 재현성")
    rep.append(f"- Runs Passed / 통과 회수: {passes}/{REPEAT}")
    rep.append(f"- Run Statuses / 실행 상태: [{', '.join(status_list)}]")
    rep.append(f"- Runner Output / 실행 출력:")
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

(BASE/'testReport_SLAC.md').write_text('\n'.join(rep)+'\n')
print(str(BASE/'testReport_SLAC.md'))

