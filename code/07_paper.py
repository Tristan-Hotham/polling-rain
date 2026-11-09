"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds booktabs tables, compiles with xelatex.
Output: release/paper/Hotham_Polling_Rain.pdf and .tex beside the f_*.pdf figures.
https://doi.org/10.5281/zenodo.24094534 stays a placeholder unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]; n = R["n"]
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Polling_Rain"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "raw": return tex(str(v))
    v = float(v)
    if f == "int": return f"{int(round(v)):,}".replace(",", "{,}")
    if f == "f0": return f"{v:.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "abs1": return f"{abs(v):.1f}"
    if f == "abs2": return f"{abs(v):.2f}"
    raise ValueError(f)


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def row(lab, m, d=2):
    lab = lab if "$" in lab else tex(lab)
    return f"{lab} & {m['b']:.{d}f} & [{m['lo']:.{d}f}, {m['hi']:.{d}f}] & {pv(m['p'])} & {m['n']:,}\\\\\n"


def table(cap, label, body, head="Specification & Estimate & 95\\% CI & $p$ & $N$", cols="p{7.6cm}rcrr", note=None):
    nt = f"\\par\\vspace{{2pt}}\\parbox{{\\linewidth}}{{\\footnotesize {note}}}" if note else ""
    return (f"\\begin{{table}}[tbp]\\centering\\small\\caption{{{cap}}}\\label{{{label}}}\n\\begin{{tabular}}{{{cols}}}\\toprule {head}\\\\\\midrule\n"
            + body + f"\\bottomrule\\end{{tabular}}{nt}\\end{{table}}")


SE = "Turnout in percentage points per centimetre of polling-hours rain. Seat and election fixed effects; standard errors clustered two ways, by seat lineage and by election $\\times$ region, unless stated."
d = M["desc"]
TD = table("Data and samples, UK general elections 1945 to 2024.", "tab:desc",
           f"Contests at 22 general elections & {n['contests']:,}\\\\\n"
           f"Excluded: uncontested / university seats / 1945 postponed polls & {n['uncontested']} / {n['univ']} / {n['postponed']}\\\\\n"
           f"Analysis sample (contests) & {n['sample']:,}\\\\\n"
           f"Seat lineages (constituency names) & {n['seats']:,}\\\\\n"
           f"Weather grid cells (0.25 degree) & {n['cells']:,}\\\\\n"
           f"Election $\\times$ region clusters & {d['clusters_elreg']:,}\\\\\n\\midrule\n"
           f"Turnout, mean (SD), \\% & {d['turnout_mean']:.1f} ({d['turnout_sd']:.1f})\\\\\n"
           f"Polling-hours rain, mean / median, mm & {d['rain_mean']:.2f} / {d['rain_median']:.1f}\\\\\n"
           f"Polling-hours rain, SD overall / within election, mm & {d['rain_sd']:.2f} / {d['rain_sd_within']:.2f}\\\\\n"
           f"Contests with at least 1 / 5 / 10 mm, \\% & {d['share_1mm']:.1f} / {d['share_5mm']:.1f} / {d['share_10mm']:.1f}\\\\\n"
           f"First-difference pairs (unchanged boundaries) & {n['fd_pairs']:,}\\\\\n", head="Item & Value", cols="p{10cm}r")

mb = row("Main: seat and election FE, two-way clustered", M["main"])
mb += row("Same, clustered by election $\\times$ region only", M["sp_cl_elreg"]) + row("Same, clustered by election only (22 clusters)", M["sp_cl_elec"])
mb += f"Wild cluster bootstrap by election (Webb weights, {M['wild']['draws']:,} draws) & & & {M['wild']['p']:.3f} & \\\\\n"
mb += f"Randomisation inference: rain maps permuted between elections ({M['ri']['draws']:,}) & & [{M['ri']['q025']:.2f}, {M['ri']['q975']:.2f}] & {M['ri']['p']:.3f} & \\\\\n"
TM = table("Main estimate (H1) and inference allowing for few elections.", "tab:main", mb,
           note=SE + " For randomisation inference the bracket is the central 95\\% of the permutation distribution under the sharp null.")

rb = "".join(row(M[k]["label"], M[k]) for k in ("sp_seatperiod", "sp_elreg", "sp_elnat", "sp_temp", "sp_noseat", "sp_fd"))
rb += "\\midrule\n" + "".join(row(M[k]["label"] + (" (per unit)" if k == "m_log" else " (points)" if k.startswith("m_r") else ""), M[k]) for k in ("m_0722", "m_day", "m_eve", "m_50km", "m_log", "m_r1", "m_r5", "m_r10"))
rb += "\\midrule\n" + "".join(row(M[k]["label"], M[k]) for k in ("drop1945", "dropNI", "drop1719"))
rb += "\\midrule\n" + row("Placebo: day before, alone", M["pl_before"]) + row("Placebo: day after, alone", M["pl_after"])
for t_, lab in (("rain_cm", "Joint: polling day"), ("rain_before_cm", "Joint: day before"), ("rain_after_cm", "Joint: day after")):
    m = M["pl_joint"]["terms"][t_]; rb += f"{lab} & {m['b']:.2f} & [{m['lo']:.2f}, {m['hi']:.2f}] & {pv(m['p'])} & {M['pl_joint']['n']:,}\\\\\n"
