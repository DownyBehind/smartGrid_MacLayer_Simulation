좋아, “전체 DC 충전 프로세스”를 시간=100으로 놓고 단계별 비율을 **실측 통계**에 기대어 잡아볼게. 차/날씨/충전기마다 편차가 커서 “절대값”은 아니고, 아래는 **현장에서 관측된 분포 + 업계 자료**를 합쳐 만든 “현실적인 기준선(range)”이야.

# 기준 단계

1. 초기화(링크·세션 셋업 = SLAC/세션설정/파라미터 교환)
2. 안전체크(케이블 체크·프리차지)
3. 전력전송 – **CC 구간(고정전류/초반 고출력)**
4. 전력전송 – **CV/테이퍼 구간(출력 서서히 하강)**
5. 종료(Stop/용접검출/세션종료)

# 대표 시나리오별 비율(시간=100 기준)

| 시나리오                      |       초기화 |   안전체크\* | 전력전송(CC) | 전력전송(CV/테이퍼) |         종료 |
| ----------------------------- | -----------: | -----------: | -----------: | ------------------: | -----------: |
| **DC 10→80%** (보통 20–30분)  |     **1–2%** | **0.3–0.7%** |   **55–75%** |          **22–42%** | **0.5–1.5%** |
| **DC 10→100%** (보통 40–60분) | **0.8–1.5%** | **0.2–0.6%** |   **40–55%** |          **42–58%** | **0.5–1.5%** |

\*안전체크(케이블 체크·프리차지)는 초기화 묶음에 포함해도 되지만, 표에 따로 떼서 퍼센트를 보여줬어.
※ 위 범위가 넓은 이유: 차량별 충전 커브(피크 파워/무릎 SoC), 배터리 온도, 충전기 등급(150/350 kW) 영향이 큼.

## 왜 이런 비율이 나오나 — 핵심 근거

- **초기화 전체(전력 인가까지)**: 대규모 현장 로그 분석에서 **중앙값 ≈ 27.6 s**. 세부로 보면 **케이블 체크 중앙값 ≈ 6.9 s**, **프리차지 중앙값 ≈ 2.2 s**. 25 분짜리(=1500 s) 세션 기준 초기화는 **약 1–2%** 수준으로 수렴. ([Idaho National Laboratory][1])
- **10→80% 구간이 “가성비 좋은” 이유**: 60–80% 부근부터 **출력이 꺾이는(테이퍼)** 패턴이 일반적이라, 80→100%의 **시간 대비 이득이 급감**. 공공기관·사업자 교육자료·가이드들 모두 10–80%를 권장. ([US EPA][2], [fastnedcharging.com][3], [blog.evbox.com][4])
- **80→100%는 “시간먹는 구간”**: 실차 테스트 기사·리뷰에서도 “**마지막 20%가 앞의 70–75%만큼 오래 걸릴 수 있다**”는 케이스가 보고됨 → 10→100% 전체에선 **CV/테이퍼가 시간 지배**가 되기 쉬움. ([MotorTrend][5])
- **종료(Stop→용접검출)**: 표준 요구 시간은 엄격(예: **WeldingDetection 응답 ≤1.5 s, EVCC 시퀀스 성능 시간 40 s 한계**), 실제 동작은 보통 수 초 내외 → **0.5–1.5%** 수준으로 귀결. ([GitHub][6])

## 해석 팁

- **짧은 세션**(예: 10→50% “스플래시 충전”)에선 초기화/종료 비중이 상대적으로 커져 \*\*2–5%\*\*까지 보일 수 있어. 반대로 **긴 세션**(10→100%)에선 **CV/테이퍼**가 커져 **절반 가까이**를 차지하기도 함.
- 겨울철/저온 배터리는 예열 때문에 **초반 CC 비중이 줄고 테이퍼·제한구간 비중이 늘어** 전체 퍼센트가 오른쪽(테이퍼 쪽)으로 이동하는 경향이 있어.

필요하면 네가 실제로 수집한 세션 로그(시작/전력인가/SoC/정지 타임스탬프)로 **차량·온도별 커브에서 “네 환경 전용” 퍼센트를 역산**해 CSV/PNG로 뽑아줄게.

[1]: https://inl.gov/content/uploads/2024/03/ChargeX-report_Quantifying-time-to-charge_Jul2025.pdf "Quantifying Time to Charge"
[2]: https://www.epa.gov/system/files/documents/2024-06/mstrs-spr-mtg-dc-fast-chrg-consumer-info-2024-05-30.pdf?utm_source=chatgpt.com "DC Fast Charging Information for Consumers"
[3]: https://www.fastnedcharging.com/en/brands-overview?utm_source=chatgpt.com "Check your EVs charge speed and compatibility"
[4]: https://blog.evbox.com/ev-charging-times?utm_source=chatgpt.com "How long does it take an electric car to charge?"
[5]: https://www.motortrend.com/features/fastest-charging-evs?utm_source=chatgpt.com "The 10 Fastest-Charging EVs We Tested in 2023"
[6]: https://github.com/uhi22/pyPLC?utm_source=chatgpt.com "GitHub - uhi22/pyPLC: Electric vehicle CCS charging ..."
