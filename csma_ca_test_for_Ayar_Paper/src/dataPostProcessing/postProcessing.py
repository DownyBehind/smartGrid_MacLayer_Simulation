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
# 파일 상단 import들 아래에 추가
import re
from pathlib import Path


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


# ===== MAC 효율(논문 식 (4)) 계산 헬퍼 =====

def _tx_time_bytes(payload_bytes, rate_bps):
    return (payload_bytes * 8.0) / float(rate_bps)

def compute_mac_efficiency_from_results(
    all_sca_csv: str,
    thr_df,             # compute_avg_bps() 결과 DataFrame (sum_bytes/avg_bps 포함)
    sim_time_sec,
    phy_rate_bps=12_000_000,   # Baseline: 12 Mbps
    slot_time=9e-6,            # 802.11g slot
    rifs=2e-6,                 # 802.11g RIFS
    cifs=34e-6,                # DIFS(유사치)
    ack_time=44e-6,            # preamble+ACK 시간(근사)
    pkt_bytes=1500,            # 데이터 페이로드 바이트
    verbose=True
    ):
    """
    논문 식(4) η = P_S*E[Data] / (P_S*T_S + P_I*T_I + P_C*T_C) / R 로 계산.
    P_S: 성공확률, P_C: 충돌/드롭 확률, P_I: idle 확률(1-P_S-P_C)
    카운트류는 스칼라에서 가져오고, 없을 경우 thr_df로 추정.
    """
    # (1) 카운트 추출
    succ_pkts_scalar = sum_scalar(all_sca_csv, 'packetReceivedFromPeer:count')  # 성공 수신
    tx_with_r   = sum_scalar(all_sca_csv, 'packetSentToPeerWithRetry:count') or 0
    tx_wo_r     = sum_scalar(all_sca_csv, 'packetSentToPeerWithoutRetry:count') or 0
    retry_limit = sum_scalar(all_sca_csv, 'retryLimitReached:count') or 0

    # 총 전송 시도: PHY로 내려간 송신(가장 보편적). 없으면 성공+드롭으로 근사
    tx_attempts_phy = sum_scalar(all_sca_csv, 'packetSentToLower:count')
    tx_attempts = int(tx_attempts_phy or (tx_with_r + tx_wo_r + retry_limit))

    # 드롭(재시도 한계) 카운트: 빌드에 따라 없을 수 있음 → 없으면 0
    retry_limit = sum_scalar(all_sca_csv, 'retryLimitReached:count') or 0

    # (2) succ_pkts 보정: 스칼라가 없으면 thr_df에서 추정
    succ_bytes = 0
    if thr_df is not None and not thr_df.empty:
        if 'sum_bytes' in thr_df.columns:
            succ_bytes = float(thr_df['sum_bytes'].sum())
    if succ_pkts_scalar is not None:
        succ_pkts = float(succ_pkts_scalar)
    else:
        succ_pkts = (succ_bytes / float(pkt_bytes)) if pkt_bytes > 0 else 0.0

    # 보호: tx_attempts가 0이면 효율 계산 불가
    if tx_attempts <= 0:
        if verbose:
            print("⚠️  전송 시도가 0입니다. η 계산을 생략합니다.")
        return {
            'eta': 0.0, 'P_S': 0.0, 'P_I': 0.0, 'P_C': 0.0,
            'T_S': 0.0, 'T_I': slot_time, 'T_C': 0.0,
            'succ_pkts': 0, 'tx_attempts': 0, 'collisions': 0
        }

    # (3) 확률 계산
