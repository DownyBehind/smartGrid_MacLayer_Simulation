# Build 

```bash
cd ~/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot
export INET_PROJ=~/study/workspace/research/inet

opp_makemake -f -O out \
  -I$INET_PROJ/src \
  -L$INET_PROJ/out/clang-release/src \
  -lINET \
  -s -o timeslot

make -j
```


# TimeSlot 빌드/실행 가이드 (Markdown)

## 1) 기본 빌드 루틴

* **소스(.cc/.h)만 수정** → 기존 Makefile이 있다면 `make`만 실행

```bash
cd ~/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot
make -j
```

* **새 파일 추가/삭제(.cc/.ned/.msg)** 또는 **컴파일/링크 옵션 변경(-I/-L/-l)** 시 → `opp_makemake` 다시 생성 후 `make`

```bash
cd ~/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot
export INET_PROJ=~/study/workspace/research/inet

opp_makemake -f -O out \
  -I$INET_PROJ/src \
  -L$INET_PROJ/out/clang-release/src \
  -lINET \
  -s -o timeslot

make -j
```

> **gcc로 INET을 빌드했다면** `clang-release` 대신 `gcc-release`로 변경하세요.

---

## 2) INET 라이브러리 존재/툴체인 확인

```bash
# clang-release 사용 시
ls ~/study/workspace/research/inet/out/clang-release/src/libINET.so

# gcc-release 사용 시
ls ~/study/workspace/research/inet/out/gcc-release/src/libINET.so
```

* 위 경로에 `libINET.so`가 있어야 **링크**가 정상 동작합니다.
* TimeSlot도 **동일한 툴체인(clang/gcc)** 으로 빌드하는 것을 권장합니다.

---

## 3) 런타임 설정 (ini / 환경변수)

`omnetpp.ini` 예시:

```ini
[General]
ned-path = ../../../inet/src;../ned;../../TimeSlot
**.result-recording-modes = +scalar

load-libs = /home/kimdawoon/study/workspace/research/inet/out/clang-release/src/INET:/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot/out/clang-release/src/libtimeslot
```

필요 시 라이브러리 검색 경로 추가:

```bash
export LD_LIBRARY_PATH=~/study/workspace/research/inet/out/clang-release/src:~/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot/out/clang-release/src:$LD_LIBRARY_PATH
```

> gcc로 빌드했다면 위의 `clang-release` 를 `gcc-release` 로 바꾸세요.

---

## 4) 편의 alias

```bash
alias build_timeslot='cd ~/study/workspace/research/project_smartCharging_macLayer_improvement/TimeSlot && export INET_PROJ=~/study/workspace/research/inet && opp_makemake -f -O out -I$INET_PROJ/src -L$INET_PROJ/out/clang-release/src -lINET -s -o timeslot && make -j'
```

> 이후에는 터미널에서 `build_timeslot` 만 입력하면 **재생성 + 빌드**가 한 번에 수행됩니다.
> gcc 환경이면 `clang-release` 부분만 `gcc-release`로 바꾸어 동일하게 사용하세요.

---

## 5) 요약

* **파일 추가/옵션 변경 없음** → `make -j`
* **파일 추가/옵션 변경 있음** → `opp_makemake … && make -j`
* ini의 `ned-path` / `load-libs` 는 **빌드된 경로와 정확히 일치**해야 함
* INET과 TimeSlot은 **같은 툴체인(clang/gcc)** 으로 빌드 권장
