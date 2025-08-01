#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNeT++ 6.1 / opp_scavetool 결과 후처리 스크립트
- 필터 없이 전체 덤프(CSV-R, CSV-S) → Python에서 name/module로 필터링
"""

import os
import sys
import glob
import csv
import io
import subprocess
import pandas as pd
from typing import List, Tuple

# EDCA AC 인덱스 → 이름 매핑
AC_MAP = {0: 'AC_VO', 1: 'AC_VI', 2: 'AC_BE', 3: 'AC_BK'}

# ------------------------- 사용자 설정 -------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR   = os.path.join(SCRIPT_DIR, 'data')
RESULTS_DIR  = os.path.join(SCRIPT_DIR, '..', '..', 'ini', 'results')

# 벡터 필터 키워드(부분 문자열 AND)
THR_NAME_KEYS    = ['packetReceivedFromPeer']   # with/withoutRetry 모두 매치
THR_MODULE_KEYS  = []                           # 모듈 제한 없음
CW_NAME_KEYS     = ['contentionWindowChanged']  # EDCA/DCF 공통 키워드

# 스칼라 이름(정확 일치)
RETRY_NAMES = [
    'packetSentToPeerWithRetry:count',
    'packetSentToPeerWithoutRetry:count',
    # 필요 시 바이트 합계도 확인 가능
    # 'packetSentToPeerWithRetry:sum(packetBytes)',
    # 'packetSentToPeerWithoutRetry:sum(packetBytes)',
]

# ✅ DCF 전용 지표는 사용하지 않습니다.
# SENT_NAME / SENT_MODULE_KEY 제거
# DROP_NAME / DROP_MODULE_KEY도 모듈 제한을 두지 않습니다.
DROP_NAME = 'retryLimitReached'   # INET 4.5.4 호환
# ---------------------------------------------------------------


def run_cmd(cmd: List[str], desc: str) -> str:
    print(f"🚀 {desc}...")
    print("   $", " ".join(cmd))
    try:
        p = subprocess.run(cmd, check=True, text=True,
                           capture_output=True, encoding='utf-8')
        if p.stdout.strip():
            print(p.stdout.strip())
        print("✅ 완료\n")
        return p.stdout
    except FileNotFoundError:
        print(f"❌ '{cmd[0]}' 명령을 찾을 수 없습니다. PATH 확인.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ 에러: {desc}")
        print("---- stdout ----")
        print(e.stdout)
        print("---- stderr ----")
        print(e.stderr)
        sys.exit(1)


def ensure_files() -> Tuple[List[str], List[str]]:
    vec_files = glob.glob(os.path.join(RESULTS_DIR, '*.vec'))
    sca_files = glob.glob(os.path.join(RESULTS_DIR, '*.sca'))
    if not vec_files and not sca_files:
        print(f"❌ .vec/.sca 결과 파일이 없습니다. 경로: {RESULTS_DIR}")
        sys.exit(1)
    print(f"🔎 vec files: {len(vec_files)}개 / sca files: {len(sca_files)}개 발견")
    return vec_files, sca_files


def dump_all(vec_files: List[str], sca_files: List[str],
             vec_out: str, sca_out: str):
    # 벡터 전체
    cmd_v = ['opp_scavetool', 'x', '-v', '-F', 'CSV-R', '-o', vec_out] + vec_files
    run_cmd(cmd_v, "벡터 전체 덤프")

    # 스칼라+파라미터 전체
    cmd_s = ['opp_scavetool', 'x', '-F', 'CSV-S', '-x', 'allowMixed=true', '-o', sca_out] + sca_files
    run_cmd(cmd_s, "스칼라/파라미터 전체 덤프")


def read_scavetool_csv(path: str) -> pd.DataFrame:
    """opp_scavetool CSV에서 헤더 줄을 찾아 pandas로 읽는다"""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    header_idx = None
    for i, l in enumerate(lines):
        if l.strip().startswith('run,') and ',module,' in l and ',name,' in l:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Header not found in {path}")
    csv_text = ''.join(lines[header_idx:])
    return pd.read_csv(io.StringIO(csv_text), engine='python', on_bad_lines='skip')

def filter_vectors(in_csv: str, out_csv: str,
                   name_keys: List[str] = None,
                   module_keys: List[str] = None):
    name_keys   = name_keys or []
    module_keys = module_keys or []

    df = read_scavetool_csv(in_csv)

    # 헤더 컨텍스트 전파
    for col in ['run', 'module', 'name']:
        if col in df.columns:
            df[col] = df[col].replace('', pd.NA).ffill()

    # CSV-R 벡터 컬럼 확인
    if 'vectime' in df.columns and 'vecvalue' in df.columns:
        tcol, vcol = 'vectime', 'vecvalue'
        # ✅ 숫자 변환 금지! 문자열이 비어있지 않은지만 확인
        sel = df[tcol].astype(str).str.strip().ne('') & df[vcol].astype(str).str.strip().ne('')
    else:
        # (CSV ‘샘플당 1행’ 형식일 때만 숫자 확인)
        tcol, vcol = 'time', 'value'
        sel = pd.to_numeric(df[tcol], errors='coerce').notna() & pd.to_numeric(df[vcol], errors='coerce').notna()

    # 이름/모듈 키워드(AND)
    for k in name_keys:
        sel &= df['name'].str.contains(k, case=False, na=False)
    for k in module_keys:
        sel &= df['module'].str.contains(k, case=False, na=False)

    kept = df.loc[sel].copy()
    kept.to_csv(out_csv, index=False)
    print(f"ℹ️  {os.path.basename(out_csv)}: {len(kept)} vector data rows kept "
          f"(name_keys={name_keys}, module_keys={module_keys})")


def filter_rows(in_csv: str, out_csv: str,
                name_keys: List[str] = None,
                module_keys: List[str] = None,
                name_exact: List[str] = None):
    """부분/정확 일치로 행 필터링"""
    name_keys   = name_keys or []
    module_keys = module_keys or []
    name_exact  = name_exact or []

    df = read_scavetool_csv(in_csv)

    sel = pd.Series([True] * len(df))
    if name_exact:
        sel &= df['name'].isin(name_exact)

    if name_keys:
        for k in name_keys:
            sel &= df['name'].str.contains(k, case=False, na=False)

    if module_keys:
        for k in module_keys:
            sel &= df['module'].str.contains(k, case=False, na=False)

    kept_df = df[sel].copy()
    kept_df.to_csv(out_csv, index=False)
    print(f"ℹ️  {os.path.basename(out_csv)}: {len(kept_df)} rows kept "
          f"(name_exact={name_exact}, name_keys={name_keys}, module_keys={module_keys})")


def to_float_safe(x):
    try:
        return float(x)
    except Exception:
        return None


def sum_scalar(in_csv: str, target_name: str, module_key: str = None) -> float:
    df = read_scavetool_csv(in_csv)
    df['value_num'] = df['value'].apply(to_float_safe)
    sel = df['name'] == target_name
    if module_key:
        sel &= df['module'].str.contains(module_key, case=False, na=False)
    return df.loc[sel, 'value_num'].sum(skipna=True)

def _parse_series(cell: str):
    if not isinstance(cell, str):
        return []
    s = cell.strip().replace('[',' ').replace(']',' ').replace(',',' ')
    parts = [p for p in s.split() if p]
    try:
        return [float(p) for p in parts]
    except ValueError:
        return []

def compute_avg_bps(throughput_csv_path, out_csv_path):
    df = read_scavetool_csv(throughput_csv_path)
    if df.empty:
        print("📈 스루풋 계산: 입력 벡터가 없습니다.")
        return None

    rows = []
    if 'vectime' in df.columns and 'vecvalue' in df.columns:
        # ✅ CSV-R: 한 행에 리스트가 들어있음
        for _, r in df.iterrows():
            times = _parse_series(r.get('vectime'))
            vals  = _parse_series(r.get('vecvalue'))
            if len(times) >= 2 and len(vals) == len(times):
                duration = times[-1] - times[0]
                totalB   = sum(vals)
                if duration > 0:
                    rows.append({
                        'run': r['run'], 'module': r['module'], 'name': r['name'],
                        'samples': len(times), 'duration': duration,
                        'sum_bytes': totalB, 'avg_bps': 8.0 * totalB / duration
                    })
    else:
        # (CSV ‘샘플당 1행’ 형식일 때)
        tcol = 'time'; vcol = 'value'
        df[tcol] = pd.to_numeric(df[tcol], errors='coerce')
        df[vcol] = pd.to_numeric(df[vcol], errors='coerce')
        df = df.dropna(subset=[tcol, vcol])
        for (r, m, n), g in df.groupby(['run','module','name']):
            g = g.sort_values(tcol)
            if len(g) < 2:
                continue
            duration = g[tcol].iloc[-1] - g[tcol].iloc[0]
            totalB   = g[vcol].sum()
            if duration > 0:
                rows.append({'run': r, 'module': m, 'name': n,
                             'samples': len(g), 'duration': duration,
                             'sum_bytes': totalB, 'avg_bps': 8.0 * totalB / duration})

    out = pd.DataFrame(rows)
    out.to_csv(out_csv_path, index=False)
    if not out.empty:
        print(f"📈 평균 스루풋 rows: {len(out)}  (저장: {out_csv_path})")
        print(f"   전체 평균: {out['avg_bps'].mean():.2f} bps")
    else:
        print("📈 스루풋 계산할 행이 없습니다.")
    return out


def compute_retry_ratio(all_sca_csv_path):
    """재시도 프레임 비율(%) 계산"""
    df = read_scavetool_csv(all_sca_csv_path)
    w  = df.loc[df['name']=='packetSentToPeerWithRetry:count','value'].astype(float).sum()
    wo = df.loc[df['name']=='packetSentToPeerWithoutRetry:count','value'].astype(float).sum()
    tot = w + wo
    ratio = (w / tot * 100.0) if tot > 0 else 0.0
    print(f"🔁 재시도 프레임: {w:.0f}/{tot:.0f}  ({ratio:.2f}%)")
    return ratio

def cw_change_summary(cw_csv_path):
    """CW 변경 이벤트 개수(빠른 sanity 체크)"""
    df = read_scavetool_csv(cw_csv_path)
    print(f"⚙️ CW 변경 이벤트 수: {len(df)}")
    return len(df)

def scan_drops(all_sca_csv_path):
    df = read_scavetool_csv(all_sca_csv_path)
    cand = df[df['name'].astype(str).str.contains('drop|queue|overflow|discard|fail', case=False, na=False)].copy()
    cand['value_num'] = pd.to_numeric(cand['value'], errors='coerce')

    # 합계 TOP10 먼저
    top = (cand.groupby('name')['value_num']
               .sum()
               .sort_values(ascending=False)
               .head(10))
    print("\n🔎 Drop-like 지표 TOP10(합계):")
    print(top.to_string())

    # 예시 20행 미리보기
    print("\n🔎 예시 20행 미리보기:")
    print(cand[['module','name','value']].head(20).to_string(index=False))
    return cand


# ---- postProcessing.py (일부) ----
def total_tx_frames(all_sca_csv_path: str) -> float:
    df = read_scavetool_csv(all_sca_csv_path)
    df['value_num'] = df['value'].apply(to_float_safe)
    # EDCA·DCF 공통으로 이름만 보고 합계
    return df[df['name'].isin(RETRY_NAMES)]['value_num'].sum(skipna=True)



def total_retrylimit_drops(all_sca_csv_path: str) -> float:
    df = read_scavetool_csv(all_sca_csv_path)
    df['value_num'] = df['value'].apply(to_float_safe)
    mask = (df['name'] == 'packetDropRetryLimitReached:count')
    return df.loc[mask, 'value_num'].sum(skipna=True)

def total_arp_fail(all_sca_csv_path: str) -> float:
    """IP 계층의 주소해결 실패(ARP 실패) 총합."""
    df = read_scavetool_csv(all_sca_csv_path)
    df['value_num'] = df['value'].apply(to_float_safe)
    mask = (df['name'] == 'packetDropAddressResolutionFailed:count')
    return df.loc[mask, 'value_num'].sum(skipna=True)

def edca_ac_breakdown(all_sca_csv_path: str):
    df = read_scavetool_csv(all_sca_csv_path)
    df['value_num'] = df['value'].apply(to_float_safe)

    m = df['module'].str.contains(r'mac\.hcf\.edca\.edcaf\[\d+\]', case=False, na=False)
    n = df['name'].isin(['packetSentToPeerWithRetry:count', 'packetSentToPeerWithoutRetry:count'])
    g = df.loc[m & n, ['module', 'name', 'value_num']].copy()
    if g.empty:
        return g

    # edcaf 인덱스 추출 → AC 라벨링
    g['ac'] = pd.to_numeric(g['module'].str.extract(r'edcaf\[(\d+)\]', expand=False), errors='coerce').astype('Int64')
    g['ac_name'] = g['ac'].map(AC_MAP)

    g = (g.groupby(['ac', 'ac_name', 'module', 'name'], dropna=False)['value_num']
           .sum()
           .reset_index()
           .sort_values(['ac', 'name', 'module']))

    if not g.empty:
        print("\n[EDCA per-AC 전송 프레임 합계]")
        print(g.to_string(index=False))
    return g


def compute_avg_bps_fallback_from_scalars(all_sca_csv_path: str,
                                          sim_time_limit_sec: float = 30.0):
    """
    CSV-R 벡터(throughput)가 비어 있을 때 UDP Sink의
    rcvdPk:sum(packetBytes) 스칼라 합계로 평균 bps 계산.
    """
    df = read_scavetool_csv(all_sca_csv_path)
    m = df['name'].astype(str).str.contains(r'rcvdPk:sum\(packetBytes\)', case=False, na=False)
    total_bytes = pd.to_numeric(df.loc[m, 'value'], errors='coerce').fillna(0).sum()
    avg_bps = 8.0 * total_bytes / sim_time_limit_sec if sim_time_limit_sec > 0 else 0.0
    print(f"📈[fallback] UDP 수신 합계={total_bytes:.0f} bytes → 평균 {avg_bps:.2f} bps")
    return avg_bps


def total_retrycount_scalar(all_sca_csv_path: str) -> float:
    """
    일부 런에서 제공되는 retryCount 스칼라 합계 집계.
    (있으면 재시도 경향 파악에 도움이 됨)
    """
    df = read_scavetool_csv(all_sca_csv_path)
    df['value_num'] = pd.to_numeric(df['value'], errors='coerce')
    return df.loc[df['name'] == 'retryCount', 'value_num'].sum(skipna=True)


def main():
    print("--- OMNeT++ 결과 데이터 후처리 시작 ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 결과 저장: {OUTPUT_DIR}\n")

    vec_files, sca_files = ensure_files()

    # 1) 전체 덤프
    all_vec_csv = os.path.join(OUTPUT_DIR, 'all_vectors.csv')
    all_sca_csv = os.path.join(OUTPUT_DIR, 'all_scalars.csv')
    dump_all(vec_files, sca_files, all_vec_csv, all_sca_csv)

    # 2) Throughput 벡터 추출
    thr_csv = os.path.join(OUTPUT_DIR, 'throughput.csv')
    filter_vectors(all_vec_csv, thr_csv,
                   name_keys=THR_NAME_KEYS,
                   module_keys=THR_MODULE_KEYS)

    # 3) CW 벡터 추출
    cw_csv = os.path.join(OUTPUT_DIR, 'cw_data.csv')
    filter_vectors(all_vec_csv, cw_csv,
                   name_keys=CW_NAME_KEYS)

    # 4) Retry 스칼라 추출 (그대로 저장)
    retry_csv = os.path.join(OUTPUT_DIR, 'retry_counts.csv')
    filter_rows(all_sca_csv, retry_csv,
                name_exact=RETRY_NAMES)

    # 5) Packet Loss Rate 계산 (MAC 재시도 한계 기준)
    total_sent    = total_tx_frames(all_sca_csv)                # ✅ 수정
    total_dropped = total_retrylimit_drops(all_sca_csv)         # ✅ 수정
    arp_failed    = total_arp_fail(all_sca_csv)                 # ✅ 추가

    loss_rate = (total_dropped / total_sent * 100.0) if total_sent > 0 else 0.0

    # 6) 스루풋/재시도/CW 요약
    out = compute_avg_bps(thr_csv, os.path.join(OUTPUT_DIR, 'throughput_bps.csv'))
    if out is None or getattr(out, 'empty', True):
        # sim-time-limit(기본 30s)에 맞춰 조정 가능
        compute_avg_bps_fallback_from_scalars(all_sca_csv, sim_time_limit_sec=5.0)

    compute_retry_ratio(all_sca_csv)
    cw_change_summary(cw_csv)
    retry_count_sum = total_retrycount_scalar(all_sca_csv)

    summary = (
        "----- 요약 -----\n"
        f"- 총 전송 프레임(EDCA/DCF 합): {total_sent:.0f}\n"
        f"- MAC 재시도 한계 드랍: {total_dropped:.0f}\n"
        f"- 패킷 손실률(=재시도한계드랍/전송): {loss_rate:.2f}%\n"
        f"- IP 주소해결 실패(ARP 실패): {arp_failed:.0f}\n"
        f"- retryCount(스칼라 합): {retry_count_sum:.0f}\n"
    )
    print(summary)

    with open(os.path.join(OUTPUT_DIR, 'packet_loss_summary.txt'), 'w', encoding='utf-8') as f:
        f.write(summary.strip())

    # 필요 시 드롭 스캔 활성화
    # scan_drops(all_sca_csv)

    # edca_ac_breakdown(all_sca_csv)

   # ---------- MAC 효율 계산 ----------  ← 기존 블록을 전부 대체 -----------------
    # (예) IEEE 802.11g 12 Mbps Baseline용 상수
    PHY_DATA_RATE      = 12_000_000  # bps
    PHY_SLOT_TIME      = 9e-6        # 9 µs
    PHY_RIFS           = 2e-6        # 802.11g RIFS 2 µs (필요 없으면 0)
    PHY_CIFS           = 34e-6       # DIFS ≈ 34 µs
    PHY_ACK_TIME       = 44e-6       # PHY preamble+ACK bits @24 Mbps
    PKT_BYTES          = 1500

    # 신호 전송시간 = 프리앰블/PHY 헤더 + 데이터/ACK 전송시간
    def tx_time(payload_bytes, rate_bps):
        return (payload_bytes * 8) / rate_bps      # data-only (PHY 헤더 등은 무시)

    T_FRAME = tx_time(PKT_BYTES, PHY_DATA_RATE)    # 데이터 프레임
    T_ACK   = PHY_ACK_TIME
    T_S     = T_FRAME + PHY_RIFS + T_ACK + PHY_CIFS      # 성공 기간
    T_C     = T_FRAME + PHY_CIFS                         # 충돌 기간
    T_I     = PHY_SLOT_TIME                              # idle 기간

    # === 1) 성공·충돌·전송 카운트 ===
    succ_pkts   = sum_scalar(all_sca_csv, 'packetReceivedFromPeer:count')
    tx_with_r   = sum_scalar(all_sca_csv, 'packetSentToPeerWithRetry:count')
    tx_wo_r     = sum_scalar(all_sca_csv, 'packetSentToPeerWithoutRetry:count')
    tx_attempts = tx_with_r + tx_wo_r
    collisions  = total_retrylimit_drops(all_sca_csv)     # = 재시도 한계 초과
    idle_slots  = 0                                       # (별도 벡터를 끌어오면 채워주세요)

    if tx_attempts == 0:
        print("⚠️  전송 시도가 0 입니다. η 계산 불가")
        eta = 0.0
    else:
        P_S = succ_pkts / tx_attempts
        P_C = collisions / tx_attempts
        P_I = 1.0 - P_S - P_C                                # 남는 시간을 idle 로 가정

        # === 2) 식 (4) 적용 ===
        E_DATA_bits = PKT_BYTES * 8
        numerator   = P_S * E_DATA_bits
        denominator = (P_S * T_S + P_I * T_I + P_C * T_C) * PHY_DATA_RATE
        eta         = numerator / denominator if denominator else 0.0

        print(f"P_S={P_S:.4f}, P_I={P_I:.4f}, P_C={P_C:.4f}")
        print(f"T_S={T_S*1e6:.2f} µs  T_I={T_I*1e6:.2f} µs  T_C={T_C*1e6:.2f} µs")

    print(f"🎯  MAC 효율 η ≈ {eta:.3f}")
    print("✅ 완료")
    # --------------------------------------------------------------------------



if __name__ == "__main__":
    main()
