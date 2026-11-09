"""Step 1: the seat-election panel (data/panel.csv) and per-cell weather summaries.
One row per contest 1945 to 2024: turnout, Conservative/Labour/Liberal shares, previous margin, region, seat crowding,
and rain/temperature measures for polling hours, the whole day, the day before and the day after."""
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from shapely import STRtree
from common import *

Wd = jload(W)
con = pd.read_csv(f"{ELE}/contests.csv", dtype=str)
con = con[con.election.isin(ELECTIONS)].copy()
cand = pd.read_csv(f"{ELE}/candidates.csv", dtype=str)
cand = cand[cand.election.isin(ELECTIONS)].copy()
for c in ("lat", "lon", "turnout", "votes_cast"):
    con[c] = pd.to_numeric(con[c], errors="coerce")
con["seats"] = con.seats.astype(int); con["uncontested"] = con.uncontested == "True"
st = {"contests_all": len(con)}

# ---- weather key: seat point rounded to the nearest 0.25 degree ----
r4 = lambda v: f"{round(v * 4) / 4:g}"
con["cell"] = con.lat.map(r4) + "," + con.lon.map(r4)
con["key"] = con.date + "|" + con.cell
assert con.key.isin(Wd).all(), con[~con.key.isin(Wd)].key.head()
st["cells"] = int(con.cell.nunique())

S = lambda a, i, j: float(np.sum(a[i:j]))
def wx(row):
    v = Wd[row.key]; p = np.array(v["p"], float); t = np.array(v["t"], float); s, e = hours(row.election)
    assert len(p) == 72 and len(t) == 72 and not np.isnan(p).any()
    return pd.Series(dict(
        rain=S(p, 25 + s, 25 + e), rain_0722=S(p, 32, 47), rain_day=S(p, 25, 49), rain_eve=S(p, 41, 47),
        rain_before=S(p, 1 + s, 1 + e), rain_after=S(p, 49 + s, 49 + e),
        rain_hrs=int((p[25 + s:25 + e] >= 0.1).sum()), rain_max=float(p[25 + s:25 + e].max()),
        temp=float(t[24 + s:25 + e].mean()), tmin=float(t[24 + s:25 + e].min()), glat=v["glat"], glon=v["glon"],
        hrs=f"{s:02d} to {e:02d}"))
con = pd.concat([con, con.apply(wx, axis=1)], axis=1)

# ---- smoother exposure: mean polling-hours rain over all used cells within 50 km of the seat cell ----
cells = {}
for k in Wd:
    d, c = k.split("|"); la, lo = map(float, c.split(",")); cells.setdefault(d, []).append((la, lo, k))
def km(la1, lo1, la2, lo2):
    p1, p2 = np.radians(la1), np.radians(la2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo2 - lo1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))
sm = {}
for e in ELECTIONS:
    dt = con[con.election == e].date.iloc[0]; s, en = hours(e)
    L = cells[dt]; la = np.array([x[0] for x in L]); lo = np.array([x[1] for x in L])
    rr = np.array([sum(Wd[x[2]]["p"][25 + s:25 + en]) for x in L])
    for i, (a, b, k) in enumerate(L):
        sm[k] = float(rr[km(a, b, la, lo) <= 50].mean())
con["rain50"] = con.key.map(sm)

# ---- region of the seat point (ONS regions; nearest region for points offshore) ----
topo = jload(f"{GEO}/uk_topo.json")
def topo_geoms(obj):
    tr = topo.get("transform"); arcs = []
    for a in topo["arcs"]:
        x = y = 0; out = []
        for q in a:
            if tr: x += q[0]; y += q[1]; out.append((x * tr["scale"][0] + tr["translate"][0], y * tr["scale"][1] + tr["translate"][1]))
            else: out.append(tuple(q))
        arcs.append(out)
    def ring(ix):
        pts = []
        for i in ix:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        return pts
    for g in topo["objects"][obj]["geometries"]:
        if g["type"] == "Polygon": geo = {"type": "Polygon", "coordinates": [ring(r) for r in g["arcs"]]}
        elif g["type"] == "MultiPolygon": geo = {"type": "MultiPolygon", "coordinates": [[ring(r) for r in p] for p in g["arcs"]]}
        else: continue
        yield g["properties"]["areanm"], shape(geo).buffer(0)
regs = list(topo_geoms("rgn"))
names = {"Yorkshire and The Humber": "Yorkshire and The Humber"}
for nm, _ in regs:
    assert nm in REGIONS, nm
tree = STRtree([g for _, g in regs])
def region(row):
    if row.nation in ("Scotland", "Wales", "Northern Ireland"): return row.nation
    p = Point(row.lon, row.lat); ix = tree.query(p, predicate="intersects")
    if len(ix): return regs[ix[0]][0]
    return regs[tree.nearest(p)][0]
