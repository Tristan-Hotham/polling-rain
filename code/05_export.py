"""Step 5: compact files for the page: data/site/seats.json (every contest 1945 to 2024 with rain, turnout and winner) and
data/site/hours.json (hourly rain on each polling day for every grid cell used, loaded when a popup opens)."""
import numpy as np
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
Wd = jload(W)
os.makedirs(f"{DATA}/site", exist_ok=True)
cells = sorted(P.cell.unique()); cid = {c: i for i, c in enumerate(cells)}
FAMS = ["CON", "LAB", "LIB", "SNP", "PC", "ULS", "IRN", "SF", "SPK", "OTH", "GRN", "REF", "ALLY"]
fi = {f: i for i, f in enumerate(FAMS)}
rows = []
for r in P.itertuples():
    rows.append([int(r.eidx), r.constituency, round(r.lon, 4), round(r.lat, 4), int(round(r.rain * 10)),
                 None if pd.isna(r.turnout) else int(round(r.turnout * 10)), int(round(r.temp * 10)),
                 fi.get(r.winner, fi["OTH"]) if isinstance(r.winner, str) else -1, cid[r.cell],
                 None if pd.isna(r.turnout_prev) else int(round(r.turnout_prev * 10)), int(round(r.rain_day * 10)),
                 0 if r.insample else (1 if r.postponed else 2 if r.univ else 3)])
el = [dict(e=x["election"], s=x["short"], date=P[P.election == x["election"]].date.iloc[0], hrs=x["hrs"], rain=round(x["rain"], 2),
           wet5=round(x["wet5"], 1), turnout=round(x["turnout"], 1), n=x["n"]) for x in R["by_election"]]
main = dict(b=round(T["b"], 2), lo=round(T["lo"], 2), hi=round(T["hi"], 2), wild=round(T["wild_p"], 2), ri=round(T["ri_p"], 2))
cls = jload(f"{DATA}/rain_classes.json")
jsave(dict(elections=el, fams=FAMS, cells=[[float(c.split(",")[0]), float(c.split(",")[1])] for c in cells], rows=rows, main=main, classes=cls),
      f"{DATA}/site/seats.json")
H = {}
for e in ELECTIONS:
    d = P[P.election == e].date.iloc[0]
    for c in P[P.election == e].cell.unique():
        H[f"{EIDX[e]}|{cid[c]}"] = [int(round(v * 10)) for v in Wd[f"{d}|{c}"]["p"][25:49]]
jsave(H, f"{DATA}/site/hours.json")
print({f: os.path.getsize(f"{DATA}/site/{f}") // 1024 for f in os.listdir(f"{DATA}/site")}, "KB")