#    P_S = succ_pkts / tx_attempts if tx_attempts > 0 else 0.0
#    P_C = ((retry_limit + tx_with_r) / tx_attempts) if tx_attempts > 0 else 0.0  # 재시도한계도달을 충돌/실패로 집계
#    P_I = max(0.0, 1.0 - P_S - P_C)

    # (3) 확률 계산 ― 패킷 기반 근사치
    P_S, P_C, P_I, coll_slots = estimate_probs_from_packets(
        all_sca_csv,
        slot_time=slot_time,
        sim_time_sec=sim_time_sec          # ▼ (아래 호출부에서 넘김)
    )
    # (4) 시간 상수
    T_FRAME = _tx_time_bytes(pkt_bytes, phy_rate_bps)
    T_ACK   = ack_time
    T_S     = T_FRAME + rifs + T_ACK + cifs
    T_C     = T_FRAME + cifs
    T_I     = slot_time

    # (5) 식 (4)
    E_DATA_bits = pkt_bytes * 8.0
    numerator   = P_S * E_DATA_bits
    denominator = (P_S * T_S + P_I * T_I + P_C * T_C) * phy_rate_bps
    eta         = (numerator / denominator) if denominator > 0 else 0.0

    if verbose:
        print(f"P_S={P_S:.4f}, P_I={P_I:.4f}, P_C={P_C:.4f}")
        print(f"T_S={T_S*1e6:.2f} µs  T_I={T_I*1e6:.2f} µs  T_C={T_C*1e6:.2f} µs")
        print(f"🎯  MAC 효율 η ≈ {eta:.3f}")

    # --- [ADD] Rate-efficiency (payload throughput / PHY rate) --------------------    
    # payload_bits_delivered 계산 (가급적 스칼라 → 없으면 thr_df → 최후 succ_pkts*pkt_bytes)
    payload_bits = 0

    # 1) 스칼라에 packet 바이트 합이 노출되어 있다면 (가장 정확)
    succ_bytes_scalar = sum_scalar(all_sca_csv, 'packetReceivedFromPeer:sum(packetBytes)')
    if succ_bytes_scalar is not None:
        payload_bits = int(succ_bytes_scalar) * 8

    # 2) 없으면 thr_df의 합계를 사용 (모듈 평균이 아니라 반드시 '합(sum_bytes)' 사용)
    elif thr_df is not None and not thr_df.empty and 'sum_bytes' in thr_df.columns:
        payload_bits = int(thr_df['sum_bytes'].sum()) * 8

    # 3) 최후 보정: 성공 패킷 수 × 페이로드 크기(가정)
    else:
        payload_bits = int(succ_pkts) * int(pkt_bytes) * 8

    # η_rate = (전달 payload 처리율) / PHY rate
    eta_rate = (payload_bits / float(sim_time_sec)) / float(phy_rate_bps)
    # ------------------------------------------------------------------------------

    # 기존 return 딕셔너리에 함께 넣기
    return {
        'eta': eta,                       # (기존: time-efficiency 추정치)
        'eta_rate': eta_rate,             # (추가) rate-efficiency
        'P_S': P_S, 'P_I': P_I, 'P_C': P_C,
        'T_S': T_S, 'T_I': T_I, 'T_C': T_C,
        'succ_pkts': int(succ_pkts),
        'tx_attempts': int(tx_attempts),
        'collisions': coll_slots
    }


def write_packet_loss_summary_txt(path: str, n: int, metrics: dict, extra: dict):
    """
    packet_loss_summary.txt 작성
    """
    lines = []
    lines.append(f"n={n}")
    lines.append(f"총 전송 시도: {metrics.get('tx_attempts',0)}")
    lines.append(f"성공 패킷: {metrics.get('succ_pkts',0)}")
    lines.append(f"충돌/드롭(재시도한계): {metrics.get('collisions',0)}")
    lines.append(f"P_S={metrics.get('P_S',0):.4f}, P_I={metrics.get('P_I',0):.4f}, P_C={metrics.get('P_C',0):.4f}")
    lines.append(f"T_S={metrics.get('T_S',0)*1e6:.2f} µs  T_I={metrics.get('T_I',0)*1e6:.2f} µs  T_C={metrics.get('T_C',0)*1e6:.2f} µs")
    lines.append(f"MAC 효율 η ≈ {metrics.get('eta',0):.3f}")
    # 부가 정보
    # --- [ADD] η_rate 표시 --------------------------------------------------------
    if 'eta_rate' in metrics:
        lines.append(f"Rate 효율 η_rate ≈ {metrics['eta_rate']:.3f}  (payload throughput / PHY rate)")
    # -----------------------------------------------------------------------------                                                                         
    if 'avg_bps' in extra:
        lines.append(f"평균 스루풋(bps-벡터평균): {extra['avg_bps']:.2f}")
    if 'retry_with' in extra and 'retry_without' in extra:
        tot = (extra['retry_with'] or 0) + (extra['retry_without'] or 0)
        rw  = extra['retry_with'] or 0
        pct = (rw / tot * 100.0) if tot > 0 else 0.0
        lines.append(f"재시도 프레임: {rw}/{tot}  ({pct:.2f}%)")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------------
