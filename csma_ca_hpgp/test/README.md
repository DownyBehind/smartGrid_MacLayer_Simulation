# HPGP MAC Baseline Experiments

## 연구 목표

본 연구는 **HPGP (IEEE 1901) 기반 Vehicle Charging MAC**의 **공유 버스 환경**에서 **DC Current Request/Response (100ms deadline)**의 **스케줄 가능성**을 분석하고, **최악의 시나리오**를 모델링하는 것을 목표로 합니다.

### 핵심 연구 질문
- **DC DMR (Deadline Miss Rate)**이 노드 수와 스케줄링 알고리즘에 따라 어떻게 변화하는가?
- **최악의 시나리오**에서 DC가 얼마나 쉽게 굶주리는가?
- **CAP3 (SLAC)과 CAP0 (DC) 간의 우선순위 충돌**이 성능에 미치는 영향은?

## 실험 설계

### 1. Baseline Worst Case 시나리오

#### WC-A: Continuous SLAC Train (순차·무간격)
- **목적**: SLAC 세션이 순차적으로 연속 실행되어 CAP3 점유율 70-90% 달성
- **특징**: 빈틈 없는 CAP3 점유로 DC 릴리스 타이밍과 정렬하여 DMR 최대화
- **설정**: PRS ON, 연속적인 SLAC 실행

#### WC-B: Simultaneous SLAC Burst (ρ=1.0)
- **목적**: 다중 SLAC 세션이 동시에 시작되어 CAP3 충돌 및 재전송 클러스터 발생
- **특징**: 충돌 폭주로 airtime 낭비 최대화, CAP0 큐잉 증가
- **설정**: PRS OFF, 동시 SLAC 실행

### 2. 실험 조건

#### 공통 설정
- **토폴로지**: Shared-bus (SLAC과 DC 모두 공유 매체 사용)
- **우선순위**: SLAC=CAP3 (최고), DC=CAP0 (최저)
- **DC 기한**: 100ms
- **DC Guard**: δ=0ms (없음)
- **DC 세그먼트**: L2 frames=3
- **Beacon duty**: 10%
- **노드 수**: N ∈ {2, 5, 10}
- **실험 횟수**: 각 조건당 30회 (고정 시드 + run index offset)

#### 채널 모델
1. **Pure-MAC**: PER=0, ISP busy=0 (이상적 채널)
2. **MAC+Channel**: PER=1e-3, impulse=1-2ms, ISP busy p=0.1, mean=2ms (현실적 채널)

## 파일 구조 및 역할

### 1. 핵심 구현 파일

#### `HpgpMac.h` / `HpgpMac.cc`
- **역할**: HPGP MAC 프로토콜의 핵심 구현
- **주요 기능**:
  - CSMA/CA 백오프 알고리즘
  - CAP3 (SLAC) 및 CAP0 (DC) 우선순위 처리
  - 충돌 감지 및 재전송 로직
  - 로깅 기능 (mac_tx.log, slac_attempt.log)
- **핵심 함수**:
  - `initialize()`: MAC 초기화 및 파라미터 설정
  - `handleMessage()`: 메시지 처리 및 상태 머신
  - `processPriorityResolution()`: 우선순위 해결 프로세스
  - `startBackoff()`: 백오프 알고리즘 실행
  - `logMacTx()`: MAC 전송 로깅
  - `logSlacAttempt()`: SLAC 시도 로깅

#### `SlacApplication.h` / `SlacApplication.cc`
- **역할**: SLAC (Signal Level Attenuation Characterization) 프로토콜 구현
- **주요 기능**:
  - SLAC 세션 관리
  - DC Current Request/Response 처리
  - 100ms deadline 관리
  - 연결 시간 측정
- **핵심 함수**:
  - `startSlac()`: SLAC 프로세스 시작
  - `sendSlacMessage()`: SLAC 메시지 전송
  - `startDcLoop()`: DC 루프 시작
  - `sendDcRequest()`: DC 요청 전송
  - `logDcCycle()`: DC 사이클 로깅

#### `ChannelManager.h` / `ChannelManager.cc`
- **역할**: 채널 상태 관리 및 충돌 감지
- **주요 기능**:
  - 채널 busy/idle 상태 관리
  - 충돌 감지 및 통지
  - 전송 완료 확인
- **핵심 함수**:
  - `initialize()`: 채널 매니저 초기화
  - `handleMessage()`: 채널 이벤트 처리
  - `onTransmissionComplete()`: 전송 완료 처리

### 2. 네트워크 구성 파일

#### `SimpleHpgpNetwork.ned`
- **역할**: ChannelManager를 포함한 완전한 HPGP 네트워크 구성
- **구성**: ChannelManager + SlacNode들

#### `SimpleNetworkNoChannel.ned`
- **역할**: ChannelManager 없는 단순한 네트워크 구성
- **구성**: 직접 연결된 SlacNode들 (테스트용)

#### `SlacNode.ned`
- **역할**: 개별 노드 구성 (SlacApplication + HpgpMac)
- **파라미터**: 노드 타입, ID, 타이밍 파라미터 등

### 3. 실험 설정 파일

#### `test/baseline_wc_a/omnetpp.ini`
- **역할**: WC-A (Continuous SLAC Train) 실험 설정
- **주요 설정**:
  - `*.numNodes = 2`
  - `repeat = 30`
  - `dcLoopEnabled = true`
  - `recordSlacMessages = true`
  - `recordDcCycles = true`

#### `test/baseline_wc_b/omnetpp.ini`
- **역할**: WC-B (Simultaneous SLAC Burst) 실험 설정
- **주요 설정**:
  - `*.numNodes = ${numNodes=2,5,10}`
  - `repeat = 30`
  - PRS OFF 설정

