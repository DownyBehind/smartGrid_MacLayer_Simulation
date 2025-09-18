# csma_ca_hpgp_withINET Test Suite

본 테스트는 `inet_plc/inet` 하위 HPGP MAC 구현이 문헌과 사전 정의 동작을 준수하는지 검증합니다.

참고 문헌
- Jung et al., 2005, "MAC throughput analysis of HomePlug 1.0" (timing sequences on medium, BPC→DC/CW mapping)
- Ayar et al., 2015, "An adaptive MAC for HomePlug Green PHY PLC" (HPGP Green PHY timing/절차)

테스트 공통 규칙
- 모든 테스트는 동일한 NED 토폴로지(간단한 EVSE-단일/다수 EV + `WireJunction`)를 사용
- INI에서 타이밍(PRS0/PRS1/RIFS/CIFS/slotTime)을 명시하고 로그 레벨을 높임
- 검증은 `*.vec`/`*.sca`와 이벤트 로그에서 추출한 타임스탬프를 파이썬으로 검증

테스트 목록
- tc1: Timing Sequence Verification
  - 목적: Contention Period → FrameTx → RIFS → Response → CIFS → PRS0/PRS1 → Contention 재진입 시퀀스가 규격대로 발생하는지 확인
  - 방법: 단일 EV와 EVSE. SLAC의 Req/Res 한 쌍 전송. `IEEE1901Mac`의 시그널과 `PLCFrame`의 `txStartTime/txEndTime`을 통해 간격 측정
  - 판정: |RIFS-실측−RIFS-설정| ≤ 1us, |CIFS-실측−CIFS-설정| ≤ 1us, PRS0/PRS1 순서/존재 확인
- tc2: Priority Resolution Correctness
  - 목적: CA0~CA3 우선순위가 PRS에서 의도대로 승리하는지, 동순위 충돌 시 백오프로 넘어가는지 확인
  - 방법: 4 EV 각각 CA0..CA3 프레임 동시 대기. PRS 비트 패턴 로깅 및 승자 확인
  - 판정: 가장 높은 우선순위 노드가 연속적으로 선점. 동순위는 충돌 후 백오프 지연 증가
- tc3: Random Backoff BPC/DC/BC Mapping
  - 목적: Jung(2005) 기반 BPC→(DC,CW) 매핑이 기대범위와 일치하는지 분포 검증
  - 방법: 다수 반복 송신으로 백오프 샘플 수집. 평균/분산이 이론값 근접
  - 판정: KS-test p>0.05 또는 평균/분산 상대오차 <10%
- tc4: Contention/Collision under Load
  - 목적: 동일 CAP 노드 다수에서 충돌, 재시도, 응답 타이밍이 유지되는지 확인
  - 방법: equalCapAllCollide=true 조건 포함 대량 DC 요청. 충돌률/성공률/지연
  - 판정: 충돌률 증가, 성공시 RIFS/CIFS 유지

실행 방법
- 각 tc 폴더에서: `opp_run -u Cmdenv -n ..:../../inet_plc/inet:../../omnetpp-6.1/samples:../../inet_plc/inet/src -l ../../omnetpp-6.1/out/gcc-release/src/liboppsim.so -c General -f omnetpp.ini | cat`
- 검증: `python3 validate.py`

주의
- 실제 경로는 환경에 맞게 수정 가능. 테스트는 최소 5~30초 내 종료하도록 구성.

MD
