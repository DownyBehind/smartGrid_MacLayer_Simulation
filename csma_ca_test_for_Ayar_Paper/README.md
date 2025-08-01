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

Collect Env Value Command

```bash
opp_run -u Cmdenv   -n "/home/.../inet/src;./ned"   -c HPGP_Step1   -q runconfig ini/omnetpp.ini > runconfig.txt
```