# 패킷 통계만으로 P_S, P_C, P_I 근사 계산 (Time-budget 방식)
# - all_sca_csv : opp_scavetool로 덤프한 스칼라 CSV 경로
# - slot_time   : 802.11 슬롯 시간(예: 9e-6)
# - sim_time_sec: 시뮬레이션 총 시간(초)
# 나머지 파라미터는 기본값(12 Mbps, 1500B, SIFS/DIFS/ACK)으로 둬도 됨
# ---------------------------------------------------------------------
def estimate_probs_from_packets(all_sca_csv: str,
                                slot_time: float,
                                sim_time_sec: float,
                                phy_rate_bps: float = 12_000_000,
                                pkt_bytes: int      = 1500,
                                sifs: float         = 16e-6,
                                difs: float         = 34e-6,
                                ack_time: float     = 44e-6):
    # 성공/재시도/드롭 카운트
    W0 = sum_scalar(all_sca_csv, 'packetSentToPeerWithoutRetry:count') or 0
    W1 = sum_scalar(all_sca_csv, 'packetSentToPeerWithRetry:count') or 0
    # 드롭 이름은 빌드에 따라 다를 수 있어 둘 다 시도
    D  = (sum_scalar(all_sca_csv, 'packetDropRetryLimitReached:count')
          or sum_scalar(all_sca_csv, 'retryLimitReached:count')
          or 0)
    # PHY로 내려간 총 송신 수(데이터/관리 포함). 없으면 보수적으로 대체
    L  = sum_scalar(all_sca_csv, 'packetSentToLower:count') or (W0 + W1 + D)

    # 충돌 슬롯 추정 (하한/상한 평균)
    C_min = W1 + 8 * D
    C_max = max(L - (W0 + W1 + D), C_min)
    C_est = 0.5 * (C_min + C_max)

    # 프레임/슬롯 시간
    t_frame = (pkt_bytes * 8.0) / float(phy_rate_bps)
    T_S = t_frame + sifs + ack_time + difs
    T_C = t_frame + difs

    # idle 슬롯 개수: 전체 시간 보존식에서 역산
    idle_slots = max(0.0, (sim_time_sec - (W0 + W1) * T_S - C_est * T_C) / slot_time)

    # 시간 비중을 확률로 사용
    if sim_time_sec <= 0:
        return 0.0, 0.0, 0.0, int(round(C_est))

    P_S = ((W0 + W1) * T_S) / sim_time_sec
    P_C = (C_est * T_C) / sim_time_sec

    # 1차 계산 후 정합성 보장:
    if P_S + P_C >= 1.0:
        # idle은 0으로, 성공/충돌을 비율 유지한 채 1로 스케일
        scale = 1.0 / (P_S + P_C)
        P_S *= scale
        P_C *= scale
        P_I = 0.0
    else:
        P_I = 1.0 - P_S - P_C

    # 수치 오차만 최소한의 클램핑
    eps = 1e-12
    P_S = min(max(P_S, 0.0), 1.0)
    P_C = min(max(P_C, 0.0), 1.0)
    P_I = min(max(P_I, 0.0), 1.0)

    return P_S, P_C, P_I, int(round(C_est))

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

