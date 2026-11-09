"""Reddit collage for polling-rain (light background, labels on paper, full legend). Run from the study root:
python3 reddit/collage.py  ->  reddit/polling_rain_collage.png. Every number comes from data/results.json."""
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import ELE, FONTS, SCR, jload, ESHORT
for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SEMI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
def fp(s):
    f = SEMI.copy(); f.set_size(s); return f
BG, INK, MUT, RULE, LANDC, RAIN, WARM = "#FBF8F1", "#22201C", "#6B655B", "#E3DDD0", "#EEEAE0", "#2F6FA8", "#C2410C"
plt.rcParams.update({"font.family": "Source Serif 4", "axes.facecolor": BG, "figure.facecolor": BG, "axes.unicode_minus": False,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT})
R = jload(f"{ROOT}/data/results.json"); T = R["T"]; M = R["M"]; C = jload(f"{ROOT}/data/rain_classes.json")
CMAP = ListedColormap(C["cols"]); NORM = BoundaryNorm(C["bins"], CMAP.N)
P = pd.read_csv(f"{ROOT}/data/panel.csv", dtype={"election": str}); P = P[P.insample].copy()
TR = Transformer.from_crs(4326, 27700, always_xy=True)
P["x"], P["y"] = TR.transform(P.lon.values, P.lat.values)
SH = []
for f in jload(f"{ELE}/nations.geojson")["features"]:
    g = f["geometry"]
    for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        r = np.array(p[0]); x, y = TR.transform(r[:, 0], r[:, 1]); SH.append(np.c_[x, y])
be = {x["election"]: x for x in R["by_election"]}


def umap(ax, e, s):
    ax.add_collection(PatchCollection([MPoly(xy) for xy in SH], facecolor=LANDC, edgecolor="#CFC8B8", lw=0.4, zorder=1))
    d = P[P.election == e].sort_values("rain")
    ax.scatter(d.x, d.y, c=d.rain, cmap=CMAP, norm=NORM, s=s, lw=0.35, edgecolors="white", zorder=3)
    ax.set_xlim(-90000, 690000); ax.set_ylim(-10000, 1230000); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(27, 17), dpi=100)
fig.text(0.025, 0.965, "Does rain keep Britain at home?", fontproperties=fp(64), color=INK, va="top")
fig.text(0.025, 0.895, f"Rain while the polls were open at {R['n']['sample']:,} constituency contests, 22 UK general elections 1945 to 2024, and turnout in the same seats",
         fontsize=27, color=MUT, va="top")
# big 2019 map
ax = fig.add_axes([0.0, 0.1, 0.33, 0.72]); umap(ax, "2019", 46)
fig.text(0.025, 0.82, "12 December 2019", fontproperties=fp(32), color=INK, va="top")
fig.text(0.025, 0.79, f"the wettest polling day: {T['wettest_mm']:.1f} mm on average,\n{T['wettest_wet5']:.0f}% of seats had 5 mm or more", fontsize=21, color=MUT, va="top")
# four small maps
for i, e in enumerate(["1950", "1987", "2017", "1997"]):
    r, c = divmod(i, 2)
    a = fig.add_axes([0.33 + c * 0.16, 0.47 - r * 0.36, 0.15, 0.33]); umap(a, e, 13)
    a.text(0.0, 1.02, f"{ESHORT[e]}  ·  {be[e]['rain']:.1f} mm", transform=a.transAxes, fontproperties=fp(23), color=INK)
# legend on paper under the maps
h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="#9A9385", markersize=20, label=l) for c, l in zip(C["cols"], C["labs"])]
lg = fig.legend(handles=h, loc="lower left", bbox_to_anchor=(0.025, 0.035), ncol=6, frameon=False, fontsize=20, title="Rain at the seat's ERA5 grid cell while its polls were open", title_fontsize=21, columnspacing=1.6)
lg._legend_box.align = "left"
# binned scatter
a1 = fig.add_axes([0.69, 0.52, 0.28, 0.24])
bs = M["binscatter"]; x = np.array([b["x"] for b in bs]); y = np.array([b["y"] for b in bs])
a1.axhline(0, color=RULE, lw=1.5); a1.axvline(0, color=RULE, lw=1.5)
a1.plot(x, y, "o", color=RAIN, ms=13, mec=BG, mew=1.5, zorder=3)
xx = np.linspace(x.min() - 0.3, x.max() + 0.3, 20); a1.plot(xx, T["b_mm"] * xx, color=WARM, lw=3)
a1.set_xlabel("rain, mm more than usual for the seat and election", fontsize=18); a1.set_ylabel("turnout vs usual, points", fontsize=18)
a1.tick_params(labelsize=15); a1.set_ylim(-1.1, 1.1)
fig.text(0.665, 0.86, f"Wetter than usual: turnout {abs(T['b']):.2f} points\nlower per cm of rain", fontproperties=fp(27), color=INK, va="top")
fig.text(0.665, 0.79, f"95% CI {T['lo']:.2f} to {T['hi']:.2f}, 20 equal groups of {M['main']['n']:,} contests", fontsize=18, color=MUT, va="top")
# randomisation histogram
dr = np.loadtxt(f"{ROOT}/data/ri_draws.csv", skiprows=1)
a2 = fig.add_axes([0.69, 0.13, 0.28, 0.19])
if dr is not None:
    a2.hist(dr, bins=40, color="#C9C2B2", edgecolor=BG)
a2.axvline(T["b"], color=WARM, lw=3.5)
a2.set_yticks([]); a2.spines["left"].set_visible(False); a2.tick_params(labelsize=15)
a2.set_xlabel("estimate with rain maps swapped between elections", fontsize=18)
fig.text(0.665, 0.45, "But only 22 elections: not certain", fontproperties=fp(27), color=INK, va="top")
fig.text(0.665, 0.41, f"Swapping whole rain maps between elections gives an\nestimate this far from zero {T['ri_share_beyond']:.0f}% of the time (p {T['ri_p']:.2f});\nrain the day before shows a link at least as big. No partisan effect.",
         fontsize=18, color=MUT, va="top")
fig.text(0.975, 0.012, "Data: ERA5 via Open-Meteo (CC BY 4.0); Who won here? (UK Parliament, House of Commons Library)  ·  Dr Tristan Hotham  ·  maps.tristanhotham.com/polling-rain",
         fontsize=16, color=MUT, ha="right", va="bottom")
fig.savefig(f"{ROOT}/reddit/polling_rain_collage.png", dpi=100, facecolor=BG)
print("collage saved")
