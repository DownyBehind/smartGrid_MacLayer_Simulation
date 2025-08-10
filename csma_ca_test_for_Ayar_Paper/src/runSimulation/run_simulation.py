#!/usr/bin/env python3
import subprocess
import shutil
import pathlib
import datetime
import os
import re

# ─────── 경로 설정 ───────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT    = SCRIPT_DIR.parent.parent   # …/csma_ca_test_for_Ayar_Paper
INET_DIR   = pathlib.Path(os.environ.get(
    "INET_DIR",
    "/home/kimdawoon/study/workspace/research/inet"
))
INET_SRC   = INET_DIR / "src"
TIME_SLOT  = PROJECT.parent / "TimeSlot"

# NED 파일 경로 (numHosts 수정 대상)
NED_FILE   = PROJECT / "ned" / "csma_ca_test_for_Ayar_Paper" / "FakeWireCsmaCaNetwork.ned"
BACKUP_NED = NED_FILE.with_suffix(".ned.bak")

# NED 경로: INET/src; 프로젝트 ned; TimeSlot
NED_PATH   = f"{INET_SRC};{PROJECT/'ned'};{TIME_SLOT}"

INI_FILE   = PROJECT / "ini" / "omnetpp.ini"
RESULT_DIR = PROJECT / "ini" / "results"
CONFIG     = "Paper_Baseline"
OMNET_BIN  = "opp_run"
RUNS       = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150]
# ──────────────────────────

# 최초 실행 시 원본 백업
if not BACKUP_NED.exists():
    shutil.copy(NED_FILE, BACKUP_NED)

def set_num_hosts(n):
    """FakeWireCsmaCaNetwork.ned 파일 내 default(numHosts) 값을 n으로 변경"""
    text = BACKUP_NED.read_text()
    # int numHosts = default(X);
    new_text = re.sub(
        r'int\s+numHosts\s*=\s*default\(\s*\d+\s*\)\s*;',
        f'int numHosts = default({n});',
        text
    )
    NED_FILE.write_text(new_text)
    print(f"  → NED numHosts default({n})로 설정")

def run_one(n):
    print(f"▶ N={n} 시뮬레이션 시작")
    set_num_hosts(n)
    cmd = [
        OMNET_BIN, "-u", "Cmdenv",
        "-n", NED_PATH,
        "-c", CONFIG,
        str(INI_FILE),
    ]
    subprocess.run(cmd, check=True)
    print("  ↳ 종료")

    # 결과 파일 이동
    dest = RESULT_DIR / f"n{n}"
    dest.mkdir(exist_ok=True)
    for ext in ("sca", "vec", "vci", "elog", "log"):
        for f in RESULT_DIR.glob(f"{CONFIG}-*.{ext}"):
            shutil.move(str(f), dest / f.name)
    print(f"  ↳ 결과 → {dest}")

def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with (RESULT_DIR / f"batch-{ts}.txt").open("w") as log:
        for n in RUNS:
            try:
                run_one(n)
                log.write(f"N={n} OK\n")
            except Exception as e:
                log.write(f"N={n} FAIL {e}\n")
                print("  ↳ 에러 발생, 계속 진행")
    print("모든 실험 완료")

if __name__=="__main__":
    main()

