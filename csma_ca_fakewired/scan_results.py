#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_results.py — OMNeT++ 결과(.sca/.vec, CSV-S/CSV-R) 빠른 패턴 검색 도구

지원:
- .sca scalar 파일:   'scalar <module> <name> <value>' 라인 파싱
- .vec vector 파일:   'vector <id> <module> <name> ...' 정의 라인 파싱(샘플 라인은 X)
- CSV-S/CSV-R 파일:   head 앞의 프롤로그를 건너뛰고 run,module,name,... 헤더부터 읽어 필터

기능:
- --pat 정규식으로 name 필드 매칭(대소문자 무시)
- --unique-names / --just-names 로 name 집계
- --csv-columns 로 CSV에서 뽑을 컬럼 지정
"""

import argparse
import csv
import glob
import io
import os
import re
import sys
from typing import List, Dict, Tuple

# ------------------------------ utils ------------------------------
def expand_paths(patterns: List[str]) -> List[str]:
    paths: List[str] = []
    for p in patterns:
        matches = glob.glob(p)
        if not matches and os.path.exists(p):
            matches = [p]
        paths.extend(sorted(matches))
    # dedup keep order
    seen = set(); out = []
    for x in paths:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def eprint(*a, **k):
    print(*a, file=sys.stderr, **k)

# ------------------------------ SCA ------------------------------
def scan_sca(paths: List[str], pat: re.Pattern, unique_names: bool, just_names: bool, limit: int):
    """
    .sca: 'scalar <module> <name> <value>'
    """
    counts: Dict[str, int] = {}
    printed = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    if not ln.startswith("scalar"):
                        continue
                    parts = ln.strip().split(None, 3)
                    if len(parts) < 4:
                        continue
                    _, module, name, value = parts
                    if pat and not pat.search(name):
                        continue
                    counts[name] = counts.get(name, 0) + 1
                    if just_names or unique_names:
                        continue
                    print(f"{path}\t{module}\t{name}\t{value}")
                    printed += 1
                    if limit and printed >= limit:
                        return
        except Exception as e:
            eprint(f"[SCA] read fail {path}: {e}")
    if just_names or unique_names:
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        for name, cnt in items:
            if just_names:
                print(name)
            else:
                print(f"{cnt}\t{name}")

# ------------------------------ VEC ------------------------------
def scan_vec(paths: List[str], pat: re.Pattern, unique_names: bool, just_names: bool, limit: int):
    """
    .vec: 벡터 '정의' 라인만 스캔 (샘플 라인은 생략)
    'vector <id> <module> <name> ...'
    """
    counts: Dict[str, int] = {}
    printed = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    if not ln.startswith("vector"):
                        continue
                    parts = ln.strip().split(None, 4)
                    if len(parts) < 4:
                        continue
                    _, vecid, module, name = parts[:4]
                    if pat and not pat.search(name):
                        continue
                    counts[name] = counts.get(name, 0) + 1
                    if just_names or unique_names:
                        continue
                    print(f"{path}\t{vecid}\t{module}\t{name}")
                    printed += 1
                    if limit and printed >= limit:
                        return
        except Exception as e:
            eprint(f"[VEC] read fail {path}: {e}")
    if just_names or unique_names:
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        for name, cnt in items:
            if just_names:
                print(name)
            else:
                print(f"{cnt}\t{name}")

# ------------------------------ CSV ------------------------------
def _find_csv_header(fh: io.TextIOBase) -> Tuple[List[str], int]:
    """
    opp_scavetool CSV의 헤더(run,module,name,...) 시작 라인 탐지
    반환: (헤더리스트, 헤더라인 인덱스)
    """
    fh.seek(0)
    lines = fh.readlines()
    header_idx = None
    for i, l in enumerate(lines):
        s = l.strip().lower()
        if s.startswith("run,") and ",module," in s and ",name," in s:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("CSV header not found (need columns: run,module,name,...)")
    header = [c.strip() for c in lines[header_idx].strip().split(",")]
    return header, header_idx

def scan_csv(paths: List[str], pat: re.Pattern, columns: List[str], unique_names: bool, just_names: bool, limit: int):
    counts: Dict[str, int] = {}
    printed = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                _, idx = _find_csv_header(fh)
                fh.seek(0)
                for _ in range(idx):
                    fh.readline()
                reader = csv.DictReader(fh)
                for rec in reader:
                    name = (rec.get("name") or "").strip()
                    if pat and not pat.search(name):
                        continue
                    counts[name] = counts.get(name, 0) + 1
                    if just_names or unique_names:
                        continue
                    if columns:
                        vals = [rec.get(c, "") for c in columns]
                    else:
                        prefer = ["run","module","name","value","time","vectime","vecvalue"]
                        vals = [rec.get(c,"") for c in prefer if c in rec]
                    print(path + "\t" + "\t".join(vals))
                    printed += 1
                    if limit and printed >= limit:
                        return
        except Exception as e:
            eprint(f"[CSV] read fail {path}: {e}")
    if just_names or unique_names:
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        for name, cnt in items:
            if just_names:
                print(name)
            else:
                print(f"{cnt}\t{name}")

# ------------------------------ main ------------------------------
def main():
    ap = argparse.ArgumentParser(description="Grep-like scanner for OMNeT++ .sca/.vec and opp_scavetool CSVs by regex over 'name'.")
    ap.add_argument("--mode", choices=["sca","vec","csv","auto"], default="auto",
                    help="파일 형식. auto는 확장자 기준 자동 판별")
    ap.add_argument("--glob", nargs="+", required=True,
                    help="입력 경로/글롭, 예: ini/results/*.sca  또는  data/all_*.csv")
    ap.add_argument("--pat", default=r"(retry|retrans|drop|collision|contentionWindowChanged|backoff|packetReceivedFromPeer)",
                    help="name 필드에 적용할 정규식(대소문자 무시)")
    ap.add_argument("--unique-names", action="store_true", help="이름별 건수만 출력")
    ap.add_argument("--just-names", action="store_true", help="이름 목록만 출력(건수 미표시)")
    ap.add_argument("--csv-columns", default="", help="CSV 출력 컬럼(쉼표로 구분). 예: run,module,name,value")
    ap.add_argument("--limit", type=int, default=0, help="최대 출력 행 수(0=무제한)")
    args = ap.parse_args()

    paths = expand_paths(args.glob)
    if not paths:
        eprint("입력 파일이 없습니다. --glob 패턴을 확인하세요.")
        sys.exit(2)

    try:
        pat = re.compile(args.pat, re.I)
    except re.error as e:
        eprint(f"정규식 오류: {e}")
        sys.exit(2)

    # 모드 자동 판별
    if args.mode == "auto":
        exts = {os.path.splitext(p)[1].lower() for p in paths}
        if exts == {".sca"}:
            mode = "sca"
        elif exts == {".vec"}:
            mode = "vec"
        elif ".csv" in exts or exts == {".csv"}:
            mode = "csv"
        else:
            mode = "csv" if any(p.endswith(".csv") for p in paths) else "sca"
    else:
        mode = args.mode

    columns = [c.strip() for c in args.csv_columns.split(",") if c.strip()] if args.csv_columns else []

    if mode == "sca":
        scan_sca(paths, pat, args.unique_names, args.just_names, args.limit)
    elif mode == "vec":
        scan_vec(paths, pat, args.unique_names, args.just_names, args.limit)
    elif mode == "csv":
        scan_csv(paths, pat, columns, args.unique_names, args.just_names, args.limit)
    else:
        eprint(f"Unsupported mode: {mode}")
        sys.exit(2)

if __name__ == "__main__":
    main()
