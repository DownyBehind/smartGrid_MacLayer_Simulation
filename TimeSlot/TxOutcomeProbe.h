#pragma once
#include <omnetpp.h>
#include <string>

using namespace omnetpp;          // OMNeT++ 기본 네임스페이스

/**
 * 802.11 Tx 결과(성공·충돌)-타임슬롯을 누적하는 간단한 프로브
 *  - host[0]·wlan[wlanIndex] 아래 mac 서브모듈의 시그널을 구독
 *  - ts_success_time / tc_collision_time / succ_pkts / tx_attempts 스칼라 기록
 */
class TxOutcomeProbe : public cSimpleModule, public cListener
{
  private:
    /* ---------- 파라미터 ---------- */
    std::string targetNodePath;   // 상위 INI: **.targetNodePath
    int         wlanIndex = 0;    // INI: **.wlanIndex
    double      sifs = 0, cifs = 0, ackTxTime = 0, ackTimeout = 0;
    double slotTime = 0;                    // ★ 추가


    bool  debugSignals  = false;  // INI: **.debugSignals (true → 첫 N개 시그널 로그)
    int   debugMaxLines = 12;     // INI: **.debugMaxLines

    /* ---------- 내부 포인터 ---------- */
    cModule *mac   = nullptr;
    cModule *radio = nullptr;

    /* ---------- 구독 시그널 ---------- */
    simsignal_t rxFromUpperSig = SIMSIGNAL_NULL;   // upper→MAC (TX 시작)
    simsignal_t rxFromLowerSig = SIMSIGNAL_NULL;   // radio→MAC (ACK 수신)
    simsignal_t txToUpperSig   = SIMSIGNAL_NULL;   // MAC→upper (무ACK 성공)

    /* ---------- 런타임 상태 ---------- */
    bool   awaitingAck      = false;
    double currentDataBits  = 0.0;
    double currentDataTxDur = 0.0;
    cMessage *ackWait       = nullptr;             // 타임아웃 이벤트

    /* ---------- 누적 ---------- */
    simtime_t succTime = SIMTIME_ZERO;
    simtime_t collTime = SIMTIME_ZERO;
    long attempts = 0;
    long succs    = 0;

  protected:
    /* 기본 API */
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;

    /* 시그널 수신 오버로드 (object) */
    virtual void receiveSignal(cComponent *src, simsignal_t id,
                               cObject *obj, cObject *details) override;
    /* 시그널 수신 오버로드 (intval_t — 구현은 빈 스텁) */
    virtual void receiveSignal(cComponent *src, simsignal_t id,
                               intval_t l, cObject *details) override;

    /* 내부 유틸 */
    void attach();               // 대상 wlan 찾아 subscribe

  public:
    virtual ~TxOutcomeProbe() override;            // 타이머 안전 제거
};
