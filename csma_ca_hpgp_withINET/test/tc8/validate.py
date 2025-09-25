import pathlib, sys

TC_DIR = pathlib.Path(__file__).resolve().parent
simout = TC_DIR/"results"/"sim.out"
elog = TC_DIR/"results"/"General-#0.elog"
lines_s = simout.read_text(errors='ignore').splitlines() if simout.exists() else []
lines_e = elog.read_text(errors='ignore').splitlines() if elog.exists() else []

has_collision = any('[PHY_COLLISION]' in ln for ln in lines_s)
has_retry = any('CTRL_TX_FAIL' in ln or '[BUSY_SLOT] escalate' in ln for ln in lines_s) or any('CTRL_TX_FAIL' in ln for ln in lines_e)

if not has_collision:
    print('No [PHY_COLLISION] evidence: FAIL')
    sys.exit(1)
if not has_retry:
    print('No retry evidence after collision: FAIL')
    sys.exit(1)
print('Collision and retry evidence present: PASS')
sys.exit(0)
