#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) > 1:
    log_path = Path(sys.argv[1])
else:
    log_path = Path(__file__).resolve().parent / "results" / "sim.out"
if not log_path.exists():
    print('sim.out not found: FAIL')
    sys.exit(1)

text = log_path.read_text(errors='ignore')

if "[PRS_DEFER]" not in text:
    print('Missing [PRS_DEFER] defer log: FAIL')
    sys.exit(2)
if 'Frames dropped' in text:
    print('Unexpected frame drop detected: FAIL')
    sys.exit(3)
print('PRS defer without drops confirmed: PASS')
sys.exit(0)

