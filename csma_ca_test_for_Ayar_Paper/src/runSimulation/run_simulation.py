#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch runner for two experiment modes without touching C++ or INI:

  1) scale  : effective sendInterval = base_ms * (N/5)
              (original behavior; keeps cfg.baseInterval constant)

  2) fixed  : effective sendInterval = fixed_ms (independent of N)
              IMPLEMENTATION TRICK:
              We DO NOT modify SendIntervalConfigurator.
              Instead, before each run we pre-compensate the N-scaling by
              writing cfg.baseInterval := fixed_ms * 5 / N into the NED file.
              Then SendIntervalConfigurator computes base*(N/5) = fixed_ms.
"""

import argparse
import subprocess
import shutil
import pathlib
import datetime
import os
import re
import sys
from typing import List

# ─────── 경로 설정 ───────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT    = SCRIPT_DIR.parent.parent   # …/csma_ca_test_for_Ayar_Paper

INET_DIR   = pathlib.Path(os.environ.get(
    "INET_DIR",
    "/home/kimdawoon/study/workspace/research/inet_plc/inet"
))
INET_SRC   = INET_DIR / "src"

TIME_SLOT  = PROJECT.parent / "TimeSlot"

NED_FILE   = PROJECT / "ned" / "csma_ca_test_for_Ayar_Paper" / "FakeWireCsmaCaNetwork.ned"
BACKUP_NED = NED_FILE.with_suffix(".ned.bak")

INI_FILE   = PROJECT / "ini" / "omnetpp.ini"
RESULT_DIR = PROJECT / "ini" / "results"
CONFIG     = "Paper_Baseline"
OMNET_BIN  = "opp_run"

DEFAULT_RUNS = list(range(5, 101, 5))

def check_prerequisites():
    """필요한 파일과 경로들이 존재하는지 확인"""
    missing = []
    
    if not INET_DIR.exists():
        missing.append(f"INET directory: {INET_DIR}")
    
    if not INET_SRC.exists():
        missing.append(f"INET src directory: {INET_SRC}")
    
    if not TIME_SLOT.exists():
        missing.append(f"TimeSlot directory: {TIME_SLOT}")
    
    if not NED_FILE.exists():
        missing.append(f"NED file: {NED_FILE}")
    
    if not INI_FILE.exists():
        missing.append(f"INI file: {INI_FILE}")
    
    if missing:
        print("ERROR: Missing required files/directories:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease check your setup and try again.")
        sys.exit(1)

def ensure_backup():
    if not BACKUP_NED.exists():
        shutil.copy(NED_FILE, BACKUP_NED)
        print(f"[i] Backup created: {BACKUP_NED.name}")

def set_num_hosts(n: int):
    """FakeWireCsmaCaNetwork.ned 내 'int numHosts = default(...)' 값을 n으로 치환."""
    text = NED_FILE.read_text()
    # \g<1>, \g<2> 형태 사용: 뒤에 숫자가 붙어도 그룹 번호 오해 방지
    new_text, cnt = re.subn(
        r'(int\s+numHosts\s*=\s*default\()\s*\d+\s*(\)\s*;)',
        rf'\g<1>{n}\g<2>',
        text,
        flags=re.MULTILINE
    )
    if cnt == 0:
        raise RuntimeError("Could not find 'int numHosts = default(...)' in NED.")
    NED_FILE.write_text(new_text)
    print(f"  → NED numHosts default({n}) set.")

def set_cfg_base_interval_seconds(sec: float):
    """
    cfg.baseInterval 값을 지정 초단위로 고정 기록.
    - NED 내 cfg 블록( SendIntervalConfigurator )의 baseInterval 할당을 찾아 교체
    - default(...) 형태든 그냥 값 할당이든 매칭
    """
    text = NED_FILE.read_text()

    # 주의: 치환 문자열에서 \1 처럼 쓰면 바로 뒤 숫자와 붙어 \10, \20으로 오해될 수 있으므로
    # 반드시 \g<1> 형태를 사용한다.
    pat = re.compile(
        r'(baseInterval\s*=\s*)(default\()?\s*[-+0-9.eE]+\s*[a-zA-Z]*\s*(\))?\s*;',
        re.MULTILINE
    )

    secs_str = f"{sec:.9f}s"
    # 백레퍼런스는 모두 \g<1> 형태로!
    repl = rf'\g<1>\g<2>{secs_str}\g<3>;'

    new_text, cnt = pat.subn(repl, text, count=1)
    if cnt == 0:
        raise RuntimeError("Could not find 'baseInterval = ...' assignment in cfg block.")
    NED_FILE.write_text(new_text)
    print(f"  → cfg.baseInterval = {secs_str}")

def run_one(n: int, use_timeslot: bool = True):
    """단일 시뮬레이션 실행"""
    print(f"▶ N={n} simulation start")
    
    # NED 경로 구성
    if use_timeslot:
        ned_path = f"{INET_SRC};{PROJECT/'ned'};{TIME_SLOT}"
    else:
        ned_path = f"{INET_SRC};{PROJECT/'ned'}"
    
    cmd = [
        OMNET_BIN, "-u", "Cmdenv",
        "-n", ned_path,
        "-c", CONFIG,
        str(INI_FILE),
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("  ↳ finished successfully")
    except subprocess.CalledProcessError as e:
        print(f"  ↳ simulation failed with exit code {e.returncode}")
        if e.stderr:
            print(f"  ↳ stderr: {e.stderr[:200]}...")
        raise RuntimeError(f"Simulation failed: exit code {e.returncode}")

    dest = RESULT_DIR / f"n{n}"
    dest.mkdir(exist_ok=True)
    moved_any = False
    for ext in ("sca", "vec", "vci", "elog", "log"):
        for f in RESULT_DIR.glob(f"{CONFIG}-*.{ext}"):
            shutil.move(str(f), dest / f.name)
            moved_any = True
    if moved_any:
        print(f"  ↳ results → {dest}")
    else:
        print("  ↳ (no files moved; check result-dir & config names)")

def main():
    parser = argparse.ArgumentParser(description="Batch OMNeT++ runner (scale vs fixed sendInterval)")
    parser.add_argument("--mode", choices=["scale", "fixed"], default="scale",
                        help="Experiment mode: 'scale' (base_ms kept constant) or 'fixed' (effective interval kept constant)")
    parser.add_argument("--base-ms", type=float, default=1.5,
                        help="[scale] baseInterval in ms at N=5 (effective interval grows with N/5). Default=1.5")
    parser.add_argument("--fixed-ms", type=float, default=1.5,
                        help="[fixed] effective sendInterval in ms for all N. Default=1.5")
    parser.add_argument("--runs", nargs="*", type=int, default=DEFAULT_RUNS,
                        help=f"List of node counts. Default={DEFAULT_RUNS[0]}..{DEFAULT_RUNS[-1]} step 5")
    parser.add_argument("--restore-ned", action="store_true",
                        help="Restore NED to original backup after all runs")
    parser.add_argument("--no-timeslot", action="store_true",
                        help="Skip TimeSlot library (for debugging segfaults)")
    args = parser.parse_args()

    # 사전 검사
    check_prerequisites()
    
    if args.no_timeslot:
        print("[WARNING] Running without TimeSlot library")

    ensure_backup()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = RESULT_DIR / f"batch-{args.mode}-{ts}.txt"
    successful_runs = 0
    failed_runs = 0
    
    with log_path.open("w") as log:
        log.write(f"Batch run started: {datetime.datetime.now()}\n")
        log.write(f"Mode: {args.mode}\n")
        log.write(f"INET_DIR: {INET_DIR}\n")
        log.write(f"TimeSlot: {'disabled' if args.no_timeslot else 'enabled'}\n")
        log.write(f"Runs: {args.runs}\n\n")
        
        for n in args.runs:
            try:
                set_num_hosts(n)

                if args.mode == "scale":
                    base_sec = args.base_ms / 1000.0
                    set_cfg_base_interval_seconds(base_sec)
                    eff = args.base_ms * (n / 5.0)
                    print(f"  → [scale] base={args.base_ms} ms, expected effective ≈ {eff:.4f} ms")
                    log.write(f"N={n} SCALE base_ms={args.base_ms} eff_ms~={eff:.4f}\n")
                else:
                    if n <= 0:
                        raise ValueError("N must be positive.")
                    base_ms = args.fixed_ms * (5.0 / n)
                    base_sec = base_ms / 1000.0
                    set_cfg_base_interval_seconds(base_sec)
                    print(f"  → [fixed] effective={args.fixed_ms} ms (by base={base_ms:.6f} ms for N={n})")
                    log.write(f"N={n} FIXED eff_ms={args.fixed_ms} base_ms_for_N={base_ms:.6f}\n")

                run_one(n, use_timeslot=not args.no_timeslot)
                successful_runs += 1
                log.write(f"N={n} SUCCESS\n")

            except Exception as e:
                failed_runs += 1
                log.write(f"N={n} FAIL {e}\n")
                print(f"  ↳ ERROR at N={n}: {e}. Continue...\n")

        log.write(f"\nBatch completed: {datetime.datetime.now()}\n")
        log.write(f"Successful: {successful_runs}, Failed: {failed_runs}\n")

    print(f"[i] Batch log saved → {log_path}")
    print(f"[i] Summary: {successful_runs} successful, {failed_runs} failed")

    if args.restore_ned:
        shutil.copy(BACKUP_NED, NED_FILE)
        print("[i] Restored NED from backup.")

    print("All runs done.")

if __name__ == "__main__":
    main()
