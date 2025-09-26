## HPGP MAC Layer Architecture & Message Flow (csma_ca_hpgp_withINET)

본 문서는 현재 구현된 HPGP(IEEE 1901 HomePlug 1.0) MAC 계층의 구성요소와 메시지 처리 흐름을 아키텍처/모델 관점에서 설명합니다. 테스트/검증을 위해 추가한 계측 로그 태그와 테스트 플래그도 함께 정리합니다.

### 1) 구성요소 개요

```
+------------------------------+         +-----------------------------------+
| Upper Apps (SlacApp, etc.)  |  PLC    | IEEE1901Interface                 |
|                              | Frames  |  - UpperRelay (debug relay)       |
|  * 테스트 플래그로 주기적 TX | ------> |  - IEEE1901Mac (MAC)             |
|    및 SLAC 완료 전 송신 허용 |         |  - IEEE1901Phy (PHY)             |
+------------------------------+         +------------------+----------------+
                                                        | Control/PRS APIs
                                                        v
                                            +-------------------------------+
                                            | IEEE1901GlobalScheduler       |
                                            |  (PRS coordinator, singleton) |
                                            +-------------------------------+
```

- SlacApp: 테스트 트래픽(PLCFrame) 생성, 주기/동기화/사이클 제어를 위한 테스트 플래그 제공
- UpperRelay: 상위 프레임을 MAC으로 중계하며 릴레이 로그([RELAY]) 출력
- IEEE1901Mac: PRS(우선순위 해상) → CSMA/CA Backoff → TX의 핵심 로직 및 로그 출력
- IEEE1901Phy: 간단한 충돌 모델/BER 모델, MAC에 Busy/Fail 알림, 충돌/드롭 로그 출력
- IEEE1901GlobalScheduler: 멀티노드 PRS 창을 전역에서 동기화/집계하는 싱글톤

중요 파라미터(예시)
- `**.plc.slotTime`, `**.plc.prs0Duration`, `**.plc.prs1Duration`
- `**.plc.phy.enableCollisionModel = true`
- PHY 데이터레이트는 실험 정책상 14 MHz(14e6 bps)로 고정 운용을 권장합니다.

테스트 플래그(주요)
- `**.ev[*].slac.testSyncStart=true`: 시작 시점 동기화
- `**.ev[*].slac.testInjectPostSlacMsgs=true`: SLAC 이후 지속 송신
- `**.ev[*].slac.testPostSlacPeriod=...`: 상위 송신 주기
- `**.ev[*].slac.testAllowPreSlacSweep=true`: SLAC 전에도 테스트 송신 허용

### 2) 상위→MAC 수신 및 PRS(우선순위 해상)

```
Upper App(SlacApp)
  - PLCFrame 생성 및 전송 [UL_TX]
      |
      v
IEEE1901Interface.relay  --[RELAY]-->  IEEE1901Mac.upperLayerIn
                                      [UL_RX]/[UL_DISPATCH]
                                      inPriorityResolution=true
                                      pendingPrsSend[PRS0/1]=true
      |
      v
IEEE1901GlobalScheduler (싱글톤)
  - onPrsPhaseStart(slot=generation window) 콜백 → MAC이 pending이면 sendPrsSignal(slot)
  - onPrsPhaseEnd(slot) 콜백 → 참여자 집계, [PRS_WINDOW] 로그, MAC으로 결과 통지

IEEE1901Mac
  - sendPrsSignal(0/1): [PRS_TX]
  - onPrsPhaseEnd(slot): [PRS_WINDOW] → conclude/evaluate
    * evaluatePriorityResolution():
      - 상위 클래스 존재: LOST → handlePriorityLoss()
      - 동일 클래스 충돌: WON 취급(HPGP대로 백오프로 진행)
      - 충돌/상위 없음: WON → handlePriorityWin()
  - handlePriorityWin(): [PRS_WIN] → scheduleBackoff()
  - handlePriorityLoss(): [PRS_DEFER], 현재 프레임 큐잉, 재시도 타이머 설정
```

관련 로그 태그
- `[UL_RX]`, `[UL_DISPATCH]`, `[RELAY]`, `[PRS_TX]`, `[PRS_WINDOW]`, `[PRS_WIN]`, `[PRS_DEFER]`

### 3) Backoff(HPGP HomePlug 1.0) 및 슬롯 감지

```
scheduleBackoff()
  - [BK_START]  (BPC/DC/CW/BC 초기화 및 BPC 증가)
  - backoffTimer를 slotTime 간격으로 스케줄
      |
      v
handleBackoffTimer()
  - busy = !isChannelIdle()
  - [SLOT_CHECK] busy=<T/F>
  - processSlotResult(busy)
      |
      +-- busy: updateCountersOnBusySlot()
      |         - [BUSY_SLOT] (BC/ DC 감소, DC==0이면 BPC 증가/에스컬레이션)
      |         - 다음 슬롯 타이머 스케줄
      |
      +-- idle: updateCountersOnIdleSlot()
                - BC 감소, BC==0 & idle이면 PHY로 전송 진행
```

