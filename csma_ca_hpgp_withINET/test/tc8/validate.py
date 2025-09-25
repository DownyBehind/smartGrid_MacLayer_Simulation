import pathlib, sys

TC_DIR = pathlib.Path(__file__).resolve().parent
cmdenv = TC_DIR/"results"/"cmdenv.log"
elog = TC_DIR/"results"/"General-#0.elog"
text = cmdenv.read_text(errors='ignore') if cmdenv.exists() else ""
elog_text = elog.read_text(errors='ignore') if elog.exists() else ""

# Evidence patterns
collision_keys = [
    '[PHY_COLLISION]',
    '[COLLISION] Simultaneous TX detected',
    'Dropping frame due to explicit collision model'
]
retry_keys = [
    'CTRL_TX_FAIL',
    '[BUSY_SLOT] escalate'
]
busy_keys = [
    'MAC busy; enqueue',
    'PHY busy; enqueue'
]

low = text.lower()
has_collision = any(k.lower() in low for k in collision_keys)
has_retry = any(k in text or k in elog_text for k in retry_keys)

# Strict: require collision evidence AND retry evidence
if not has_collision:
    print('No collision evidence ([PHY_COLLISION]/COLLISION/drop): FAIL')
    sys.exit(1)
if not has_retry:
    print('No retry evidence (CTRL_TX_FAIL/[BUSY_SLOT] escalate): FAIL')
    sys.exit(1)

print('Collision with retry evidence: PASS')
sys.exit(0)