def collect_runs_by_n(results_dir: str, conf_prefix: str = "Paper_Baseline"):
    """
    results_dir 안의 .vec/.sca 파일을 스캔해서
    파일명 패턴:  <conf_prefix>-n=<N>-#<run>.{vec|sca}
    를 찾아 N(노드 수)별로 묶어 return.

    return 예시:
    {
      5:  {'vec': ['/.../Paper_Baseline-n=5-#0.vec'], 'sca': ['/.../Paper_Baseline-n=5-#0.sca']},
      20: {'vec': ['/.../Paper_Baseline-n=20-#0.vec'], 'sca': ['/.../Paper_Baseline-n=20-#0.sca']},
      ...
    }
    """
    runs = {}
    p = Path(results_dir)
    for f in p.glob(f"{conf_prefix}-n=*#*.*"):
        m = re.search(rf"{re.escape(conf_prefix)}-n=(\d+)-#\d+\.(vec|sca)$", f.name)
        if not m:
            continue
        n = int(m.group(1))
        ext = m.group(2)
        runs.setdefault(n, {'vec': [], 'sca': []})
        runs[n][ext].append(str(f))
    # 각 n마다 vec/sca 최신 것 1개만 쓰도록 정리(여러 run 있을 때)
    for n in list(runs.keys()):
        runs[n]['vec'] = sorted(runs[n]['vec'])[-1:] if runs[n]['vec'] else []
        runs[n]['sca'] = sorted(runs[n]['sca'])[-1:] if runs[n]['sca'] else []
        if not runs[n]['vec'] and not runs[n]['sca']:
            runs.pop(n, None)
    return runs

def make_outputs_for_n(output_dir: str, n: int):
    """
    n 값별 출력 파일 경로 묶음 반환
    """
    odir = Path(output_dir) / f"n{n}"
    odir.mkdir(parents=True, exist_ok=True)
    return {
        'out_dir':   str(odir),                     # <- 추가
        'all_vec_csv': str(odir / "all_vectors.csv"),
        'all_sca_csv': str(odir / "all_scalars.csv"),
        'thr_csv':     str(odir / "throughput.csv"),
        'cw_csv':      str(odir / "cw_data.csv"),
        'retry_csv':   str(odir / "retry_counts.csv"),
        'thr_bps_csv': str(odir / "throughput_bps.csv"),
    }
def update_eta_summary_csv(csv_path: str, n: int, metrics: dict, thr_df=None):
    """
    summary_eta_by_n.csv 파일에 한 줄을 (n 기준) 추가/갱신한다.
    - 기존 파일에 eta_rate 열이 없어도 자동으로 추가한다.
    - 같은 n 값이 이미 있으면 최신 값으로 덮어쓴다.
    """
    # 1) 값 추출
    eta_time = metrics.get('eta', float('nan'))
    eta_rate = metrics.get('eta_rate', float('nan'))
    succ_pkts = metrics.get('succ_pkts', float('nan'))
    tx_attempts = metrics.get('tx_attempts', float('nan'))
    collisions = metrics.get('collisions', float('nan'))
    P_S = metrics.get('P_S', float('nan'))
    P_I = metrics.get('P_I', float('nan'))
    P_C = metrics.get('P_C', float('nan'))
    T_S = metrics.get('T_S', float('nan'))
    T_I = metrics.get('T_I', float('nan'))
    T_C = metrics.get('T_C', float('nan'))

    # thr_df에 avg_bps가 있으면 가져옴(없으면 NaN)
    avg_bps = float('nan')
    if thr_df is not None and not getattr(thr_df, 'empty', True) and 'avg_bps' in thr_df.columns:
        avg_bps = float(thr_df['avg_bps'].mean())

    # 2) 현재 행(dict)
    row = {
        'n': n,
        'eta': eta_time,         # 기존 time-efficiency
        'eta_rate': eta_rate,    # (신규) rate-efficiency
        'avg_bps': avg_bps,
        'tx_attempts': tx_attempts,
        'succ_pkts': succ_pkts,
        'collisions': collisions,
        'P_S': P_S, 'P_I': P_I, 'P_C': P_C,
        'T_S_us': T_S * 1e6 if isinstance(T_S, (int, float)) else T_S,
        'T_I_us': T_I * 1e6 if isinstance(T_I, (int, float)) else T_I,
        'T_C_us': T_C * 1e6 if isinstance(T_C, (int, float)) else T_C,
    }

    # 3) 기존 CSV 읽기 (없으면 빈 DF 생성)
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # 열이 없으면 추가
        for k in row.keys():
            if k not in df.columns:
                df[k] = pd.NA
    else:
        df = pd.DataFrame(columns=list(row.keys()))

    # 4) 같은 n이 있으면 덮어쓰기, 없으면 추가
    if (df.shape[0] > 0) and ('n' in df.columns) and (df['n'] == n).any():
        df.loc[df['n'] == n, list(row.keys())] = pd.Series(row)
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # 5) n 기준 정렬 후 저장
    if 'n' in df.columns:
        try:
            df = df.sort_values('n').reset_index(drop=True)
        except Exception:
            pass

    df.to_csv(csv_path, index=False)

