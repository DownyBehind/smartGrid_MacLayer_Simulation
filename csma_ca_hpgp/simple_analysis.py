#!/usr/bin/env python3
"""
간단한 OMNeT++ 결과 분석 스크립트
"""

import matplotlib.pyplot as plt
import re
import os

def analyze_sca_file():
    """SCA 파일을 분석하여 기본 통계를 출력합니다."""
    sca_file = 'results/General-#0.sca'
    
    if not os.path.exists(sca_file):
        print(f"SCA 파일을 찾을 수 없습니다: {sca_file}")
        return
    
    with open(sca_file, 'r') as f:
        content = f.read()
    
    # Scalar 데이터 추출
    scalar_pattern = r'scalar\s+([^\s]+)\s+([^\s]+)\s+(.+)'
    scalars = re.findall(scalar_pattern, content)
    
    print("=== 시뮬레이션 통계 ===")
    for module, name, value in scalars:
        print(f"{module}.{name}: {value}")
    
    # Config 정보 추출
    config_pattern = r'config\s+([^\s]+)\s+(.+)'
    configs = re.findall(config_pattern, content)
    
    print("\n=== 시뮬레이션 설정 ===")
    for key, value in configs:
        if 'numNodes' in key or 'time' in key:
            print(f"{key}: {value}")

if __name__ == "__main__":
    analyze_sca_file()
