import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
cmdenv = TC_DIR/"results"/"cmdenv.log"
text = cmdenv.read_text(errors='ignore') if cmdenv.exists() else ""

# Accept one of:
#  - explicit CAx parameters log
#  - backoff counters initialization log
#  - MAC finish summary containing Backoffs: N (evidence that backoff ran)
has_cax = ('CA3/CA2 parameters - BPC=' in text) or ('CA1/CA0 parameters - BPC=' in text)
has_init = ('Initialized HomePlug 1.0 backoff counters:' in text)
has_summary_backoffs = bool(re.search(r"Backoffs:\s+\d+", text))

if not (has_cax or has_init or has_summary_backoffs):
    print('No Table I/backoff evidence detected: FAIL')
    sys.exit(1)
print('Table I/backoff evidence detected: PASS')
sys.exit(0)
