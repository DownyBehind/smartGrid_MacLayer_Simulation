# CSMA CA Fake Wired

Test Command

```bash
opp_run -u Cmdenv \
    -n "/home/kimdawoon/study/workspace/research/inet/src;./ned" \
    -c Base \
    ini/omnetpp.ini
```


Test Command 2

```bash
opp_run -u Cmdenv \
    -n "/home/kimdawoon/study/workspace/research/inet/src;./ned" \
    -c HPGP_Step1 \
    ini/omnetpp.ini
```

Test Command 2

```bash
opp_run -u Cmdenv \
    -n "/home/kimdawoon/study/workspace/research/inet/src;./ned" \
    -c Paper_Baseline \
    ini/omnetpp.ini
```

Test Command + TimeSlot

```bash
opp_run -u Cmdenv \
   -n "/home/kimdawoon/study/workspace/research/inet/src;./ned;../TimeSlot" \
   -x"csma_ca_test_for_Ayar_Paper.FakeWireCsmaCaNetwork.numHosts=20" \
   -c Paper_Baseline \
   ini/omnetpp.ini

```

```bash
opp_run -u Cmdenv \
   -n "/home/kimdawoon/study/workspace/research/inet/src;./ned;../TimeSlot" \
   -x"csma_ca_test_for_Ayar_Paper.FakeWireCsmaCaNetwork.numHosts=20" \
   -c Paper_Baseline \
   ini/omnetpp.ini
```

Test Command + TimeSlot

```bash
opp_run -u Cmdenv   -n "/home/kimdawoon/study/workspace/research/inet/src;./ned;../TimeSlot"   -c Paper_Baseline   ini/omnetpp.ini
```


Collect Env Value Command

```bash
opp_run -u Cmdenv   -n "/home/.../inet/src;./ned"   -c HPGP_Step1   -q runconfig ini/omnetpp.ini > runconfig.txt
```