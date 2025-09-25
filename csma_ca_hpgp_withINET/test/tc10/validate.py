import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
simout = TC_DIR/"results"/"sim.out"
lines = simout.read_text(errors='ignore').splitlines() if simout.exists() else []

busy = any('[BUSY_SLOT]' in ln for ln in lines)
dc0busy = any('[BUSY_SLOT] escalate' in ln or 'Deferral Counter reached 0 with busy medium - increasing BPC' in ln for ln in lines)

if not busy:
    print('No [BUSY_SLOT] entries: FAIL')
    sys.exit(1)
if not dc0busy:
    print('No DC==0 busy escalation evidence: FAIL')
    sys.exit(1)
print('Busy-slot and escalation evidence present: PASS')
sys.exit(0)
