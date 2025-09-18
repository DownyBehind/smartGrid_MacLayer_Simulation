#!/usr/bin/env python3
"""
노드 5개 실험 결과 분석 스크립트
- 데드라인 미스 4종류 분석
- MAC 경쟁 지연 반영 검증
- HPGP MAC 표준 준수 검증
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import re

def load_dc_jobs_data(filepath):
    """DC 잡 데이터 로드"""
    columns = [
        'nodeId', 'jobId', 'releaseTime', 'windowStart', 'windowEnd', 'deadline',
        'state', 'seq', 'reqTime', 'resTime', 'enq_req', 'txStart_req', 'txEnd_req',
        'enq_rsp', 'rxStart_rsp', 'rxEnd_rsp', 'event'
    ]
    
    df = pd.read_csv(filepath, names=columns)
    return df

def load_dc_misses_data(filepath):
    """DC 미스 데이터 로드"""
    columns = [
        'nodeId', 'jobId', 'releaseTime', 'windowStart', 'windowEnd', 'deadline',
        'state', 'seq', 'reqTime', 'resTime', 'enq_req', 'txStart_req', 'txEnd_req',
        'enq_rsp', 'rxStart_rsp', 'rxEnd_rsp'
    ]
    
    df = pd.read_csv(filepath, names=columns)
    return df

def load_mac_tx_data(filepath):
    """MAC 전송 데이터 로드"""
    df = pd.read_csv(filepath, names=['time', 'nodeId', 'msgType', 'seq', 'success', 'collision'])
    return df

def load_slac_data(filepath):
    """SLAC 데이터 로드"""
    df = pd.read_csv(filepath, names=['time', 'nodeId', 'msgType', 'success', 'retries'])
    return df

def analyze_deadline_misses(dc_jobs_df, dc_misses_df):
    """데드라인 미스 4종류 분석"""
    print("=== 데드라인 미스 4종류 분석 ===")
    
    # 잡 상태별 분류
    total_jobs = len(dc_jobs_df)
    completed_jobs = len(dc_jobs_df[dc_jobs_df['state'] == 2])  # RES_RECEIVED
    missed_jobs = len(dc_misses_df)
    
    print(f"총 잡 수: {total_jobs}")
    print(f"완료된 잡 수: {completed_jobs}")
    print(f"미스된 잡 수: {missed_jobs}")
    print(f"성공률: {completed_jobs/total_jobs*100:.2f}%")
    print(f"미스률: {missed_jobs/total_jobs*100:.2f}%")
    
    # 미스 유형별 분석 (상태 코드 기반)
    miss_types = {
        0: "M0: NO-REQ (요청 전송 안됨)",
        1: "M1: REQ-FAIL (요청 전송 실패)", 
        2: "M2: RES-MISS (응답 미수신)",
        3: "M3: RES-LATE (응답 지연)"
    }
    
    print("\n미스 유형별 분포:")
    for state, description in miss_types.items():
        count = len(dc_misses_df[dc_misses_df['state'] == state])
        percentage = count / missed_jobs * 100 if missed_jobs > 0 else 0
        print(f"  {description}: {count}개 ({percentage:.2f}%)")
    
    return {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'missed_jobs': missed_jobs,
        'success_rate': completed_jobs/total_jobs*100,
        'miss_rate': missed_jobs/total_jobs*100,
        'miss_types': {state: len(dc_misses_df[dc_misses_df['state'] == state]) for state in miss_types.keys()}
    }

def analyze_mac_contention_delay(dc_jobs_df, mac_tx_df):
    """MAC 경쟁 지연 분석"""
    print("\n=== MAC 경쟁 지연 분석 ===")
    
    # RTT 계산 (txEnd_req가 있는 경우만)
    valid_rtt_jobs = dc_jobs_df[
        (dc_jobs_df['txEnd_req'] > 0) & 
        (dc_jobs_df['rxEnd_rsp'] > 0) & 
        (dc_jobs_df['state'] == 2)
    ].copy()
    
    if len(valid_rtt_jobs) > 0:
        valid_rtt_jobs['rtt'] = valid_rtt_jobs['rxEnd_rsp'] - valid_rtt_jobs['txEnd_req']
        
        print(f"유효한 RTT 측정 잡 수: {len(valid_rtt_jobs)}")
        print(f"평균 RTT: {valid_rtt_jobs['rtt'].mean()*1000:.3f} ms")
        print(f"최대 RTT: {valid_rtt_jobs['rtt'].max()*1000:.3f} ms")
        print(f"최소 RTT: {valid_rtt_jobs['rtt'].min()*1000:.3f} ms")
        print(f"RTT 표준편차: {valid_rtt_jobs['rtt'].std()*1000:.3f} ms")
        
        # RTT 분포
        rtt_percentiles = valid_rtt_jobs['rtt'].quantile([0.5, 0.9, 0.95, 0.99])
        print(f"\nRTT 백분위수:")
        for p, value in rtt_percentiles.items():
            print(f"  P{int(p*100)}: {value*1000:.3f} ms")
    else:
        print("유효한 RTT 측정 데이터가 없습니다.")
    
    # MAC 전송 통계
    total_tx = len(mac_tx_df)
    successful_tx = len(mac_tx_df[mac_tx_df['success'] == 1])
    collision_tx = len(mac_tx_df[mac_tx_df['collision'] == 1])
    
    print(f"\nMAC 전송 통계:")
    print(f"  총 전송 시도: {total_tx}")
    print(f"  성공한 전송: {successful_tx} ({successful_tx/total_tx*100:.2f}%)")
    print(f"  충돌 발생: {collision_tx} ({collision_tx/total_tx*100:.2f}%)")
    
    return {
        'valid_rtt_count': len(valid_rtt_jobs),
        'avg_rtt': valid_rtt_jobs['rtt'].mean() if len(valid_rtt_jobs) > 0 else 0,
        'max_rtt': valid_rtt_jobs['rtt'].max() if len(valid_rtt_jobs) > 0 else 0,
        'min_rtt': valid_rtt_jobs['rtt'].min() if len(valid_rtt_jobs) > 0 else 0,
        'rtt_std': valid_rtt_jobs['rtt'].std() if len(valid_rtt_jobs) > 0 else 0,
        'total_tx': total_tx,
        'successful_tx': successful_tx,
        'collision_tx': collision_tx
    }

def analyze_hpgp_mac_compliance(dc_jobs_df, slac_df):
    """HPGP MAC 표준 준수 분석"""
    print("\n=== HPGP MAC 표준 준수 분석 ===")
    
    # DC 명령 주기 분석
    dc_jobs = dc_jobs_df[dc_jobs_df['event'] == 'DC_RELEASE'].copy()
    if len(dc_jobs) > 1:
        dc_jobs = dc_jobs.sort_values('releaseTime')
        dc_jobs['period'] = dc_jobs['releaseTime'].diff()
        actual_periods = dc_jobs['period'].dropna()
        
        print(f"DC 명령 주기 분석:")
        print(f"  평균 주기: {actual_periods.mean()*1000:.3f} ms")
        print(f"  표준 주기: 100.000 ms")
        print(f"  주기 편차: {abs(actual_periods.mean() - 0.1)*1000:.3f} ms")
        
        # 주기 준수율 (100ms ± 5ms 범위)
        period_compliance = len(actual_periods[(actual_periods >= 0.095) & (actual_periods <= 0.105)])
        period_compliance_rate = period_compliance / len(actual_periods) * 100
        print(f"  주기 준수율 (±5ms): {period_compliance_rate:.2f}%")
    
    # SLAC 성공률 분석
    total_slac = len(slac_df)
    successful_slac = len(slac_df[slac_df['success'] == 1])
    slac_success_rate = successful_slac / total_slac * 100 if total_slac > 0 else 0
    
    print(f"\nSLAC 성공률:")
    print(f"  총 SLAC 시도: {total_slac}")
    print(f"  성공한 SLAC: {successful_slac}")
    print(f"  SLAC 성공률: {slac_success_rate:.2f}%")
    
    # 노드별 성능 분석
    print(f"\n노드별 성능:")
    for node_id in sorted(dc_jobs_df['nodeId'].unique()):
        node_jobs = dc_jobs_df[dc_jobs_df['nodeId'] == node_id]
        node_completed = len(node_jobs[node_jobs['state'] == 2])
        node_total = len(node_jobs[node_jobs['event'] == 'DC_RELEASE'])
        node_success_rate = node_completed / node_total * 100 if node_total > 0 else 0
        print(f"  노드 {node_id}: {node_completed}/{node_total} ({node_success_rate:.2f}%)")
    
    return {
        'avg_period': actual_periods.mean() if len(dc_jobs) > 1 else 0,
        'period_compliance_rate': period_compliance_rate if len(dc_jobs) > 1 else 0,
        'slac_success_rate': slac_success_rate,
        'node_performance': {node_id: len(dc_jobs_df[(dc_jobs_df['nodeId'] == node_id) & (dc_jobs_df['state'] == 2)]) / 
                            len(dc_jobs_df[(dc_jobs_df['nodeId'] == node_id) & (dc_jobs_df['event'] == 'DC_RELEASE')]) * 100
                            for node_id in sorted(dc_jobs_df['nodeId'].unique())}
    }

def create_analysis_plots(dc_jobs_df, dc_misses_df, mac_tx_df, slac_df):
    """분석 결과 시각화"""
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('노드 5개 실험 결과 분석', fontsize=16, fontweight='bold')
    
    # 1. 데드라인 미스 유형 분포
    miss_types = {0: "M0: NO-REQ", 1: "M1: REQ-FAIL", 2: "M2: RES-MISS", 3: "M3: RES-LATE"}
    miss_counts = [len(dc_misses_df[dc_misses_df['state'] == state]) for state in miss_types.keys()]
    miss_labels = list(miss_types.values())
    
    axes[0, 0].pie(miss_counts, labels=miss_labels, autopct='%1.1f%%', startangle=90)
    axes[0, 0].set_title('데드라인 미스 유형 분포')
    
    # 2. RTT 분포
    valid_rtt_jobs = dc_jobs_df[
        (dc_jobs_df['txEnd_req'] > 0) & 
        (dc_jobs_df['rxEnd_rsp'] > 0) & 
        (dc_jobs_df['state'] == 2)
    ].copy()
    if len(valid_rtt_jobs) > 0:
        valid_rtt_jobs['rtt'] = valid_rtt_jobs['rxEnd_rsp'] - valid_rtt_jobs['txEnd_req']
        axes[0, 1].hist(valid_rtt_jobs['rtt'] * 1000, bins=50, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('RTT 분포')
        axes[0, 1].set_xlabel('RTT (ms)')
        axes[0, 1].set_ylabel('빈도')
        axes[0, 1].axvline(valid_rtt_jobs['rtt'].mean() * 1000, color='red', linestyle='--', label=f'평균: {valid_rtt_jobs["rtt"].mean()*1000:.3f}ms')
        axes[0, 1].legend()
    
    # 3. 노드별 성공률
    node_success_rates = []
    node_ids = sorted(dc_jobs_df['nodeId'].unique())
    for node_id in node_ids:
        node_jobs = dc_jobs_df[dc_jobs_df['nodeId'] == node_id]
        node_completed = len(node_jobs[node_jobs['state'] == 2])
        node_total = len(node_jobs[node_jobs['event'] == 'DC_RELEASE'])
        success_rate = node_completed / node_total * 100 if node_total > 0 else 0
        node_success_rates.append(success_rate)
    
    axes[0, 2].bar(node_ids, node_success_rates, alpha=0.7, edgecolor='black')
    axes[0, 2].set_title('노드별 DC 명령 성공률')
    axes[0, 2].set_xlabel('노드 ID')
    axes[0, 2].set_ylabel('성공률 (%)')
    axes[0, 2].set_ylim(0, 100)
    
    # 4. 시간별 DC 명령 처리량
    dc_releases = dc_jobs_df[dc_jobs_df['event'] == 'DC_RELEASE'].copy()
    dc_releases['time_bin'] = (dc_releases['releaseTime'] // 10) * 10  # 10초 단위
    throughput = dc_releases.groupby('time_bin').size()
    
    axes[1, 0].plot(throughput.index, throughput.values, marker='o', linewidth=2)
    axes[1, 0].set_title('시간별 DC 명령 처리량 (10초 단위)')
    axes[1, 0].set_xlabel('시간 (초)')
    axes[1, 0].set_ylabel('처리량')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. MAC 충돌률 시간별 변화
    mac_tx_df['time_bin'] = (mac_tx_df['time'] // 10) * 10
    collision_rate = mac_tx_df.groupby('time_bin').apply(lambda x: x['collision'].sum() / len(x) * 100)
    
    axes[1, 1].plot(collision_rate.index, collision_rate.values, marker='s', color='red', linewidth=2)
    axes[1, 1].set_title('시간별 MAC 충돌률 (10초 단위)')
    axes[1, 1].set_xlabel('시간 (초)')
    axes[1, 1].set_ylabel('충돌률 (%)')
    axes[1, 1].grid(True, alpha=0.3)
    
    # 6. SLAC 성공률
    slac_success = len(slac_df[slac_df['success'] == 1])
    slac_failure = len(slac_df[slac_df['success'] == 0])
    
    axes[1, 2].pie([slac_success, slac_failure], labels=['성공', '실패'], autopct='%1.1f%%', 
                   colors=['lightgreen', 'lightcoral'], startangle=90)
    axes[1, 2].set_title(f'SLAC 성공률\n(총 {len(slac_df)}개 시도)')
    
    plt.tight_layout()
    plt.savefig('results/node5_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """메인 분석 함수"""
    print("노드 5개 실험 결과 분석을 시작합니다...")
    
    # 데이터 로드
    dc_jobs_df = load_dc_jobs_data('results/dc_jobs.log')
    dc_misses_df = load_dc_misses_data('results/dc_misses.log')
    mac_tx_df = load_mac_tx_data('results/mac_tx.log')
    slac_df = load_slac_data('results/slac_attempt.log')
    
    print(f"데이터 로드 완료:")
    print(f"  DC 잡: {len(dc_jobs_df):,}개")
    print(f"  DC 미스: {len(dc_misses_df):,}개")
    print(f"  MAC 전송: {len(mac_tx_df):,}개")
    print(f"  SLAC 시도: {len(slac_df):,}개")
    
    # 분석 수행
    miss_analysis = analyze_deadline_misses(dc_jobs_df, dc_misses_df)
    mac_analysis = analyze_mac_contention_delay(dc_jobs_df, mac_tx_df)
    hpgp_analysis = analyze_hpgp_mac_compliance(dc_jobs_df, slac_df)
    
    # 시각화
    create_analysis_plots(dc_jobs_df, dc_misses_df, mac_tx_df, slac_df)
    
    # 종합 요약
    print("\n" + "="*50)
    print("종합 분석 요약")
    print("="*50)
    print(f"1. 데드라인 미스 분석:")
    print(f"   - 전체 성공률: {miss_analysis['success_rate']:.2f}%")
    print(f"   - 미스률: {miss_analysis['miss_rate']:.2f}%")
    print(f"   - 주요 미스 유형: M{max(miss_analysis['miss_types'], key=miss_analysis['miss_types'].get)}")
    
    print(f"\n2. MAC 경쟁 지연 분석:")
    print(f"   - 평균 RTT: {mac_analysis['avg_rtt']*1000:.3f} ms")
    print(f"   - MAC 충돌률: {mac_analysis['collision_tx']/mac_analysis['total_tx']*100:.2f}%")
    
    print(f"\n3. HPGP MAC 표준 준수:")
    print(f"   - DC 주기 준수율: {hpgp_analysis['period_compliance_rate']:.2f}%")
    print(f"   - SLAC 성공률: {hpgp_analysis['slac_success_rate']:.2f}%")
    
    print(f"\n분석 완료! 결과 그래프가 'results/node5_analysis.png'에 저장되었습니다.")

if __name__ == "__main__":
    main()

