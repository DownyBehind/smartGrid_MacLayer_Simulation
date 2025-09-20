import re, sys
from pathlib import Path

def has_timeout_simout(simout: Path):
    # We consider timeout if SLAC_DONE never appears, but START_ATTEN appears
    if not simout.exists():
        return False
    has_start=False; has_done=False
    with simout.open(errors='ignore') as f:
        for line in f:
            # Only consider EV node lines
            if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=START_ATTEN' in line:
                has_start=True
            if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=SLAC_DONE' in line:
                has_done=True
    return has_start and not has_done

def has_timeout(elog: Path):
    # Look for repeated START_ATTEN without reaching SLAC_DONE within time
    pat = re.compile(r"^ES\s+id\s+\d+.*\bn\s+(START_ATTEN|SLAC_DONE)\b.*\bat\s+([0-9eE+\-\.]+)")
    ev=[]
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m: continue
            ev.append(m.group(1))
    # condition: at least one START_ATTEN exists and no SLAC_DONE
    return ('START_ATTEN' in ev) and ('SLAC_DONE' not in ev)

def main():
    simout = Path('results/sim.out')
    if has_timeout_simout(simout):
        print('OK')
        return
    elog = Path('results/General-#0.elog')
    if not elog.exists() or not has_timeout(elog):
        print('NG: expected timeout condition not observed')
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()