관련 로그 태그
- `[BK_START]`, `[SLOT_CHECK]`, `[SLOT_RESULT]`, `[BUSY_SLOT]`, `MAC busy; enqueue ...`

채널 Busy 감지(요약)
- PHY에서 `CTRL_PHY_BUSY_ON/OFF`를 MAC으로 통지 → MAC의 전역 busy 카운터 업데이트
- `isChannelIdle()`는 전역 busy 상태를 확인하여 슬롯 바쁨/유휴를 판정

### 4) PHY 전송/수신 및 충돌/BER 모델

```
MAC → PHY: handleFrameFromMac()
  - 이미 TX 중이면 큐잉, 아니면 전송 시작
  - enableCollisionModel=true인 경우:
    * activeTransmitters 레지스트리에 등록
    * 동시 TX가 감지되면 양쪽에 충돌 표시(txCollided=true)
    * [COLL_TRACE], 필요 시 [PHY_COLLISION]
  - 채널로 프레임 전송 → transmissionEnd 시각에 self-message
  - TX 끝: activeTransmitters에서 제거, CTRL_PHY_BUSY_OFF
           txCollided==true이면 CTRL_TX_FAIL 통지

채널 → PHY: handleFrameFromChannel()
  - SNR/BER 계산 → PER 기반 드롭 여부 산정
  - enableCollisionModel=true이고, 수신 시점 동시 TX/충돌 표식이 있으면 드롭
    * [PHY_COLLISION], "Dropping frame due to explicit collision model"
  - 드롭 아니면 MAC으로 전달(지연 고려), CTRL_PHY_BUSY_OFF
```

관련 로그 태그
- `[COLL_TRACE]`, `[PHY_COLLISION]`, `CTRL_TX_FAIL`, `Dropping frame due to explicit collision model`

### 5) 상위로의 수신 전달

```
PHY → MAC: handleLowerLayerFrame()
  - PLCFrame 수신 시 상위로 인계
  - CTRL_* 메시지는 MAC의 busy/실패 처리 경로로 연결

MAC → Upper: mac.upperLayerOut → Upper Apps
```

### 6) 주요 시퀀스(요약 다이어그램)

송신 성공 시나리오(동일 우선순위 충돌 없음 또는 backoff로 분리)
```
SlacApp → Relay → MAC[UL_RX]->PRS{TX,WINDOW}->[PRS_WIN]
   → Backoff [BK_START] → [SLOT_CHECK]/[SLOT_RESULT] ... (idle 진행)
   → PHY TX 시작 → 채널 → PHY RX(상대) → MAC 상위 전달
```

충돌/바쁜 슬롯 시나리오(테스트에서 기대되는 증거)
```
SlacApp → MAC → PRS 결과(동일 클래스 충돌 → 백오프)
   → [BK_START] → [SLOT_CHECK] busy → [BUSY_SLOT] (DC 감소, DC==0이면 escalate)
   → (동시 TX 시) PHY 측 [PHY_COLLISION]/CTRL_TX_FAIL/Drop 로그
```

### 7) 테스트/검증과 계측 로그

테스트 케이스에서 확인하는 대표 로그
- PRS: `[PRS_TX]`, `[PRS_WINDOW]`, `[PRS_WIN]`, `[PRS_DEFER]`
- Backoff/Busy: `[BK_START]`, `[SLOT_CHECK]`, `[SLOT_RESULT]`, `[BUSY_SLOT]`, “MAC busy; enqueue ...”
- 충돌/재시도: `[PHY_COLLISION]`, `Dropping frame due to explicit collision model`, `CTRL_TX_FAIL`

권장 사용법
- 충돌 검증(tc8): `**.plc.phy.enableCollisionModel=true`, 송신 주기 단축으로 동시 TX 유도
- DC 에스컬레이션(tc10): 바쁜 슬롯을 충분히 만들고 `[BUSY_SLOT] escalate` 로그 확인

### 8) 설계 상의 원칙(요약)
- PRS 타이밍/판정은 전역 스케줄러가 권위 있게 조정(멀티노드 동기화 정확성)
- MAC의 로컬 타이머 핸들러는 호환성 래퍼(no-op)로 유지(ABI 안정), 실 동작은 스케줄러 콜백 기반
- Backoff는 HPGP 규칙(BC/DC/CW/BPC) 준수, 바쁜 슬롯 시 DC 감소 및 DC==0에서 BPC 증가
- PHY 충돌 모델은 단순/명시적이며, 계측 로그로 검증 가능하도록 설계


