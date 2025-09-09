#!/usr/bin/env python3
"""
SLAC 메시지 시각화 스크립트
실제 시뮬레이션 로그를 분석하여 SLAC 메시지의 시간별 그래프를 생성합니다.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def parse_slac_log(log_file):
    """SLAC 메시지 로그 파일을 파싱합니다."""
    if not os.path.exists(log_file):
        print(f"로그 파일을 찾을 수 없습니다: {log_file}")
        return None
    
    data = []
    with open(log_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                time = float(parts[0])
                node_info = parts[1]  # Node_1_EV
                msg_type = int(parts[2].split('_')[-1])  # SLAC_MSG_TYPE_1 -> 1
                bits = int(parts[3])
                
                # 노드 정보 파싱
                node_parts = node_info.split('_')
                node_id = int(node_parts[1])
                node_type = node_parts[2]
                
                data.append({
                    'time': time,
                    'node_id': node_id,
                    'node_type': node_type,
                    'message_type': msg_type,
                    'bits': bits
                })
    
    return pd.DataFrame(data)

def create_slac_timeline(df, output_file='slac_timeline.png'):
    """SLAC 메시지 타임라인 그래프를 생성합니다."""
    if df is None or df.empty:
        print("데이터가 없습니다.")
        return
    
    plt.figure(figsize=(15, 8))
    
    # 노드별 색상 설정
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    # 노드별로 그룹화
    for node_id in df['node_id'].unique():
        node_data = df[df['node_id'] == node_id]
        node_type = node_data['node_type'].iloc[0]
        color = colors[node_id % len(colors)]
        
        # 메시지 타입별로 다른 마커 사용
        for msg_type in node_data['message_type'].unique():
            msg_data = node_data[node_data['message_type'] == msg_type]
            
            marker = 'o' if msg_type == 1 else 's'
            label = f'Node {node_id} ({node_type}) - Type {msg_type}'
            
            plt.scatter(msg_data['time'], msg_data['node_id'], 
                       c=color, marker=marker, s=100, alpha=0.7, label=label)
            
            # 메시지 타입 라벨 추가
            for _, row in msg_data.iterrows():
                plt.annotate(f'T{msg_type}', (row['time'], row['node_id']), 
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, alpha=0.8)
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Node ID', fontsize=12)
    plt.title('SLAC Message Timeline', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Y축 설정
    if not df.empty:
        plt.yticks(range(int(df['node_id'].min()), int(df['node_id'].max()) + 1))
    
    # 범례 (중복 제거)
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"SLAC 타임라인 그래프가 저장되었습니다: {output_file}")
    plt.show()

def create_message_frequency_plot(df, output_file='slac_frequency.png'):
    """SLAC 메시지 빈도 그래프를 생성합니다."""
    if df is None or df.empty:
        print("데이터가 없습니다.")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. 노드별 메시지 수
    node_counts = df['node_id'].value_counts().sort_index()
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    bars1 = ax1.bar(node_counts.index, node_counts.values, 
                    color=[colors[i % len(colors)] for i in node_counts.index], alpha=0.7)
    ax1.set_xlabel('Node ID', fontsize=12)
    ax1.set_ylabel('Message Count', fontsize=12)
    ax1.set_title('SLAC Messages per Node', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # 막대 위에 값 표시
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    # 2. 메시지 타입별 분포
    msg_type_counts = df['message_type'].value_counts().sort_index()
    bars2 = ax2.bar(msg_type_counts.index, msg_type_counts.values, 
                    color='skyblue', alpha=0.7)
    ax2.set_xlabel('Message Type', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('SLAC Messages by Type', fontsize=14)
    ax2.grid(True, alpha=0.3)
    
    # 막대 위에 값 표시
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"SLAC 빈도 그래프가 저장되었습니다: {output_file}")
    plt.show()

def create_time_series_plot(df, output_file='slac_timeseries.png'):
    """SLAC 메시지 시간 시리즈 그래프를 생성합니다."""
    if df is None or df.empty:
        print("데이터가 없습니다.")
        return
    
    plt.figure(figsize=(15, 6))
    
    # 시간별 메시지 수 계산
    time_bins = np.linspace(df['time'].min(), df['time'].max(), 20)
    message_counts = []
    
    for i in range(len(time_bins) - 1):
        count = len(df[(df['time'] >= time_bins[i]) & (df['time'] < time_bins[i + 1])])
        message_counts.append(count)
    
    # 시간 구간의 중점 계산
    time_centers = [(time_bins[i] + time_bins[i + 1]) / 2 for i in range(len(time_bins) - 1)]
    
    plt.plot(time_centers, message_counts, marker='o', linewidth=2, markersize=6)
    plt.fill_between(time_centers, message_counts, alpha=0.3)
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Message Count', fontsize=12)
    plt.title('SLAC Message Frequency Over Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"SLAC 시간 시리즈 그래프가 저장되었습니다: {output_file}")
    plt.show()

def main():
    """메인 함수"""
    print("SLAC 메시지 시각화 시작...")
    
    # 로그 파일 경로
    log_file = 'results/slac_messages.log'
    
    # 데이터 파싱
    df = parse_slac_log(log_file)
    
    if df is not None and not df.empty:
        print(f"파싱된 SLAC 메시지 수: {len(df)}")
        print(f"노드 수: {df['node_id'].nunique()}")
        print(f"메시지 타입 수: {df['message_type'].nunique()}")
        print(f"시간 범위: {df['time'].min():.3f}s ~ {df['time'].max():.3f}s")
        
        # 그래프 생성
        create_slac_timeline(df)
        create_message_frequency_plot(df)
        create_time_series_plot(df)
        
        # 상세 통계 출력
        print("\n=== 상세 통계 ===")
        print(df.groupby(['node_id', 'node_type', 'message_type']).size().reset_index(name='count'))
        
    else:
        print("SLAC 메시지 데이터를 찾을 수 없습니다.")
        print("시뮬레이션을 실행하여 로그 파일을 생성해주세요.")

if __name__ == "__main__":
    main()
