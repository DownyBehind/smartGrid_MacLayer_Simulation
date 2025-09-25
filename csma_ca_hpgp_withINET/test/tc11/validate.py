import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
elog = TC_DIR/"results"/"General-#0.elog"
simout = TC_DIR/"results"/"sim.out"
lines_e = elog.read_text(errors='ignore').splitlines() if elog.exists() else []
lines_s = simout.read_text(errors='ignore').splitlines() if simout.exists() else []

inc_bpc = any('increasing BPC' in ln for ln in lines_e)
tx_fail_scalar = any('tx_fail_collisions' in ln for ln in lines_s)
if not inc_bpc and not tx_fail_scalar:
    print('No collision→MAC retry evidence (BPC++/tx_fail_collisions): FAIL')
    sys.exit(1)
print('Collision→MAC retry evidence present: PASS')
sys.exit(0)
