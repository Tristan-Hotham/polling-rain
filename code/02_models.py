"""Step 2: every pre-specified model (NOTES.md plan) and the exploratory extras, written to data/models.json.
Estimator: OLS with high-dimensional fixed effects (pyfixest). Main inference: two-way clustering by seat lineage and by
election x region; plus a wild cluster bootstrap by election and randomisation inference that swaps whole national
rain maps between elections."""
import warnings
import numpy as np
import pandas as pd
import pyfixest as pf
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(SEED)
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
D = P[P.insample].copy()
D["elreg"] = D.election + "|" + D.region
D["elnat"] = D.election + "|" + D.nation
for c in ("rain", "rain_0722", "rain_day", "rain_eve", "rain_before", "rain_after", "rain50"):
    D[c + "_cm"] = D[c] / 10
D["r1"] = (D.rain >= 1).astype(int); D["r5"] = (D.rain >= 5).astype(int); D["r10"] = (D.rain >= 10).astype(int)
D["lrain"] = np.log1p(D.rain)
D["post01"] = (D.year >= 2001).astype(int)
D["marg10"] = (D.margin_prev < 10).astype(float); D.loc[D.margin_prev.isna(), "marg10"] = np.nan
D["temp10"] = D.temp / 10; D["temp10sq"] = D.temp10 ** 2
D["dturn"] = D.turnout - D.turnout_prev; D["drain_cm"] = (D.rain - D.rain_prev) / 10
M = {}
CL = {"CRV1": "seat+elreg"}


def fit(name, fml, data=None, vcov=CL, term="rain_cm", label=None, extra=None):
    d = D if data is None else data
    f = pf.feols(fml, data=d, vcov=vcov)
    t = f.tidy()
    out = dict(label=label or name, fml=fml, n=int(f._N), terms={})
    for k in t.index:
        r = t.loc[k]
        out["terms"][k] = dict(b=float(r["Estimate"]), se=float(r["Std. Error"]), lo=float(r["2.5%"]), hi=float(r["97.5%"]), p=float(r["Pr(>|t|)"]))
    if term in out["terms"]:
        out.update(out["terms"][term])
    if extra: out.update(extra)
    M[name] = out
    return f


# ---------------- descriptives of the exposure ----------------
D["rain_dm"] = D.rain - D.groupby("election").rain.transform("mean")
M["desc"] = dict(n=len(D), seats=int(D.seat.nunique()), elections=int(D.election.nunique()), clusters_elreg=int(D.elreg.nunique()),
                 rain_mean=float(D.rain.mean()), rain_median=float(D.rain.median()), rain_sd=float(D.rain.std()),
                 rain_sd_within=float(D.rain_dm.std()), share_1mm=100 * float(D.r1.mean()), share_5mm=100 * float(D.r5.mean()),
                 share_10mm=100 * float(D.r10.mean()), turnout_mean=float(D.turnout.mean()), turnout_sd=float(D.turnout.std()),
                 by_election={e: dict(rain=float(g.rain.mean()), rain_sd=float(g.rain.std()), rain_max=float(g.rain.max()), wet5=100 * float(g.r5.mean()),
                                      turnout=float(g.turnout.mean()), temp=float(g.temp.mean()), n=len(g), hrs=g.hrs.iloc[0])
                              for e, g in D.groupby("election")})

# ---------------- H1 main and alternative specifications ----------------
fit("main", "turnout ~ rain_cm | seat + election", label="Main: seat and election FE")
fit("sp_seatperiod", "turnout ~ rain_cm | seat_period + election", label="Seat x boundary period FE")
fit("sp_elreg", "turnout ~ rain_cm | seat + elreg", label="Election x region FE")
fit("sp_elnat", "turnout ~ rain_cm | seat + elnat", label="Election x nation FE")
fit("sp_temp", "turnout ~ rain_cm + temp10 + temp10sq | seat + election", label="Adding temperature and its square")
fit("sp_noseat", "turnout ~ rain_cm | region + election", label="Region FE instead of seat FE")
fit("sp_cl_elreg", "turnout ~ rain_cm | seat + election", vcov={"CRV1": "elreg"}, label="SE clustered by election x region only")
fit("sp_cl_elec", "turnout ~ rain_cm | seat + election", vcov={"CRV1": "election"}, label="SE clustered by election only")
FD = D[(D.same_bounds == 1) & D.dturn.notna() & D.drain_cm.notna()].copy()
fit("sp_fd", "dturn ~ drain_cm | election", data=FD, term="drain_cm", label="First differences, unchanged seats")
fit("temp", "turnout ~ rain_cm + temp10 | seat + election", term="temp10", label="Temperature, per 10 degrees C (with rain)")

