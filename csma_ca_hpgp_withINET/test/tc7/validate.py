import pathlib, sys

TC_DIR = pathlib.Path(__file__).resolve().parent
cmdenv = TC_DIR/"results"/"cmdenv.log"
text = cmdenv.read_text(errors='ignore') if cmdenv.exists() else ""

if '[BUSY_SLOT]' not in text:
    print('No [BUSY_SLOT] evidence in cmdenv.log: FAIL')
    sys.exit(1)
print('[BUSY_SLOT] evidence present: PASS')
sys.exit(0)
