"""Step 4: figures for the page (img/*.jpg), blog (release/blog/b_*.png, 1800 px), paper (release/paper/f_*.pdf, vector)
and header.png (1200 x 630). All numbers from data/results.json, data/models.json and data/panel.csv."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from PIL import Image
from pyproj import Transformer
from common import *

for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF, MONO = "Source Serif 4", "IBM Plex Mono"
SEMI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
def fp(size):
    f = SEMI.copy(); f.set_size(size); return f
BG, INK, MUT, RULE, LANDC, SEA = "#FBF8F1", "#22201C", "#6B655B", "#E3DDD0", "#EEEAE0", "#FBF8F1"
RAIN, NEU, WARM = "#2F6FA8", "#8A8478", "#C2410C"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": BG, "figure.facecolor": BG, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.unicode_minus": False, "pdf.fonttype": 42})
IMG, BLOG, PAP = f"{ROOT}/img", f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (IMG, BLOG, PAP):
    os.makedirs(d, exist_ok=True)
R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str}); D = P[P.insample]

# rain classes shared by every map (page, collage, GIF)
BINS = [0, 0.1, 1, 2, 5, 10, 100]
COLS = ["#D9D2C3", "#CFE0EC", "#9CC3E0", "#5E9DCC", "#2B67A3", "#13335F"]
LABS = ["dry (under 0.1 mm)", "0.1 to 1 mm", "1 to 2 mm", "2 to 5 mm", "5 to 10 mm", "10 mm or more"]
CMAP = ListedColormap(COLS); NORM = BoundaryNorm(BINS, CMAP.N)
jsave(dict(bins=BINS, cols=COLS, labs=LABS), f"{DATA}/rain_classes.json", indent=1)
TR = Transformer.from_crs(4326, 27700, always_xy=True)
NAT = jload(f"{ELE}/nations.geojson")
SHAPES = []
for f in NAT["features"]:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for p in polys:
        r = np.array(p[0]); x, y = TR.transform(r[:, 0], r[:, 1]); SHAPES.append((f["properties"]["nation"], np.c_[x, y]))
D = D.copy(); D["x"], D["y"] = TR.transform(D.lon.values, D.lat.values)


def out(fig, name, page=True, blog=True, paper=True):
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    if paper:
        fig.savefig(f"{PAP}/f_{name}.pdf", facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=86, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, s=None, y=0.975, x=0.04):
    fig.text(x, y, t, fontproperties=fp(17), color=INK, va="top")
    if s: fig.text(x, y - 0.05, s, fontsize=11.5, color=MUT, va="top")


def basemap(ax, ireland=True):
    pats = [MPoly(xy, closed=True) for n, xy in SHAPES if ireland or n != "Ireland"]
    ax.add_collection(PatchCollection(pats, facecolor=LANDC, edgecolor="#CFC8B8", linewidth=0.3, zorder=1))
    ax.set_xlim(-90000, 690000); ax.set_ylim(-10000, 1230000); ax.set_aspect("equal"); ax.axis("off")


def seats(ax, d, s=6, col="rain"):
    d = d.sort_values(col)
    ax.scatter(d.x, d.y, c=d[col], cmap=CMAP, norm=NORM, s=s, linewidths=0.25, edgecolors="white", zorder=3, rasterized=False)


def legend_rain(ax_or_fig, loc="center", title_="Rain in polling hours", fontsize=10, **kw):
    h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="#9A9385", markersize=9, label=l) for c, l in zip(COLS, LABS)]
    lg = ax_or_fig.legend(handles=h, loc=loc, frameon=False, fontsize=fontsize, title=title_, title_fontsize=fontsize + 1, **kw)
    lg.get_title().set_fontproperties(fp(fontsize + 1))
    return lg


be = {x["election"]: x for x in R["by_election"]}

# ---------- 1. rain maps, every election ----------
fig = plt.figure(figsize=(12, 13.2))
title(fig, "Rain while the polls were open, every UK general election 1945 to 2024",
      "Each dot is a constituency, coloured by rain at its ERA5 grid cell during polling hours. Mean in brackets.")
for i, e in enumerate(ELECTIONS):
    r, c = divmod(i, 6)
    ax = fig.add_axes([0.02 + c * 0.163, 0.69 - r * 0.215, 0.155, 0.2])
    basemap(ax); seats(ax, D[D.election == e], s=3.2)
    ax.text(0.02, 0.98, ESHORT[e], transform=ax.transAxes, fontproperties=fp(11.5), va="top", color=INK)
    ax.text(0.02, 0.89, f"({be[e]['rain']:.1f} mm)", transform=ax.transAxes, fontsize=9.5, va="top", color=MUT)
lax = fig.add_axes([0.68, 0.045, 0.3, 0.17]); lax.axis("off")
legend_rain(lax, loc="center left", fontsize=10.5)
fig.text(0.04, 0.012, "Data: ERA5 via Open-Meteo (CC BY 4.0); seats and turnout: Who won here? (UK Parliament, House of Commons Library).", fontsize=9, color=MUT)
out(fig, "maps")

# ---------- 2. rain and turnout by election ----------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.2), sharex=True, gridspec_kw=dict(hspace=0.12))
fig.subplots_adjust(top=0.84, left=0.08, right=0.97, bottom=0.12)
title(fig, "Wet and dry polling days, and turnout", "Top: mean rain in polling hours across seats (bar), wettest seat (dot). Bottom: mean turnout across contested seats.")
xs = np.arange(len(ELECTIONS))
a1.bar(xs, [be[e]["rain"] for e in ELECTIONS], color=RAIN, width=0.7)
a1.plot(xs, [be[e]["rain_max"] for e in ELECTIONS], "o", color="#13335F", ms=4.5)
a1.set_ylabel("mm in polling hours"); a1.grid(axis="y", color=RULE, lw=0.6); a1.set_axisbelow(True)
a2.plot(xs, [be[e]["turnout"] for e in ELECTIONS], "-o", color=INK, ms=4, lw=1.6)
a2.set_ylabel("turnout, %"); a2.grid(axis="y", color=RULE, lw=0.6); a2.set_axisbelow(True)
a2.set_xticks(xs); a2.set_xticklabels([ESHORT[e].replace("Feb ", "F").replace("Oct ", "O") for e in ELECTIONS], rotation=90, fontsize=10)
a2.axvline(xs[ELECTIONS.index("2001")] - 0.5, color=MUT, lw=1, ls=(0, (4, 3)))
a2.text(xs[ELECTIONS.index("2001")] - 0.35, 79, "postal votes on\ndemand from 2001", fontsize=9.5, color=MUT, va="bottom")
out(fig, "time")

# ---------- 3. binned scatter ----------
bs = M["binscatter"]
fig, ax = plt.subplots(figsize=(9.5, 6.4)); fig.subplots_adjust(top=0.83, left=0.11, right=0.96, bottom=0.12)
title(fig, "Wetter than usual, turnout slightly lower than usual",
      f"Turnout and rain after removing each seat's average and each election's average; 20 equal bins of {M['main']['n']:,} contests.")
x = np.array([b["x"] for b in bs]); y = np.array([b["y"] for b in bs])
ax.axhline(0, color=RULE, lw=1); ax.axvline(0, color=RULE, lw=1)
ax.plot(x, y, "o", color=RAIN, ms=8, mec=BG, mew=1.2, zorder=3)
xx = np.linspace(x.min() - 0.3, x.max() + 0.3, 50); ax.plot(xx, T["b_mm"] * xx, color=WARM, lw=2)
ax.set_xlabel("rain in polling hours, mm above (or below) what the seat and election would lead you to expect")
ax.set_ylabel("turnout, points above or below expected")
ax.text(0.98, 0.94, f"slope {T['b_mm']:.2f} points per mm\n(95% CI {T['lo_mm']:.2f} to {T['hi_mm']:.2f}, two-way clustered)", transform=ax.transAxes,
        ha="right", va="top", fontsize=11, color=WARM)
ax.set_ylim(-1.2, 1.2)
out(fig, "bins")

# ---------- 4. randomisation inference ----------
dr = np.loadtxt(f"{DATA}/ri_draws.csv", skiprows=1)
fig, ax = plt.subplots(figsize=(9.5, 5.8)); fig.subplots_adjust(top=0.76, left=0.09, right=0.96, bottom=0.14)
title(fig, "How unusual is the real estimate? Swapping whole rain maps between elections",
      f"{len(dr):,} reshuffles: each election gets another polling day's rain map.\nGrey: estimates from reshuffled weather; orange: the real one.")
ax.hist(dr, bins=45, color="#C9C2B2", edgecolor=BG)
ax.axvline(T["b"], color=WARM, lw=2.5)
ax.text(T["b"] - 0.05, ax.get_ylim()[1] * 0.92, f"real: {T['b']:.2f}", color=WARM, ha="right", fontsize=11.5)
ax.text(0.98, 0.93, f"{T['ri_share_beyond']:.1f}% of reshuffles at least as far from zero\n(randomisation p = {T['ri_p']:.2f}; wild bootstrap by election p = {T['wild_p']:.2f})",
        transform=ax.transAxes, ha="right", va="top", fontsize=10.5, color=INK)
ax.set_xlabel("estimated change in turnout per cm of polling-hours rain (points)"); ax.set_yticks([])
ax.spines["left"].set_visible(False)
out(fig, "ri")


# ---------- 5. robustness coefficient plot ----------
def coefplot(ax, rows, xlab, xlim=None):
    y = np.arange(len(rows))[::-1]
    for yy, (lab, k, sty) in zip(y, rows):
        if k is None:
            ax.text(0.0, yy, lab, transform=ax.get_yaxis_transform(), ha="right", fontproperties=fp(10.5), color=INK, va="center")
            continue
        m = M[k]; c = {"main": WARM, "plac": NEU}.get(sty, RAIN)
        ax.plot([m["lo"], m["hi"]], [yy, yy], color=c, lw=2.2, solid_capstyle="round")
        ax.plot(m["b"], yy, "o", ms=8 if sty == "main" else 6.5, color=c, mec=BG, mew=1.4, zorder=3)
    ax.set_yticks([yy for yy, r in zip(y, rows) if r[1] is not None]); ax.set_yticklabels([r[0] for r in rows if r[1] is not None], fontsize=10.5)
    ax.axvline(0, color=MUT, lw=1, ls=(0, (4, 3)), zorder=0); ax.set_xlabel(xlab); ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True)
    if xlim: ax.set_xlim(*xlim)
    ax.tick_params(axis="y", length=0)


rows = [("Main: seat and election FE, two-way clusters", "main", "main"),
        ("Seat x boundary period FE", "sp_seatperiod", ""), ("Election x region FE", "sp_elreg", ""), ("Election x nation FE", "sp_elnat", ""),
        ("Adding temperature", "sp_temp", ""), ("Region FE instead of seat FE", "sp_noseat", ""), ("First differences, unchanged seats", "sp_fd", ""),
        ("Clustered by election only", "sp_cl_elec", ""),
        ("Hours 07 to 22 for every election", "m_0722", ""), ("Whole polling day", "m_day", ""), ("Evening only, 16 to 22", "m_eve", ""),
        ("Mean of cells within 50 km", "m_50km", ""),
        ("Without 1945", "drop1945", ""), ("Great Britain only", "dropNI", ""), ("Without 2017 and 2019", "drop1719", ""),
        ("Placebo: rain the day before", "pl_before", "plac"), ("Placebo: rain the day after", "pl_after", "plac")]
fig, ax = plt.subplots(figsize=(10, 8.2)); fig.subplots_adjust(top=0.88, left=0.39, right=0.97, bottom=0.08)
title(fig, "The estimate under other choices", "Change in turnout (points) per cm of rain, with 95% confidence intervals. Grey: placebo days.", x=0.03)
coefplot(ax, rows, "points of turnout per cm of rain")
out(fig, "robust")

# ---------- 6. leave one out ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 7.4), gridspec_kw=dict(width_ratios=[1, 1], wspace=0.55)); fig.subplots_adjust(top=0.86, left=0.13, right=0.98, bottom=0.09)
title(fig, "Leaving out one election or one region at a time", "Points of turnout per cm of rain, 95% confidence intervals; the vertical line marks the main estimate.", x=0.03)
coefplot(a1, [(f"without {ESHORT[e]}", f"loo_e_{e}", "") for e in ELECTIONS], "per cm")
coefplot(a2, [(f"without {r.replace('Yorkshire and The Humber', 'Yorkshire & Humber')}", f"loo_r_{r}", "") for r in REGIONS], "per cm")
for a in (a1, a2):
    a.axvline(T["b"], color=WARM, lw=1)
    for lab in a.get_yticklabels(): lab.set_fontsize(9.5)
out(fig, "loo", blog=False)

# ---------- 7. heterogeneity and party shares ----------
rows = [("Turnout", None, ""), ("1945 to 1997", "h_pre", ""), ("2001 to 2024 (postal votes on demand)", "h_post", ""),
        ("England", "h_nat_England", ""), ("Scotland", "h_nat_Scotland", ""), ("Wales", "h_nat_Wales", ""),
        ("More crowded (urban) seats", "h_urb1", ""), ("Less crowded seats", "h_urb0", ""),
        ("Marginal (previous margin under 10)", "h_marg1", ""), ("Safer seats", "h_marg0", ""),
        ("Vote share (Great Britain)", None, ""), ("Conservative share", "party_con", "main"), ("Labour share", "party_lab", "main"), ("Liberal family share", "party_lib", "")]
fig, ax = plt.subplots(figsize=(10, 7.6)); fig.subplots_adjust(top=0.88, left=0.39, right=0.97, bottom=0.09)
title(fig, "Where and for whom?", "Separate regressions; points per cm of polling-hours rain with 95% confidence intervals. Northern Ireland (few seats) in the tables.", x=0.03)
coefplot(ax, rows, "points per cm of rain")
out(fig, "het")

# ---------- header.png 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(BG)
ax = fig.add_axes([0.6, 0.03, 0.38, 0.94]); basemap(ax); seats(ax, D[D.election == "2019"], s=14)
ax.text(0.02, 0.97, "12 December 2019", transform=ax.transAxes, fontproperties=fp(13), va="top", color=INK)
ax.text(0.02, 0.92, "rain while polls were open", transform=ax.transAxes, fontsize=11, va="top", color=MUT)
fig.text(0.05, 0.86, "DATA STUDY · 1945 TO 2024", fontname=MONO, fontsize=12, color=MUT)
fig.text(0.05, 0.78, "Does rain keep\nBritain at home?", fontproperties=fp(46), color=INK, va="top", linespacing=1.0)
fig.text(0.05, 0.42, f"22 general elections, {T['b']:.1f} points of turnout\nper cm of rain, and not quite\nsure it is real", fontsize=19, color=RAIN, va="top", linespacing=1.25)
fig.text(0.05, 0.08, "Dr Tristan Hotham · maps.tristanhotham.com/polling-rain", fontname=MONO, fontsize=11.5, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=BG)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
