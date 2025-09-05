# hpgp_sim/plot_slac.py
# ---------------------
# SLAC 5종 메시지를 색으로 구분한 간트 타임라인 (노드별 + 하단 ALL 오버레이)
# - 입력: out_dir/tx_log.csv, debug.csv
# - 출력: out_dir/slac_timeline.png
# - sim_time_us 인자를 주면 x축을 [0, sim_time]으로 고정

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

_NODE_PATTERNS = [
    re.compile(r"node\s*[:=]\s*'?([A-Za-z0-9_]+)"),
    re.compile(r"'node'\s*:\s*'([A-Za-z0-9_]+)'"),
    re.compile(r'"node"\s*:\s*"([A-Za-z0-9_]+)"'),
    re.compile(r"'node'\s*:\s*([A-Za-z0-9_]+)"),
    re.compile(r'"node"\s*:\s*([A-Za-z0-9_]+)'),
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

    # debug 이벤트(타임아웃/재시작)
    events = []
    if os.path.exists(dbg_csv):
        with open(dbg_csv, newline="", encoding="utf-8") as f:
            rdr = csv.reader(f); _ = next(rdr, None)
            for r in rdr:
                try:
                    t_us = int(r[0]); tag = (r[1] or "").strip().upper()
                    kv   = r[2] if len(r) > 2 else ""
                    if tag in ("SLAC_TIMEOUT_MSG", "SLAC_TIMEOUT_PROC", "SLAC_RETRY"):
                        node = _parse_node_from_kv(kv)
                        events.append((t_us, tag, node))
                except Exception:
                    continue

    # 노드 목록
    nodes = sorted({n for _,_,n,_ in tx_rows})

    # 시간 범위: 기본은 데이터범위, sim_time_us 있으면 [0, sim_time] 고정
    if sim_time_us is not None:
        t_min = 0
        t_max = int(sim_time_us)
    else:
        t_min = min(s for s,_,_,_ in tx_rows)
        t_max = max(e for _,e,_,_ in tx_rows)
        for t, _, _ in events:
            t_min = min(t_min, t); t_max = max(t_max, t)

    span_s = max(1.0, (t_max - t_min) / 1e6)

    # Figure 스케일 & 최소 표시폭 보장
    h = max(3.5, 0.36 * (len(nodes) + 1) + 1.6)  # +1: ALL 트랙
    fig_w = min(18, 10 + span_s * 0.8)
    fig, ax = plt.subplots(figsize=(fig_w, h))
    ax.set_title("SLAC Timeline (bars = frames on air)")

    # x축 범위
    x_span_data = max(1e-6, (t_max - t_min) / 1e6)
    ax.set_xlim(0, x_span_data)

    # 픽셀→데이터 변환으로 최소 1.5px 너비 보장
    dpi = fig.dpi
    fig_w_in = fig.get_size_inches()[0]
    px_per_data = max(1e-9, dpi * fig_w_in / x_span_data)  # px per second
    min_w_s = 1.5 / px_per_data

    # y축: 맨 아래에 "ALL" 트랙 추가, N0는 "SECC"로 표기
    def _disp_label(n: str) -> str:
        return "SECC" if n.upper() == "N0" else n

    y_all = -1
    y_base = {node: i for i, node in enumerate(nodes)}
    ax.set_yticks([y_all] + [y_base[n] for n in nodes])
    ax.set_yticklabels(["ALL"] + [_disp_label(n) for n in nodes])

    # 간트 바 (테두리 제거 + 최소너비 적용)
    for (s_us, e_us, node, canon) in tx_rows:
        y = y_base[node]
        s = (s_us - t_min) / 1e6
        w = max((e_us - s_us) / 1e6, min_w_s)
        c = COLOR.get(canon, "gray")
        ax.broken_barh([(s, w)], (y - 0.38, 0.76),
                       facecolor=c, edgecolor=c, linewidth=0.0, alpha=0.95)

    # 하단 ALL 트랙(모든 프레임 오버레이)
    for (s_us, e_us, _node, canon) in tx_rows:
        s = (s_us - t_min) / 1e6
        w = max((e_us - s_us) / 1e6, min_w_s)
        c = COLOR.get(canon, "gray")
        ax.broken_barh([(s, w)], (y_all - 0.38, 0.76),
                       facecolor=c, edgecolor=c, linewidth=0.0, alpha=0.95)

    # 이벤트 오버레이
    for (t_us, tag, node) in events:
        x = (t_us - t_min) / 1e6
        if tag == "SLAC_TIMEOUT_PROC":
            ax.axvline(x=x, color="red", linestyle="--", linewidth=1.2, alpha=0.9)
        elif tag == "SLAC_TIMEOUT_MSG":
            y = y_base.get(node, y_all)
            ax.plot([x], [y], marker="v", color="red", markersize=6, linestyle="None")
        elif tag == "SLAC_RETRY":
            y = y_base.get(node, y_all)
            ax.plot([x], [y], marker="D", color="black", markersize=5, linestyle="None")

    # 범례
    handles = []
    for canon, color in COLOR.items():
        hdl = plt.Line2D([0], [0], color=color, lw=8)
        handles.append((hdl, canon.replace("CM_", "")))
    h_to = plt.Line2D([0], [0], marker="v", color="red", lw=0, markersize=6)
    h_proc = plt.Line2D([0], [0], color="red", lw=1.2, linestyle="--")
    h_retry = plt.Line2D([0], [0], marker="D", color="black", lw=0, markersize=5)
    handles += [(h_to, "TIMEOUT_MSG"), (h_proc, "TIMEOUT_PROC"), (h_retry, "RETRY")]

    ax.legend([h for h,_ in handles], [n for _,n in handles], loc="upper right", ncol=1, frameon=True)
    ax.set_xlabel("Time (s)")
    ax.grid(True, which="both", axis="x", alpha=0.35, linewidth=0.5)
    ax.set_ylim(y_all - 0.8, (len(nodes) - 1) + 0.8)
    fig.tight_layout()
    out_png = os.path.join(out_dir, filename)
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
    return True