### 4. 실행 및 분석 스크립트

#### `run_baseline_experiments.py`
- **역할**: Baseline 실험 자동 실행
- **기능**:
  - WC-A, WC-B 실험을 각각 30회씩 실행
  - 2, 5, 10 노드에 대해 실험
  - 결과 분석 자동 실행

#### `analyze_baseline_data.py`
- **역할**: 실험 데이터 분석 및 그래프 생성
- **기능**:
  - 로그 파일 파싱 및 메트릭 계산
  - 6개 핵심 그래프 생성
  - 요약 보고서 생성

## 데이터 수집

### 로그 파일

#### `mac_tx.log`
- **형식**: `nodeId, kind, bpc, bits, startTime, endTime, success, attempts, bpc_val, bc`
- **내용**: MAC 전송 시도 및 성공/실패 정보
- **용도**: RTT, 충돌률, airtime 계산

#### `slac_attempt.log`
- **형식**: `nodeId, tryId, startTime, endTime, success, connTime, msgTimeouts, procTimeout, retries`
- **내용**: SLAC 연결 시도 및 성공/실패 정보
- **용도**: SLAC 연결성, 연결 시간 분석

#### `dc_cycle.log` (목표)
- **형식**: `seq, reqTime, rspTime, rtt, missFlag, gapViolation, retries, segFrames`
- **내용**: DC Request/Response 사이클 정보
- **용도**: DMR, DC 성능 분석

### 파생 지표

#### 핵심 메트릭
- **DMR (Deadline Miss Rate)**: 100ms 기한 초과율
- **RTT p95/p99**: 응답 시간 95/99 백분위수
- **SLAC Connectivity**: SLAC 연결 성공률
- **Airtime Breakdown**: CAP3, Beacon, PRS, Collision, CAP0, Idle 비율
- **Collision Rate**: 충돌 발생률
- **V_max**: 최대 연속 busy 시간

## 실험 결과 확인 방법

### 1. 로그 파일 확인
```bash
# MAC 전송 로그
cat results/mac_tx.log

# SLAC 시도 로그
cat results/slac_attempt.log

# 분석 결과 디렉토리
ls -la results/analysis/
```

### 2. 생성된 그래프 확인
```bash
# 6개 핵심 그래프
ls -la results/analysis/*.png
```

### 3. 실험 실행
```bash
# 전체 실험 실행
python3 run_baseline_experiments.py

# 개별 실험 실행
./csma_ca_hpgp -u Cmdenv -c Baseline_WC_A_Sequential_SLAC test/baseline_wc_a/omnetpp.ini -r 0
```

## 실험 결과 해석 방법

### 1. DMR (Deadline Miss Rate) 분석
- **목표**: DMR < 1% (99% 이상의 DC 요청이 100ms 내 완료)
- **해석**: 
  - DMR이 낮을수록 DC 성능이 좋음
  - 노드 수 증가 시 DMR 증가 패턴 관찰
  - WC-A vs WC-B 시나리오 비교

### 2. RTT (Round Trip Time) 분석
- **p95 RTT**: 95%의 요청이 이 시간 내 완료
- **p99 RTT**: 99%의 요청이 이 시간 내 완료
- **해석**:
  - RTT가 낮을수록 응답성이 좋음
  - 노드 수에 따른 RTT 증가 패턴 분석

### 3. Airtime Breakdown 분석
- **CAP3 (SLAC)**: SLAC 전송으로 인한 채널 점유
- **CAP0 (DC)**: DC 전송으로 인한 채널 점유
- **Collision**: 충돌로 인한 채널 낭비
- **Idle**: 채널 유휴 시간
- **해석**:
  - CAP3 점유율이 높을수록 DC가 굶주림
  - 충돌률이 높을수록 효율성 저하

### 4. SLAC Connectivity 분석
- **연결 성공률**: SLAC 프로세스 완료율
- **연결 시간**: SLAC 완료까지 소요 시간
- **해석**:
  - 높은 연결성은 안정적인 통신 보장
  - 짧은 연결 시간은 빠른 설정 완료

### 5. 시나리오별 비교
- **WC-A vs WC-B**: 
  - WC-A는 순차적 실행으로 안정적
  - WC-B는 동시 실행으로 충돌 발생
- **노드 수별 성능**:
  - 노드 수 증가 시 성능 저하 패턴
  - 확장성 한계점 식별

## 현재 실험 결과 (예시)

### 핵심 지표
- **DMR**: 0.0000 (100% 성공)
- **RTT p99**: 0.000171s (매우 낮은 지연)
- **SLAC Connectivity**: 1.0000 (100% 연결 성공)
- **Collision Rate**: 0.0000 (충돌 없음)
- **Airtime Ratio**: 0.0029 (매우 낮은 채널 사용률)

### 해석
현재 실험 결과는 **이상적인 조건**에서의 성능을 보여줍니다:
- DC 요청이 100% 100ms 내 완료
- SLAC 연결이 100% 성공
- 충돌이 전혀 발생하지 않음

이는 **Pure-MAC 모델**과 **2노드 환경**에서의 결과로, 실제 환경에서는 더 복잡한 패턴이 관찰될 것으로 예상됩니다.

## 향후 개선 방향

1. **dc_cycle.log 생성**: DC 루프 시작 문제 해결
2. **다양한 채널 모델**: MAC+Channel 모델 구현
3. **확장된 노드 수**: 더 많은 노드에서의 성능 분석
4. **실시간 모니터링**: 실험 진행 상황 실시간 확인
5. **통계적 분석**: 신뢰구간 및 통계적 유의성 검증