# ---------------- measurement ----------------
fit("m_0722", "turnout ~ rain_0722_cm | seat + election", term="rain_0722_cm", label="07 to 22 hours for every election")
fit("m_day", "turnout ~ rain_day_cm | seat + election", term="rain_day_cm", label="Whole polling day (00 to 24)")
fit("m_eve", "turnout ~ rain_eve_cm | seat + election", term="rain_eve_cm", label="Evening only (16 to 22)")
fit("m_50km", "turnout ~ rain50_cm | seat + election", term="rain50_cm", label="Mean of cells within 50 km")
fit("m_log", "turnout ~ lrain | seat + election", term="lrain", label="log(1 + mm)")
for k, lab in (("r1", "At least 1 mm (indicator)"), ("r5", "At least 5 mm (indicator)"), ("r10", "At least 10 mm (indicator)")):
    fit(f"m_{k}", f"turnout ~ {k} | seat + election", term=k, label=lab)
fit("m_bins", "turnout ~ r1 + r5 + r10 | seat + election", term="r10", label="Thresholds together")

# ---------------- placebos ----------------
fit("pl_before", "turnout ~ rain_before_cm | seat + election", term="rain_before_cm", label="Placebo: day before, alone")
fit("pl_after", "turnout ~ rain_after_cm | seat + election", term="rain_after_cm", label="Placebo: day after, alone")
fit("pl_joint", "turnout ~ rain_cm + rain_before_cm + rain_after_cm | seat + election", label="Polling day with both placebo days")
# correlation of rain across days (within election), to read the alone-placebos
M["desc"]["corr_before"] = float(np.corrcoef(D.rain_dm, D.rain_before - D.groupby("election").rain_before.transform("mean"))[0, 1])
M["desc"]["corr_after"] = float(np.corrcoef(D.rain_dm, D.rain_after - D.groupby("election").rain_after.transform("mean"))[0, 1])

# ---------------- leave one out ----------------
for e in ELECTIONS:
    fit(f"loo_e_{e}", "turnout ~ rain_cm | seat + election", data=D[D.election != e], label=f"Without {e}")
for r in REGIONS:
    fit(f"loo_r_{r}", "turnout ~ rain_cm | seat + election", data=D[D.region != r], label=f"Without {r}")
fit("drop1945", "turnout ~ rain_cm | seat + election", data=D[D.election != "1945"], label="Without 1945")
fit("dropNI", "turnout ~ rain_cm | seat + election", data=D[D.nation != "Northern Ireland"], label="Great Britain only")
fit("drop1719", "turnout ~ rain_cm | seat + election", data=D[~D.election.isin(["2017", "2019"])], label="Without 2017 and 2019")

# ---------------- heterogeneity ----------------
fit("h_post01", "turnout ~ rain_cm + rain_cm:post01 | seat + election", term="rain_cm:post01", label="Rain x 2001 on (postal votes on demand)")
fit("h_pre", "turnout ~ rain_cm | seat + election", data=D[D.year < 2001], label="1945 to 1997")
fit("h_post", "turnout ~ rain_cm | seat + election", data=D[D.year >= 2001], label="2001 to 2024")
for n in ("England", "Scotland", "Wales", "Northern Ireland"):
    fit(f"h_nat_{n}", "turnout ~ rain_cm | seat + election", data=D[D.nation == n], label=n)
fit("h_urban", "turnout ~ rain_cm + rain_cm:urban + urban | seat + election", term="rain_cm:urban", label="Rain x urban (crowded) seat")
fit("h_urb1", "turnout ~ rain_cm | seat + election", data=D[D.urban == 1], label="Urban (crowded) seats")
fit("h_urb0", "turnout ~ rain_cm | seat + election", data=D[D.urban == 0], label="Less crowded seats")
DM = D[D.marg10.notna()]
fit("h_marg", "turnout ~ rain_cm + rain_cm:marg10 + marg10 | seat + election", data=DM, term="rain_cm:marg10", label="Rain x marginal (previous margin under 10 points)")
fit("h_marg1", "turnout ~ rain_cm | seat + election", data=DM[DM.marg10 == 1], label="Marginal seats")
fit("h_marg0", "turnout ~ rain_cm | seat + election", data=DM[DM.marg10 == 0], label="Safer seats")

