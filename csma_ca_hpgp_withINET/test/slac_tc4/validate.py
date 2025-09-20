import re, sys
from pathlib import Path

def read_lines(p: Path):
    return p.read_text(errors='ignore').splitlines() if p and p.exists() else []

def parse_slac_logs(sim_out_path: Path):
    logs = []
    pat = re.compile(r"^\[INFO\]\s+SLAC_LOG\s+stage=([A-Z_]+)\s+node=([^\s]+).*?(?:idx=(\d+))?.*?t=([0-9eE+\-\.]+).*")
    for line in read_lines(sim_out_path):
        m = pat.search(line)
        if m:
            stage, node, idx, t = m.groups()
            logs.append({'stage': stage, 'node': node, 'idx': int(idx) if idx else None, 't': float(t)})
    return logs

def main():
    sim_out = Path('results/sim.out')
    if not sim_out.exists():
        print('NG: sim.out not found')
        sys.exit(1)
    logs = parse_slac_logs(sim_out)
    ev_logs = [l for l in logs if l['node'].startswith('ev[')]
    start_count = sum(1 for l in ev_logs if l['stage']=='START_ATTEN')
    msound_obs = [l for l in ev_logs if l['stage']=='M_SOUND']
    done_count = sum(1 for l in ev_logs if l['stage']=='SLAC_DONE')
    if start_count != 4:
        print(f'NG: START_ATTEN count {start_count} != 4')
        sys.exit(1)
    if len(msound_obs) == 0:
        print('NG: no M_SOUND observed')
        sys.exit(1)
    if done_count < 1:
        print('NG: SLAC_DONE not observed')
        sys.exit(1)
    print('OK')

if __name__ == '__main__':
    main()
