import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
cmdenv = TC_DIR/"results"/"cmdenv.log"
text = cmdenv.read_text(errors='ignore') if cmdenv.exists() else ""

keywords_busy = [
    '[BUSY_SLOT]',
    'MAC busy; enqueue',
    'PHY busy; enqueue'
]
keywords_escalate = [
    '[BUSY_SLOT] escalate',
    'Deferral Counter reached 0 with busy medium - increasing BPC'
]

low = text.lower()
busy = any(k.lower() in low for k in keywords_busy)
dc0busy = any(k.lower() in low for k in keywords_escalate)

if not busy:
    print('No busy evidence in cmdenv.log: FAIL')
    sys.exit(1)
if not dc0busy:
    print('No DC==0 busy escalation evidence: FAIL')
    sys.exit(1)
print('Busy-slot escalation evidence present: PASS')
sys.exit(0)