# ---------------- partisan (GB, single-member) ----------------
G = D[(D.nation != "Northern Ireland") & (D.seats == 1)]
for f, lab in (("con", "Conservative share"), ("lab", "Labour share"), ("lib", "Liberal family share")):
    g = G[G[f].notna()]
    fit(f"party_{f}", f"{f} ~ rain_cm | seat + election", data=g, label=lab)
    fit(f"party_{f}_elreg", f"{f} ~ rain_cm | seat + elreg", data=g, label=lab + ", election x region FE")
    fit(f"party_{f}_pre", f"{f} ~ rain_cm | seat + election", data=g[g.year < 2001], label=lab + ", 1945 to 1997")
G2 = G[G.con.notna() & G.lab.notna()].copy(); G2["clgap"] = G2.con - G2.lab
fit("party_gap", "clgap ~ rain_cm | seat + election", data=G2, label="Conservative minus Labour share")

# ---------------- inference with few elections ----------------
g1 = pd.factorize(D.seat)[0]; g2 = pd.factorize(D.election)[0]


def demean2(v, tol=1e-11):
    v = np.asarray(v, float).copy()
    c1 = np.bincount(g1); c2 = np.bincount(g2)
    for _ in range(5000):
        v -= (np.bincount(g1, weights=v) / c1)[g1]
        m2 = (np.bincount(g2, weights=v) / c2)[g2]; v -= m2
        if np.abs(m2).max() < tol: break
    return v


X = demean2(D.rain_cm.values); Y = demean2(D.turnout.values)
cl = D.election.values
b_hat = float((X @ Y) / (X @ X))
assert abs(b_hat - M["main"]["b"]) < 1e-6, (b_hat, M["main"]["b"])
G_ = pd.factorize(cl)[0]; ng = G_.max() + 1


def crse(x, u):
    s = np.bincount(G_, weights=x * u, minlength=ng)
    return np.sqrt((s @ s) / (x @ x) ** 2 * ng / (ng - 1))


u_hat = Y - b_hat * X
t_hat = b_hat / crse(X, u_hat)
# wild cluster restricted bootstrap (null b = 0 imposed: restricted residuals are Y itself), Webb six-point weights
webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])
B = 9999; ts = np.empty(B)
for i in range(B):
    w = webb[rng.integers(0, 6, ng)][G_]
    ys = Y * w; bs = (X @ ys) / (X @ X); ts[i] = bs / crse(X, ys - bs * X)
M["wild"] = dict(t=float(t_hat), p=float((np.abs(ts) >= abs(t_hat)).mean()), draws=B, clusters=int(ng), weights="Webb six-point",
                 se_cl_election=float(crse(X, u_hat)))

# randomisation inference: give every seat the rain its cell had on another election's polling day (same hours as its
# own election), permuting whole national maps between elections
Wj = jload(W)
dates = {e: D[D.election == e].date.iloc[0] for e in ELECTIONS}
E = D.election.values; Cc = D.cell.values
hrs = {e: hours(e) for e in ELECTIONS}
cache = {}
def rain_on(cell, src, e):
    k = (cell, src, e)
    if k not in cache:
        s, en = hrs[e]; cache[k] = sum(Wj[f"{dates[src]}|{cell}"]["p"][25 + s:25 + en]) / 10
    return cache[k]
NP = 1000; bs = np.empty(NP)
for i in range(NP):
    perm = dict(zip(ELECTIONS, rng.permutation(ELECTIONS)))
    xd = demean2([rain_on(c, perm[e], e) for c, e in zip(Cc, E)])   # permuted rain, FE partialled out
    bs[i] = (xd @ Y) / (xd @ xd)
M["ri"] = dict(p=float((np.abs(bs) >= abs(b_hat)).mean()), draws=NP, mean=float(bs.mean()), sd=float(bs.std()),
               q025=float(np.quantile(bs, 0.025)), q975=float(np.quantile(bs, 0.975)), b=b_hat)
np.savetxt(f"{DATA}/ri_draws.csv", bs, fmt="%.6f", header="b_permuted", comments="")

# ---------------- exploratory checks added at independent review (not in the plan) ----------------
rng2 = np.random.default_rng(SEED + 1)


def demean_fe(v, ga, gb, tol=1e-11):
    v = np.asarray(v, float).copy(); ca = np.bincount(ga); cb = np.bincount(gb)
    for _ in range(5000):
        v -= (np.bincount(ga, weights=v) / ca)[ga]
        m = (np.bincount(gb, weights=v) / cb)[gb]; v -= m
        if np.abs(m).max() < tol: break
    return v


