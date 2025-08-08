#include "SendIntervalConfigurator.h"

Define_Module(SendIntervalConfigurator);

void SendIntervalConfigurator::initialize()
{
    // ‼ 기존 코드 지우고 ↓ 한 줄로 교체
    int N = getParentModule()->par("numHosts");   // 네트워크 모듈의 파라미터

    double base = par("baseInterval").doubleValue();   // 1.5 ms
    double iv   = base * N / 5.0;                      // 스케일

    for (int i = 0; ; ++i) {
        cModule *host = getParentModule()->getSubmodule("host", i);
        if (!host) break;
        cModule *app  = host->getSubmodule("app", 0);
        if (app) app->par("sendInterval") = iv;
    }
    EV_INFO << "SendInterval set to " << iv << " for N=" << N << endl;
}
