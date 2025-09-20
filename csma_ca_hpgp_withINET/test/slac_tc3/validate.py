import re, sys
from pathlib import Path

def match_cnf_seen(elog: Path):
    if not elog.exists():
        return False
    txt = elog.read_text(errors='ignore')
    return 'SLAC_MATCH_CNF' in txt

def parse_timeout(simout: Path):
    has_start=False; has_done=False
    if not simout.exists():
        return False, False
    for line in simout.read_text(errors='ignore').splitlines():
        if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=START_ATTEN' in line:
            has_start=True
        if 'SLAC_LOG' in line and 'node=ev[' in line and 'stage=SLAC_DONE' in line:
            has_done=True
    return has_start, has_done

def main():
    simout = Path('results/sim.out')
    has_start, has_done = parse_timeout(simout)
    # optional info (not affecting verdict): whether SLAC_MATCH_CNF appeared in .elog
    elog = Path('results/General-#0.elog')
    _seen = match_cnf_seen(elog)
    if not has_start:
        print('NG: no START_ATTEN observed')
        sys.exit(1)
    if has_done:
        print('NG: SLAC_DONE observed despite high BER/noise (matchCnfSeen=%s)' % _seen)
        sys.exit(1)
    print('OK')

if __name__=='__main__':
    main()