TR = table("Robustness: specifications, measures of rain, samples and placebo days.", "tab:rob", rb,
           note=SE + " Indicator rows give points for a contest with at least that much rain. The first-difference row relates the change in turnout to the change in rain between consecutive elections in seats with unchanged boundaries, with election FE.")

hb = "".join(row(M[k]["label"], M[k]) for k in ("h_pre", "h_post", "h_post01"))
hb += "".join(row(n_, M[f"h_nat_{n_}"]) for n_ in ("England", "Scotland", "Wales", "Northern Ireland"))
hb += "".join(row(M[k]["label"], M[k]) for k in ("h_urb1", "h_urb0", "h_urban", "h_marg1", "h_marg0", "h_marg"))
hb += row("Temperature, per 10 degrees C (with rain)", M["temp"])
hb += "\\midrule\n" + "".join(row(M[k]["label"], M[k]) for k in ("party_con", "party_con_elreg", "party_con_pre", "party_lab", "party_lab_elreg", "party_lab_pre", "party_lib", "party_lib_elreg", "party_gap"))
TH = table("Heterogeneity (H2, H4) and party shares (H3).", "tab:het", hb,
           note=SE + " Interaction rows report the interaction term. Party shares: percentage points of the vote, single-member contests in Great Britain where the party stood. Holm-adjusted $p$ for H2 to H4: " +
           ", ".join(f"{dict(h_post01='rain x 2001 on', temp='temperature', party_con='Conservative share', party_lab='Labour share')[k]} {v:.2f}" for k, v in T["holm"].items()) + ".")

le = "".join(row(M[f"loo_e_{e}"]["label"], M[f"loo_e_{e}"]) for e in ELECTIONS) + "\\midrule\n" + "".join(row(M[f"loo_r_{r}"]["label"], M[f"loo_r_{r}"]) for r in REGIONS)
TL = table("Leave one election or one region out.", "tab:loo", le, note=SE)
eb = "".join(f"{x['election']} & {x['hrs']} & {x['n']} & {x['rain']:.2f} & {x['rain_sd']:.2f} & {x['rain_max']:.1f} & {x['wet5']:.1f} & {x['temp']:.1f} & {x['turnout']:.1f}\\\\\n" for x in R["by_election"])
TE = table("Weather and turnout by election (analysis sample).", "tab:elec", eb,
           head="Election & Hours & $N$ & Rain mean & SD & Max & $\\geq$5 mm \\% & Temp. $^\\circ$C & Turnout \\%", cols="lcrrrrrrr",
           note="Rain in mm over polling hours at the seat's grid cell; temperature is the mean over polling hours.")
AD = (f"Contests are those of \\citet{{hotham2026ele}} for the 22 general elections from 1945 to 2024 ({n['contests']:,} rows). Seat points (longitude, latitude) were rounded to the nearest 0.25 degree to give {n['cells']} cells; every contest matched a weather record. "
      "For each cell and polling date the Open-Meteo archive returned 72 hourly values of precipitation (mm, total of the preceding hour) and 2 m temperature from 00:00 local time (Europe/London) on the day before. "
      "With $s$ and $e$ the opening and closing hours, polling-hours rain is the sum of values with indices $25+s$ to $24+e$ (0-based); the day-before and day-after placebos use the same hours shifted by 24 hours, and whole-day rain the hours 00:00 to 24:00. "
      "Seat lineage is the constituency name lower-cased with punctuation removed. Region is the ONS region containing the seat point (nearest region for points offshore), or the nation for Scotland, Wales and Northern Ireland. "
      f"Seat crowding is the number of other constituency points within 15 km at the same election. Previous margin is the winner's share minus the runner-up's share at the previous election under the same name (single-member contests). "
      f"Party families follow \\citet{{hotham2026ele}}. The 1945 seats dropped as postponed are: {tex(', '.join(POSTPONED_1945))}.")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_DESC", TD), ("TABLE_MAIN", TM), ("TABLE_HET", TH), ("TABLE_ROB", TR), ("TABLE_LOO", TL), ("TABLE_ELEC", TE), ("APPENDIX_DATA", AD)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24094534", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, [l for l in t.splitlines() if "{{" in l or "--" in l][:5]
assert "pre-registered" not in t.lower() and "DSIT" not in t and "DCMS" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
ab = re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1)
print("paper", r.returncode, len(txt.split()), "words in all;", len(txt.split("References")[0].split()), "before references; abstract", len(ab.split()), [l for l in pages.splitlines() if l.startswith("Pages")])
