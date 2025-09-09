# hpgp_sim/plot_slac.py
# ---------------------
# SLAC 5종 메시지를 색으로 구분한 간트 타임라인 (노드별 + 하단 ALL 오버레이)
# - 입력: out_dir/tx_log.csv, debug.csv
# - 출력: out_dir/slac_timeline.png
# - sim_time_us 인자를 주면 x축을 [0, sim_time]으로 고정
#
# 추가:
# - SLAC_DONE 표시: ok=1(초록 ★), ok=0(빨간 x)
# - SLAC_DONE 시점 세로선: ok=1(초록 점선), ok=0(빨간 점선)
# - 노드 정렬: 맨 위 N1 → N2 → … → (마지막) N0=SECC → (맨 아래) ALL

import os, csv, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# SLAC 메시지 5종 컬러
COLOR = {
    "CM_SLAC_PARM":   "tab:blue",
    "CM_START_ATTEN": "tab:orange",
    "CM_MNBC_SOUND":  "tab:purple",
    "CM_ATTEN_CHAR":  "tab:green",
    "CM_SLAC_MATCH":  "tab:red",
}

def _classify_kind(raw_kind: str):
    if not raw_kind:
        return None
    rk = str(raw_kind).upper()
    # 느슨한 부분문자열 매칭
    if "ATTEN_CHAR" in rk: return "CM_ATTEN_CHAR"
    if "MNBC" in rk or "SOUND" in rk: return "CM_MNBC_SOUND"
    if "START_ATTEN" in rk: return "CM_START_ATTEN"
    if "MATCH" in rk: return "CM_SLAC_MATCH"
    if "PARM" in rk: return "CM_SLAC_PARM"
    for canon in COLOR.keys():
        if canon in rk:
            return canon
    return None

