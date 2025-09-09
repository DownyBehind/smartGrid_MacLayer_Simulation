#!/usr/bin/env python3
"""
SLAC 메시지 분석 및 시각화 스크립트
OMNeT++ 시뮬레이션 결과를 분석하여 SLAC 메시지의 시간별 그래프를 생성합니다.
"""

import matplotlib.pyplot as plt
import numpy as np
import re
from datetime import datetime
import os

def parse_simulation_log(log_file):
    """시뮬레이션 로그 파일을 파싱하여 SLAC 메시지 정보를 추출합니다."""
    slac_messages = []
    
    if not os.path.exists(log_file):
        print(f"로그 파일을 찾을 수 없습니다: {log_file}")
        return slac_messages
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # SLAC 메시지 패턴 찾기
    # 예: [0.001] Node 0 (EVSE): Sending SLAC message type 0 (bits: 2400)
    pattern = r'\[([\d.]+)\]\s+Node\s+(\d+)\s+\((\w+)\):\s+Sending\s+SLAC\s+message\s+type\s+(\d+)\s+\(bits:\s+(\d+)\)'
    
    matches = re.findall(pattern, content)
    
    for match in matches:
        time = float(match[0])
        node_id = int(match[1])
        node_type = match[2]
        message_type = int(match[3])
        bits = int(match[4])
        
        slac_messages.append({
            'time': time,
            'node_id': node_id,
            'node_type': node_type,
            'message_type': message_type,
            'bits': bits
        })
    
    return slac_messages

def create_slac_timeline_graph(slac_messages, output_file='slac_timeline.png'):
    """SLAC 메시지의 시간별 그래프를 생성합니다."""
    
    if not slac_messages:
        print("SLAC 메시지가 없습니다. 시뮬레이션 로그를 확인해주세요.")
        return
    
    # 그래프 설정
    plt.figure(figsize=(15, 10))
    
    # 노드별로 색상 설정
    node_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    # 메시지 타입별로 마커 설정
    message_markers = ['o', 's', '^', 'v', 'D', 'h', 'p', '*']
    
    # 노드별로 그룹화
    nodes = {}
    for msg in slac_messages:
        node_id = msg['node_id']
        if node_id not in nodes:
            nodes[node_id] = []
        nodes[node_id].append(msg)
    
    # 각 노드별로 플롯
    for node_id, messages in nodes.items():
        times = [msg['time'] for msg in messages]
        message_types = [msg['message_type'] for msg in messages]
        node_type = messages[0]['node_type']
        
        color = node_colors[node_id % len(node_colors)]
        
        # 메시지 타입별로 다른 마커 사용
        for i, (time, msg_type) in enumerate(zip(times, message_types)):
            marker = message_markers[msg_type % len(message_markers)]
            plt.scatter(time, node_id, c=color, marker=marker, s=100, alpha=0.7)
            
            # 메시지 타입 라벨 추가
            plt.annotate(f'T{msg_type}', (time, node_id), 
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8)
    
    # 그래프 설정
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Node ID', fontsize=12)
    plt.title('SLAC Message Timeline\n(Red=EVSE, Blue/Green/Orange/Purple=EVs)', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Y축 설정
    if nodes:
        plt.yticks(range(max(nodes.keys()) + 1))
    
    # 범례 추가
    legend_elements = []
    for node_id, messages in nodes.items():
        node_type = messages[0]['node_type']
        color = node_colors[node_id % len(node_colors)]
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor=color, markersize=10,
                                        label=f'Node {node_id} ({node_type})'))
    
    plt.legend(handles=legend_elements, loc='upper right')
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 파일 저장
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"SLAC 타임라인 그래프가 저장되었습니다: {output_file}")
    
    # 그래프 표시
    plt.show()

def create_message_type_distribution(slac_messages, output_file='slac_message_types.png'):
    """SLAC 메시지 타입별 분포 그래프를 생성합니다."""
    
    if not slac_messages:
        print("SLAC 메시지가 없습니다.")
        return
    
    # 메시지 타입별 카운트
    message_type_counts = {}
    for msg in slac_messages:
        msg_type = msg['message_type']
        if msg_type not in message_type_counts:
            message_type_counts[msg_type] = 0
        message_type_counts[msg_type] += 1
    
    # 그래프 생성
    plt.figure(figsize=(12, 6))
    
    types = list(message_type_counts.keys())
    counts = list(message_type_counts.values())
    
    plt.bar(types, counts, color='skyblue', alpha=0.7)
    plt.xlabel('SLAC Message Type', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.title('SLAC Message Type Distribution', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # 각 막대 위에 값 표시
    for i, count in enumerate(counts):
        plt.text(types[i], count + 0.1, str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"SLAC 메시지 타입 분포 그래프가 저장되었습니다: {output_file}")
    plt.show()

def main():
    """메인 함수"""
    print("SLAC 메시지 분석 시작...")
    
    # 로그 파일 경로
    log_file = 'results/detailed_simulation.log'
    
    # SLAC 메시지 파싱
    slac_messages = parse_simulation_log(log_file)
    
    print(f"발견된 SLAC 메시지 수: {len(slac_messages)}")
    
    if slac_messages:
        # 시간별 그래프 생성
        create_slac_timeline_graph(slac_messages)
        
        # 메시지 타입별 분포 그래프 생성
        create_message_type_distribution(slac_messages)
        
        # 통계 정보 출력
        print("\n=== SLAC 메시지 통계 ===")
        print(f"총 메시지 수: {len(slac_messages)}")
        
        # 노드별 통계
        node_stats = {}
        for msg in slac_messages:
            node_id = msg['node_id']
            if node_id not in node_stats:
                node_stats[node_id] = {'count': 0, 'node_type': msg['node_type']}
            node_stats[node_id]['count'] += 1
        
        for node_id, stats in node_stats.items():
            print(f"Node {node_id} ({stats['node_type']}): {stats['count']} messages")
        
        # 시간 범위
        times = [msg['time'] for msg in slac_messages]
        print(f"시간 범위: {min(times):.3f}s ~ {max(times):.3f}s")
        
    else:
        print("SLAC 메시지를 찾을 수 없습니다.")
        print("시뮬레이션 로그에서 SLAC 메시지가 제대로 출력되지 않았을 수 있습니다.")
        print("로그 파일을 확인해보세요:", log_file)

if __name__ == "__main__":
    main()
