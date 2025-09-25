import re, sys, pathlib

TC_DIR = pathlib.Path(__file__).resolve().parent
simout = TC_DIR/"results"/"sim.out"
lines = simout.read_text(errors='ignore').splitlines() if simout.exists() else []

# Accept one of:
#  - explicit CAx parameters log
#  - backoff counters initialization log
#  - MAC finish summary containing Backoffs: N (evidence that backoff ran)
has_cax = any(('CA3/CA2 parameters - BPC=' in ln) or ('CA1/CA0 parameters - BPC=' in ln) for ln in lines)
has_init = any('Initialized HomePlug 1.0 backoff counters:' in ln for ln in lines)
has_summary_backoffs = any(re.search(r"Backoffs:\s+\d+", ln) for ln in lines)

if not (has_cax or has_init or has_summary_backoffs):
    print('No Table I/backoff evidence detected: FAIL')
    sys.exit(1)
print('Table I/backoff evidence detected: PASS')
sys.exit(0)
