import pandas as pd, re
from io import StringIO

SCA = "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_fakewired/src/dataPostProcessing/data/all_scalars.csv"
VEC = "/home/kimdawoon/study/workspace/research/project_smartCharging_macLayer_improvement/csma_ca_fakewired/src/dataPostProcessing/data/all_vectors.csv"

def read_scavetool_csv(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    header_idx = next((i for i,l in enumerate(lines)
                       if l.strip().startswith("run,") and ",module," in l and ",name," in l), 0)
    return pd.read_csv(StringIO("".join(lines[header_idx:])),
                       engine="python", on_bad_lines="skip")

pat = re.compile(r"(retry|retrans|noack|drop|collision|cw|contentionwindow|backoff)", re.I)

sca = read_scavetool_csv(SCA)
vec = read_scavetool_csv(VEC)

# --- 스칼라: 이름별 합계 ---
sca_hits = sca[sca["name"].astype(str).str.contains(pat, na=False)].copy()
sca_hits["value"] = pd.to_numeric(sca_hits.get("value"), errors="coerce")
print("\n[SCALARS] hits:", len(sca_hits), "unique names:", sca_hits["name"].nunique())
print(sca_hits.groupby("name")["value"].sum(min_count=1)
      .sort_values(ascending=False).head(40))

# --- 벡터: 이름별 row 수(존재 확인용) ---
vec_hits = vec[vec["name"].astype(str).str.contains(pat, na=False)]
print("\n[VECTORS] hits:", len(vec_hits), "unique names:", vec_hits["name"].nunique())
print(vec_hits.groupby("name").size().sort_values(ascending=False).head(40))
