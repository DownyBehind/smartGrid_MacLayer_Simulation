import re, sys
from pathlib import Path

TOL = 1e-6  # 1us

def parse_prs1_end_from_cmdenv(cmdenv: Path):
    # Flexible match for PRS1_END lines regardless of prefix formatting
    end_pat = re.compile(r"PRS1_END.*?t=([0-9eE+\-\.]+)")
    with cmdenv.open(errors='ignore') as f:
        for line in f:
            m = end_pat.search(line)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    continue
    return None

def read_backoff_tx(elog: Path):
    # Extract ES lines for backoffTimer and txTimer: module id (sm), st, at
    pat = re.compile(r"^(ES)\s+id\s+\d+.*\bn\s+(backoffTimer|txTimer)\b.*\bsm\s+(\d+)\b.*\bst\s+([0-9eE+\-\.]+)\s+am\s+\d+\s+at\s+([0-9eE+\-\.]+)")
    backs = []
    txs = []
    with elog.open(errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if not m:
                continue
            _, name, sm, st, at = m.groups()
            sm = int(sm); st = float(st); at = float(at)
            if name == 'backoffTimer':
                backs.append((sm, st, at))
            else:
                txs.append((sm, st, at))
    return backs, txs

def main():
    elog = Path('results/General-#0.elog')
    cmdenv = Path('results/cmdenv.log')
    if not elog.exists() or not cmdenv.exists():
        print('NG: missing logs')
        sys.exit(1)

    prs1_end = parse_prs1_end_from_cmdenv(cmdenv)
    if prs1_end is None:
        print('NG: missing PRS1_END')
        sys.exit(1)

    backs, txs = read_backoff_tx(elog)
    if not backs or not txs:
        print('NG: missing backoff/tx events')
        sys.exit(1)

    # contenders: modules whose first backoffTimer ES starts exactly at PRS1_END
    contenders = {sm for (sm, st, at) in backs if abs(st - prs1_end) <= TOL}
    if not contenders:
        print('NG: no contenders at PRS1_END')
        sys.exit(1)

    # first tx after PRS1_END must belong to contenders
    tx_after = sorted([(sm, at) for (sm, _, at) in txs if at >= prs1_end], key=lambda x: x[1])
    if not tx_after:
        print('NG: no tx after PRS1_END')
        sys.exit(1)
    if tx_after[0][0] not in contenders:
        print('NG: winner not among PRS1 contenders')
        sys.exit(1)

    print('OK')

if __name__=='__main__':
    main()
