import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
elog = TC_DIR/"results"/"General-#0.elog"
cmdenv = TC_DIR/"results"/"cmdenv.log"
elog_text = elog.read_text(errors='ignore') if elog.exists() else ""
cmd_text = cmdenv.read_text(errors='ignore') if cmdenv.exists() else ""

# Accept either explicit BPC++ evidence in eventlog or runtime signs in cmdenv
has_bpc_inc = ('increasing BPC' in elog_text)
has_tx_fail = ('CTRL_TX_FAIL' in cmd_text) or ('Dropping frame due to explicit collision model' in cmd_text)
has_busy = ('PHY busy; enqueue' in cmd_text) or ('MAC busy; enqueue' in cmd_text)

if not (has_bpc_inc or has_tx_fail):
    print('No collision→MAC retry evidence (BPC++/CTRL_TX_FAIL): FAIL')
    sys.exit(1)
print('Collision→MAC retry evidence present: PASS')
sys.exit(0)