def main():
    summary_rows = []   # n별 요약 행
    eta_rows = []   # n별 MAC 효율 비교용 누적

    print("--- OMNeT++ 결과 데이터 후처리 시작 ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 결과 저장: {OUTPUT_DIR}\n")

    # 1) n 값별 run 수집 (없으면 기존 방식 fallback)
    runs = collect_runs_by_n(RESULTS_DIR, conf_prefix="Paper_Baseline")

    if not runs:
        # 기존 동작: 한 세트만 처리
        vec_files, sca_files = ensure_files()
        all_vec_csv = os.path.join(OUTPUT_DIR, 'all_vectors.csv')
        all_sca_csv = os.path.join(OUTPUT_DIR, 'all_scalars.csv')
        dump_all(vec_files, sca_files, all_vec_csv, all_sca_csv)

        # 필터링
        thr_csv = os.path.join(OUTPUT_DIR, 'throughput.csv')
        cw_csv = os.path.join(OUTPUT_DIR, 'cw_data.csv')
        retry_csv = os.path.join(OUTPUT_DIR, 'retry_counts.csv')
        filter_vectors(all_vec_csv, thr_csv, THR_NAME_KEYS, THR_MODULE_KEYS)
        filter_vectors(all_vec_csv, cw_csv, CW_NAME_KEYS, [])
        filter_rows(all_sca_csv, retry_csv, name_exact=RETRY_NAMES)

        # 스루풋 계산
        thr_bps_csv = os.path.join(OUTPUT_DIR, 'throughput_bps.csv')
        compute_avg_bps(thr_csv, thr_bps_csv)

        # 요약(기존 출력 루틴 유지)
        retry_with = sum_scalar(all_sca_csv, 'packetSentToPeerWithRetry:count')
        retry_without = sum_scalar(all_sca_csv, 'packetSentToPeerWithoutRetry:count')
        total_retry_frames = int((retry_with or 0) + (retry_without or 0))
        print(f"🔁 재시도 프레임: {int(retry_with or 0)}/{total_retry_frames}  ({(retry_with or 0)/(total_retry_frames or 1)*100:.2f}%)")
        print("✅ 완료")
        return

    # 2) n별 처리
    summary_rows = []
    for n, files in sorted(runs.items()):
        print(f"\n=== n={n} 처리 시작 ===")
        out = make_outputs_for_n(OUTPUT_DIR, n)

        vec_files = files.get('vec', [])
        sca_files = files.get('sca', [])
        if not vec_files or not sca_files:
            print(f"⚠️  n={n}: vec/sca 파일이 부족합니다. 건너뜀.")
            continue

        # 덤프
        dump_all(vec_files, sca_files, out['all_vec_csv'], out['all_sca_csv'])

        # 필터
        filter_vectors(out['all_vec_csv'], out['thr_csv'], THR_NAME_KEYS, THR_MODULE_KEYS)
        filter_vectors(out['all_vec_csv'], out['cw_csv'], CW_NAME_KEYS, [])
        filter_rows(out['all_sca_csv'], out['retry_csv'], name_exact=RETRY_NAMES)

        # 스루풋 계산
        thr_df = compute_avg_bps(out['thr_csv'], out['thr_bps_csv'])

        # 재시도/드롭 등 요약(스칼라에서)
        retry_with = sum_scalar(out['all_sca_csv'], 'packetSentToPeerWithRetry:count')
        retry_without = sum_scalar(out['all_sca_csv'], 'packetSentToPeerWithoutRetry:count')
        retry_limit = sum_scalar(out['all_sca_csv'], 'retryLimitReached:count')  # 없으면 0 반환 처리됨
        total_tx = sum_scalar(out['all_sca_csv'], 'packetSentToPeer:count') or 0

        # succ_bytes는 기존 로직/레코더에 따라 다르므로, 없으면 0
        succ_bytes = sum_scalar(out['all_sca_csv'], 'rcvdPk:sum(packetBytes)') or 0
        succ_bits = 8 * succ_bytes

        # 간단 요약 행
        summary_rows.append({
            'n': n,
            'avg_bps_from_vectors': float(thr_df['avg_bps'].mean()) if thr_df is not None and not thr_df.empty else 0.0,
            'retry_with': int(retry_with or 0),
            'retry_without': int(retry_without or 0),
            'retry_limit_drops': int(retry_limit or 0),
            'total_tx_frames': int(total_tx or 0),
            'succ_bytes': int(succ_bytes),
            'succ_bits': int(succ_bits),
        })

        # ----- η 계산(논문 식(4)) + 요약 텍스트 저장 -----
        avg_bps_mean = float(thr_df['avg_bps'].mean()) if thr_df is not None and not thr_df.empty else 0.0

        # mac_metrics = compute_mac_efficiency_from_results(
        #     out['all_sca_csv'],
        #     thr_df,
        #     sim_time_sec=5.0,
        #     phy_rate_bps=12_000_000,   # Baseline 12 Mbps
        #     slot_time=9e-6,
        #     rifs=2e-6,
        #     cifs=34e-6,
        #     ack_time=44e-6,
        #     pkt_bytes=1500,
        #     verbose=True
        # )
        sim_time_sec = 5.0
        if thr_df is not None and not thr_df.empty and 'duration' in thr_df.columns:
            sim_time_sec = float(thr_df['duration'].max())

        mac_metrics = compute_mac_efficiency_from_results(
            out['all_sca_csv'],
            thr_df,
            sim_time_sec=sim_time_sec,   # ← 측정값 사용
            phy_rate_bps=12_000_000,
            slot_time=9e-6,
            rifs=2e-6,
            cifs=34e-6,
            ack_time=44e-6,
            pkt_bytes=1500,
            verbose=True
        )

        # n 전용 요약 텍스트
        summary_txt_dir = out.get('out_dir') or str(Path(out['all_sca_csv']).parent)
        summary_txt_path = os.path.join(summary_txt_dir, 'packet_loss_summary.txt')
        write_packet_loss_summary_txt(
            summary_txt_path, n, mac_metrics,
            extra={
                'avg_bps': avg_bps_mean,
                'retry_with': int(retry_with or 0),
                'retry_without': int(retry_without or 0)
            }
        )
        print(f"📝 packet_loss_summary.txt 저장: {summary_txt_path}")

        print(f"η_time≈{mac_metrics.get('eta',0):.3f}, η_rate≈{mac_metrics.get('eta_rate',0):.3f}")


        # 전체 비교 CSV에 η/확률도 포함하도록 별도 리스트에 추가
        # (main() 맨 위에 eta_rows = [] 선언 필요)
        eta_rows.append({
            'n': n,
            'eta': mac_metrics.get('eta', 0.0),
            'eta_rate': mac_metrics.get('eta_rate', float('nan')),  # ← 추가
            'P_S': mac_metrics.get('P_S', 0.0),
            'P_I': mac_metrics.get('P_I', 0.0),
            'P_C': mac_metrics.get('P_C', 0.0),
            'avg_bps': avg_bps_mean,
            'tx_attempts': mac_metrics.get('tx_attempts', 0),
            'succ_pkts': mac_metrics.get('succ_pkts', 0),
            'collisions': mac_metrics.get('collisions', 0),
            'retry_with': int(retry_with or 0),
            'retry_without': int(retry_without or 0),
            'retry_limit_drops': int(retry_limit or 0)
        })

        print(f"=== n={n} 처리 완료 ===")

    # 3) n별 요약 CSV 저장
    if summary_rows:
        import pandas as pd
        summary_df = pd.DataFrame(summary_rows).sort_values('n')
        summary_path = os.path.join(OUTPUT_DIR, "summary_by_n.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\n📊 n별 요약 저장: {summary_path}")

        # 4) n별 MAC 효율 비교 CSV 저장
    if eta_rows:
        import pandas as pd
        eta_df = pd.DataFrame(eta_rows).sort_values('n')
        eta_csv_path = os.path.join(OUTPUT_DIR, "summary_eta_by_n.csv")
        eta_df.to_csv(eta_csv_path, index=False)
        print(f"📊 n별 MAC 효율 요약 저장: {eta_csv_path}")

    print("✅ 완료")



if __name__ == "__main__":
    main()