def _read_tx_rows(tx_csv_path):
    rows = []
    with open(tx_csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        _ = next(rdr, None)  # start_us,end_us,node,prio,bits,kind,success
        for r in rdr:
            try:
                start_us = int(r[0]); end_us = int(r[1])
                node_id  = str(r[2]).strip()               # "N0","N1",...
                kind     = (r[5].strip() if len(r) > 5 else "")
                mapped   = _classify_kind(kind)
                if mapped is None:
                    continue
                rows.append((start_us, end_us, node_id, mapped))
            except Exception:
                continue
    return rows

# debug.csv 파서용 정규식
_NODE_PATTERNS = [
    re.compile(r"node\s*[:=]\s*'?([A-Za-z0-9_]+)"),
    re.compile(r"'node'\s*:\s*'([A-Za-z0-9_]+)'"),
    re.compile(r'"node"\s*:\s*"([A-Za-z0-9_]+)"'),
    re.compile(r"'node'\s*:\s*([A-Za-z0-9_]+)"),
    re.compile(r'"node"\s*:\s*([A-Za-z0-9_]+)'),
]
_OK_PATTERNS = [
    re.compile(r"ok\s*[:=]\s*([01])"),
    re.compile(r"'ok'\s*:\s*([01])"),
    re.compile(r'"ok"\s*:\s*([01])'),
]

def _parse_node_from_kv(kv_text: str):
    if not kv_text:
        return None
    s = str(kv_text)
    for pat in _NODE_PATTERNS:
        m = pat.search(s)
        if m:
            return m.group(1)
    return None

def _parse_ok_from_kv(kv_text: str):
    if not kv_text:
        return None
    s = str(kv_text)
    for pat in _OK_PATTERNS:
        m = pat.search(s)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None

def _node_num(n: str) -> int:
    """'N12' -> 12, 파싱 실패 시 큰 값 리턴"""
    try:
        if n and (n[0] in "Nn"):
            return int(n[1:])
        return int(n)
    except Exception:
        return 10**9

def _order_nodes(nodes_set):
    """
    노드 정렬:
    - 맨 위에 N1, 그 다음 N2, ... Nmax
    - 그 다음 N0(SECC)
    - 맨 아래는 ALL (y=-1로 별도 처리)
    """
    nodes_set = set(nodes_set)
    has_secc = "N0" in {s.upper() for s in nodes_set}
    ev_nodes = [n for n in nodes_set if n.upper() != "N0"]
    # 숫자 기준 오름차순
    ev_nodes_sorted = sorted(ev_nodes, key=_node_num)
    # 최상단이 N1이 되도록 y좌표를 역순 배치할 예정이므로,
    # 여기서는 순서만 결정하고 y배치는 아래에서 처리
    ordered = ev_nodes_sorted[:]  # N1, N2, ..., Nmax
    if has_secc:
        # 마지막에 SECC(N0)
        # 실제 y좌표는 아래에서 '최하단'으로 배치
        ordered.append("N0")
    return ordered

def write_slac_timeline(out_dir: str, filename: str = "slac_timeline.png", sim_time_us: int | None = None):
    """SLAC 타임라인 이미지 생성
    Args:
        out_dir: 산출물 폴더
        filename: 저장 파일명
        sim_time_us: 있으면 x축을 [0, sim_time]으로 고정(초 단위로 환산)
    """
    tx_csv = os.path.join(out_dir, "tx_log.csv")
    dbg_csv = os.path.join(out_dir, "debug.csv")
    if not os.path.exists(tx_csv):
        return False

    tx_rows = _read_tx_rows(tx_csv)
    if not tx_rows:
        return False

    # ---- debug 이벤트 로드 ----
    timeouts = []     # (t_us, tag, node)
    retries  = []     # (t_us, node)
    done_ev  = []     # (t_us, node, ok)  # SLAC 완료 표시(+ 세로선)

    if os.path.exists(dbg_csv):
        with open(dbg_csv, newline="", encoding="utf-8") as f:
            rdr = csv.reader(f); _ = next(rdr, None)
            for r in rdr:
                try:
                    t_us = int(r[0]); tag = (r[1] or "").strip().upper()
                    kv   = r[2] if len(r) > 2 else ""
                    if tag in ("SLAC_TIMEOUT_MSG", "SLAC_TIMEOUT_PROC"):
                        node = _parse_node_from_kv(kv)
                        timeouts.append((t_us, tag, node))
                    elif tag == "SLAC_RETRY":
                        node = _parse_node_from_kv(kv)
                        retries.append((t_us, node))
                    elif tag == "SLAC_DONE":
                        node = _parse_node_from_kv(kv)
                        ok   = _parse_ok_from_kv(kv)
                        done_ev.append((t_us, node, 1 if ok == 1 else 0))
                except Exception:
                    continue

    # ---- 노드 목록 정렬 / 시간 범위 ----
    raw_nodes = {n for _,_,n,_ in tx_rows}
    nodes = _order_nodes(raw_nodes)     # 표시 순서 결정 (논리 순서)
    has_secc = any(n.upper()=="N0" for n in nodes)

    # 시간 범위
    if sim_time_us is not None:
        t_min = 0
        t_max = int(sim_time_us)
    else:
        t_min = min(s for s,_,_,_ in tx_rows)
        t_max = max(e for _,e,_,_ in tx_rows)
        for t, _, _ in timeouts:
            t_min = min(t_min, t); t_max = max(t_max, t)
        for t, _ in retries:
            t_min = min(t_min, t); t_max = max(t_max, t)
        for t, _, _ in done_ev:
            t_min = min(t_min, t); t_max = max(t_max, t)

    span_s = max(1.0, (t_max - t_min) / 1e6)

    # ---- Figure 스케일 & 최소 표시폭 ----
    # y 좌표 배치:
    #  - N1..Nmax를 '위쪽'으로 갈수록 큰 y가 되게 배치
    #  - SECC(N0)는 최하단(y=0), ALL은 y=-1
    ev_nodes = [n for n in nodes if n.upper() != "N0"]
    ev_count = len(ev_nodes)
    y_all = -1
    y_base = {}

    # SECC 최하단
    if has_secc:
        y_base["N0"] = 0

    # EV 노드: N1이 최상단이 되도록 높은 y 부여
    # (위쪽이 큰 y 이므로, N1에게 ev_count, N2에게 ev_count-1, ... 할당)
    for idx, n in enumerate(ev_nodes):  # n: N1, N2, ...
        y_base[n] = ev_count - idx

    # y-ticks와 라벨(아래→위 순서로): ALL, SECC(있으면), Nmax..N2, N1
    yticks = [y_all]
    ylabels = ["ALL"]
    if has_secc:
        yticks.append(y_base["N0"]); ylabels.append("SECC")
    for n in reversed(ev_nodes):  # Nmax..N2,N1
        yticks.append(y_base[n]); ylabels.append(n)

    # 그림 크기
    h = max(3.8, 0.36 * (len(yticks) - 1) + 1.8)  # 노드 수 따라 자동 스케일
    fig_w = min(18, 10 + span_s * 0.8)
    fig, ax = plt.subplots(figsize=(fig_w, h))
    ax.set_title("SLAC Timeline (bars = frames on air)")

    x_span_data = max(1e-6, (t_max - t_min) / 1e6)
    ax.set_xlim(0, x_span_data)

    # 픽셀→데이터 변환으로 최소 1.5px 너비 보장
    dpi = fig.dpi
    fig_w_in = fig.get_size_inches()[0]
    px_per_data = max(1e-9, dpi * fig_w_in / x_span_data)  # px per second
    min_w_s = 1.5 / px_per_data

    # y축 설정
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)

    # ---- 간트 바: 노드별 + 하단 ALL (SLAC 5종만) ----
    for (s_us, e_us, node, canon) in tx_rows:
        if node not in y_base:
            # 혹시 모르는 이름(표시 대상 외)은 스킵
            continue
        y = y_base[node]
        s = (s_us - t_min) / 1e6
        w = max((e_us - s_us) / 1e6, min_w_s)
        c = COLOR.get(canon, "gray")
        ax.broken_barh([(s, w)], (y - 0.38, 0.76),
                       facecolor=c, edgecolor=c, linewidth=0.0, alpha=0.95)
        # ALL
        ax.broken_barh([(s, w)], (y_all - 0.38, 0.76),
                       facecolor=c, edgecolor=c, linewidth=0.0, alpha=0.95)

    # ---- 이벤트 오버레이 ----
    # 타임아웃
    for (t_us, tag, node) in timeouts:
        x = (t_us - t_min) / 1e6
        if tag == "SLAC_TIMEOUT_PROC":
            ax.axvline(x=x, color="red", linestyle="--", linewidth=1.2, alpha=0.9)
        else:  # SLAC_TIMEOUT_MSG
            y = y_base.get(node, y_all)
            ax.plot([x], [y], marker="v", color="red", markersize=6, linestyle="None", zorder=5)

    # 재시도
    for (t_us, node) in retries:
        x = (t_us - t_min) / 1e6
        y = y_base.get(node, y_all)
        ax.plot([x], [y], marker="D", color="black", markersize=5, linestyle="None", zorder=5)

    # SLAC 완료(마커 + 세로선)
    for (t_us, node, ok) in done_ev:
        x = (t_us - t_min) / 1e6
        y = y_base.get(node, y_all)
        # 세로선 (전체 높이 가로지름)
        ax.axvline(
            x=x,
            color=("tab:green" if ok == 1 else "red"),
            linestyle=":",
            linewidth=1.1,
            alpha=0.7,
            zorder=3,
        )
        # 노드 라인 위 마커
        if ok == 1:
            ax.plot([x], [y], marker="*", color="tab:green", markersize=8, linestyle="None", zorder=6)
        else:
            ax.plot([x], [y], marker="x", color="red", markersize=7, linestyle="None", zorder=6)

    # ---- 범례 ----
    handles = []
    for canon, color in COLOR.items():
        hdl = plt.Line2D([0], [0], color=color, lw=8)
        handles.append((hdl, canon.replace("CM_", "")))
    h_to = plt.Line2D([0], [0], marker="v", color="red", lw=0, markersize=6)
    h_proc = plt.Line2D([0], [0], color="red", lw=1.2, linestyle="--")
    h_retry = plt.Line2D([0], [0], marker="D", color="black", lw=0, markersize=5)
    h_done_ok = plt.Line2D([0], [0], marker="*", color="tab:green", lw=0, markersize=8)
    h_done_ng = plt.Line2D([0], [0], marker="x", color="red", lw=0, markersize=7)
    h_vline_ok = plt.Line2D([0], [0], color="tab:green", lw=1.1, linestyle=":")
    h_vline_ng = plt.Line2D([0], [0], color="red", lw=1.1, linestyle=":")

    handles += [
        (h_to, "TIMEOUT_MSG"), (h_proc, "TIMEOUT_PROC"),
        (h_retry, "RETRY"),
        (h_done_ok, "SLAC_DONE_OK ★"), (h_done_ng, "SLAC_DONE_FAIL x"),
        (h_vline_ok, "DONE LINE OK"), (h_vline_ng, "DONE LINE FAIL"),
    ]

    ax.legend([h for h,_ in handles], [n for _,n in handles],
              loc="upper right", ncol=1, frameon=True)
    ax.set_xlabel("Time (s)")
    ax.grid(True, which="both", axis="x", alpha=0.35, linewidth=0.5)
    ax.set_ylim(y_all - 0.8, max(y_base.values()) + 0.8 if y_base else 1.0)
    fig.tight_layout()
    out_png = os.path.join(out_dir, filename)
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
    return True
