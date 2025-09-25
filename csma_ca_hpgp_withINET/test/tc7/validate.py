import pathlib, sys

TC_DIR = pathlib.Path(__file__).resolve().parent
simout = TC_DIR/"results"/"sim.out"
lines = simout.read_text(errors='ignore').splitlines() if simout.exists() else []

if not any('[BUSY_SLOT]' in ln for ln in lines):
    print('No [BUSY_SLOT] evidence: FAIL')
    sys.exit(1)
print('Busy-slot evidence present: PASS')
sys.exit(0)
