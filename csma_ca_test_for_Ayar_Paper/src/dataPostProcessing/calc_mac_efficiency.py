#!/usr/bin/env python3
"""
calc_mac_efficiency.py  (rev.7) – 슬롯 기반 MAC 효율
η = ns / (ns + nc + ni)
"""

from pathlib import Path
import re, argparse, sys, pandas as pd, matplotlib.pyplot as plt

RESULTS_DIR = Path("/home/kimdawoon/study/workspace/research/"
                   "project_smartCharging_macLayer_improvement/"
                   "csma_ca_test_for_Ayar_Paper/ini/results")

def parse_sca(fp: Path):
    rows = []
    keep = ("ns_success_slots", "nc_collision_slots", "ni_idle_slots")
    with fp.open() as f:
        for line in f:
            if not line.startswith("scalar"): continue
            _, mod, name, val = line.split(maxsplit=3)
            if ".host[0]." in mod: continue        # sink 제외
            if name in keep:
                rows.append({"module": mod,
                             "scalar": name,
                             "value": float(val)})
    df = pd.DataFrame(rows)
    piv = df.pivot(index="module", columns="scalar",
                   values="value").reset_index()

    ns = piv["ns_success_slots"].sum()
    nc = piv["nc_collision_slots"].sum()
    ni = piv["ni_idle_slots"].iloc[0]     # 중복 제거

    eta = ns / (ns + nc + ni) if ns else float("nan")
    return piv, ns, nc, ni, eta

def infer_nodes(label, piv):
    m = re.search(r"-n=(\d+)", label)
    return int(m.group(1)) if m else piv["module"].str.extract(
        r"host\[(\d+)\]").astype(int).max()[0]

def collect(dirp):
    sum_, det = [], []
    for sca in sorted(dirp.glob("*.sca")):
        lbl = sca.stem.split("-#")[0]
        piv, ns, nc, ni, eta = parse_sca(sca)
        n = infer_nodes(lbl, piv)
        sum_.append(dict(run=lbl, nodes=n,
                         ns=ns, nc=nc, ni=ni, eta=eta))
        det.append(piv.assign(run=lbl, nodes=n))
    return (pd.DataFrame(sum_).sort_values("nodes"),
            pd.concat(det))

def main():
    sum_df, _ = collect(RESULTS_DIR)
    print("\n=== SLOT-BASED MAC EFFICIENCY ===")
    print(sum_df[["run","nodes","ns","nc","ni","eta"]]
          .to_string(index=False, float_format="%.4f"))

if __name__ == "__main__":
    main()