con["region"] = con.apply(region, axis=1)

# ---- seat lineage, boundary period, crowding ----
con["seat"] = con.constituency.map(norm)
con["period"] = [period(e, n) for e, n in zip(con.election, con.nation)]
con["seat_period"] = con.seat + "|" + con.period
con["eidx"] = con.election.map(EIDX); con["year"] = con.election.str[-4:].astype(int)
crowd = np.zeros(len(con), int)
for e, g in con.groupby("election"):
    la, lo = g.lat.values, g.lon.values
    for j, ix in enumerate(g.index):
        crowd[con.index.get_loc(ix)] = int((km(la[j], lo[j], la, lo) <= 15).sum() - 1)
con["crowd15"] = crowd
con["urban"] = (con.crowd15 > con.groupby("election").crowd15.transform("median")).astype(int)

# ---- party shares and margins ----
cand["share"] = pd.to_numeric(cand.share, errors="coerce"); cand["votes"] = pd.to_numeric(cand.votes, errors="coerce")
fam = cand.groupby(["election", "constituency", "family"]).share.sum().unstack()
for f, col in (("CON", "con"), ("LAB", "lab"), ("LIB", "lib")):
    con[col] = [fam.loc[(e, c), f] if (e, c) in fam.index and f in fam.columns and fam.loc[(e, c), f] > 0 else np.nan
                for e, c in zip(con.election, con.constituency)]
top2 = cand.dropna(subset=["share"]).sort_values("share", ascending=False).groupby(["election", "constituency"]).share.apply(lambda s: list(s)[:2])
con["margin"] = [(lambda t: t[0] - t[1] if len(t) == 2 else np.nan)(top2.get((e, c), [])) for e, c in zip(con.election, con.constituency)]
con.loc[con.seats > 1, "margin"] = np.nan
win = cand[cand.elected == "True"].groupby(["election", "constituency"]).family.first()
con["winner"] = [win.get((e, c)) for e, c in zip(con.election, con.constituency)]
prev = con.set_index(["seat", "eidx"])
def lag(col):
    return [prev[col].get((s, i - 1), np.nan) if (s, i - 1) in prev.index else np.nan for s, i in zip(con.seat, con.eidx)]
con["margin_prev"] = lag("margin")
con["turnout_prev"] = lag("turnout"); con["rain_prev"] = lag("rain")
con["period_prev"] = [prev["period"].get((s, i - 1)) if (s, i - 1) in prev.index else None for s, i in zip(con.seat, con.eidx)]
con["same_bounds"] = (con.period_prev == con.period).astype(int)

# ---- sample flags ----
con["univ"] = con.constituency.str.contains("Universit")
con["postponed"] = (con.election == "1945") & con.constituency.isin(POSTPONED_1945)
assert int(con.postponed.sum()) == len(POSTPONED_1945), int(con.postponed.sum())
con["insample"] = (~con.uncontested) & con.turnout.notna() & (~con.univ) & (~con.postponed)
st.update(contests=len(con), uncontested=int(con.uncontested.sum()), univ=int(con.univ.sum()), postponed=int(con.postponed.sum()),
          no_turnout=int(con.turnout.isna().sum()), sample=int(con.insample.sum()), seats=int(con[con.insample].seat.nunique()),
          seat_periods=int(con[con.insample].seat_period.nunique()), multi=int(((con.seats > 1) & con.insample).sum()),
          fd_pairs=int((con.insample & (con.same_bounds == 1) & con.turnout_prev.notna()).sum()))
cols = ["election", "date", "year", "eidx", "constituency", "seat", "period", "seat_period", "wikidata", "nation", "region", "lat", "lon",
        "cell", "glat", "glon", "seats", "uncontested", "univ", "postponed", "insample", "turnout", "votes_cast", "con", "lab", "lib",
        "winner", "margin", "margin_prev", "turnout_prev", "rain_prev", "same_bounds", "crowd15", "urban", "hrs", "rain", "rain_0722",
        "rain_day", "rain_eve", "rain_before", "rain_after", "rain50", "rain_hrs", "rain_max", "temp", "tmin"]
out = con[cols].sort_values(["eidx", "constituency"])
for c in ("rain", "rain_0722", "rain_day", "rain_eve", "rain_before", "rain_after", "rain50", "rain_max", "temp", "tmin", "rain_prev"):
    out[c] = out[c].round(2)
out.to_csv(f"{DATA}/panel.csv", index=False)
jsave(st, f"{SCR}/stats01.json", indent=1)
print(st); print(out.groupby("region").size())