def wild_p(x, y, weights, B=9999):
    """Restricted wild cluster bootstrap by election (null b = 0), x and y already partialled on the fixed effects."""
    b = (x @ y) / (x @ x); t0 = b / crse(x, y - b * x); tt = np.empty(B)
    for i in range(B):
        w = weights[rng2.integers(0, len(weights), ng)][G_]
        ys = y * w; bs_ = (x @ ys) / (x @ x); tt[i] = bs_ / crse(x, ys - bs_ * x)
    return float((np.abs(tt) >= abs(t0)).mean())


rad = np.array([-1.0, 1.0])
M["rev_wild_rad"] = dict(p=wild_p(X, Y, rad), draws=9999, weights="Rademacher", label="Wild bootstrap by election, Rademacher weights (planned)")
Xb = demean2(D.rain_before_cm.values)
M["rev_wild_before"] = dict(p=wild_p(Xb, Y, webb), b=float((Xb @ Y) / (Xb @ Xb)), label="Day-before placebo, wild bootstrap by election (Webb)")
ger = pd.factorize(D.elreg)[0]
Xr = demean_fe(D.rain_cm.values, g1, ger); Yr = demean_fe(D.turnout.values, g1, ger)
M["rev_wild_elreg"] = dict(p=wild_p(Xr, Yr, webb), b=float((Xr @ Yr) / (Xr @ Xr)), label="Election x region FE, wild bootstrap by election (Webb)")
# randomisation inference for the day-before placebo: the same map swaps, applied to the day before
cacheb = {}
def before_on(cell, src, e):
    k = (cell, src, e)
    if k not in cacheb:
        s, en = hrs[e]; cacheb[k] = sum(Wj[f"{dates[src]}|{cell}"]["p"][1 + s:1 + en]) / 10
    return cacheb[k]
bb = np.empty(NP); b_before = float((Xb @ Y) / (Xb @ Xb))
for i in range(NP):
    perm = dict(zip(ELECTIONS, rng2.permutation(ELECTIONS)))
    xd = demean2([before_on(c, perm[e], e) for c, e in zip(Cc, E)]); bb[i] = (xd @ Y) / (xd @ xd)
M["rev_ri_before"] = dict(p=float((np.abs(bb) >= abs(b_before)).mean()), draws=NP, b=b_before, label="Day-before placebo, randomisation inference")
# one observation per grid cell and election (seats sharing a cell share their rain): cell-mean turnout on cell rain
CE = D.groupby(["cell", "election"]).agg(turnout=("turnout", "mean"), rain_cm=("rain_cm", "first"), region=("region", "first"), k=("turnout", "size")).reset_index()
CE["elreg"] = CE.election + "|" + CE.region
fit("rev_cell", "turnout ~ rain_cm | cell + election", data=CE, vcov={"CRV1": "cell+elreg"}, label="One row per grid cell and election (cell and election FE)")
M["rev_cell"]["cells"] = int(CE.cell.nunique())
del Wj, cache, cacheb

# ---------------- binned scatter for the figure (residualised on FE) ----------------
xr = X; yr = Y
q = pd.qcut(pd.Series(xr).rank(method="first"), 20, labels=False)
M["binscatter"] = [dict(x=float(xr[q == k].mean() * 10), y=float(yr[q == k].mean()), n=int((q == k).sum())) for k in range(20)]
M["samples"] = dict(main=M["main"]["n"], fd=M["sp_fd"]["n"], gb_single=len(G), con=int(G.con.notna().sum()), lab=int(G.lab.notna().sum()),
                    lib=int(G.lib.notna().sum()), marg=len(DM), singletons=int(len(D) - M["main"]["n"]))
jsave(M, f"{DATA}/models.json", indent=1, keepdash=True)
for k in ("main", "sp_seatperiod", "sp_elreg", "sp_elnat", "sp_temp", "sp_fd", "sp_noseat", "m_day", "m_50km", "m_r5", "m_r10",
          "pl_before", "pl_after", "pl_joint", "h_post01", "h_pre", "h_post", "h_urban", "h_marg", "party_con", "party_lab", "party_lib", "temp"):
    m = M[k]; print(f"{k:16s} {m['b']:+.3f} [{m['lo']:+.3f}, {m['hi']:+.3f}] p={m['p']:.3f} n={m['n']}")
print("wild", M["wild"]); print({k: M[k] for k in M if k.startswith("rev_")}); print("ri", {k: v for k, v in M["ri"].items()})
