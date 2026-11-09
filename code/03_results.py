"""Step 3: data/results.json, the single source of every number quoted anywhere (page, paper, blog, collage, post, README).
Combines data/models.json (step 2) with descriptive counts from data/panel.csv; also asserts the statements made in words."""
import numpy as np
import pandas as pd
from common import *

M = jload(f"{DATA}/models.json")
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
D = P[P.insample]
st = jload(f"{SCR}/stats01.json")
R = {"M": M, "n": st}

T = {}
m = M["main"]
T["b"], T["lo"], T["hi"], T["p"] = m["b"], m["lo"], m["hi"], m["p"]
T["b_mm"] = m["b"] / 10; T["lo_mm"] = m["lo"] / 10; T["hi_mm"] = m["hi"] / 10
T["b_sd"] = m["b"] * M["desc"]["rain_sd_within"] / 10
T["b_5mm"] = m["b"] * 0.5
T["b_inch"] = m["b"] * 2.54
T["wild_p"] = M["wild"]["p"]; T["ri_p"] = M["ri"]["p"]; T["ri_lo"] = M["ri"]["q025"]; T["ri_hi"] = M["ri"]["q975"]
T["ri_mean"] = M["ri"]["mean"]
T["ri_share_beyond"] = 100 * M["ri"]["p"]
le = [M[f"loo_e_{e}"]["b"] for e in ELECTIONS]; lr = [M[f"loo_r_{r}"]["b"] for r in REGIONS]
T["loo_e_min"], T["loo_e_max"] = min(le), max(le); T["loo_r_min"], T["loo_r_max"] = min(lr), max(lr)
T["loo_e_sig"] = sum(M[f"loo_e_{e}"]["hi"] < 0 for e in ELECTIONS); T["loo_r_sig"] = sum(M[f"loo_r_{r}"]["hi"] < 0 for r in REGIONS)
alt = ["sp_seatperiod", "sp_elreg", "sp_elnat", "sp_temp", "sp_noseat", "sp_fd"]
T["alt_min"] = min(M[k]["b"] for k in alt); T["alt_max"] = max(M[k]["b"] for k in alt)
T["alt_sig"] = sum(M[k]["hi"] < 0 for k in alt); T["alt_n"] = len(alt)
mea = ["m_0722", "m_day", "m_eve", "m_50km"]
T["meas_min"] = min(M[k]["b"] for k in mea); T["meas_max"] = max(M[k]["b"] for k in mea)
T["pre_b"], T["post_b"] = M["h_pre"]["b"], M["h_post"]["b"]
T["turnout_mean"] = M["desc"]["turnout_mean"]
T["rain_median"] = M["desc"]["rain_median"]; T["rain_mean"] = M["desc"]["rain_mean"]
be = M["desc"]["by_election"]
T["wettest_e"] = max(be, key=lambda e: be[e]["rain"]); T["wettest_mm"] = be[T["wettest_e"]]["rain"]
T["wettest_wet5"] = be[T["wettest_e"]]["wet5"]
T["driest_e"] = min(be, key=lambda e: be[e]["rain"]); T["driest_mm"] = be[T["driest_e"]]["rain"]
T["second_e"] = sorted(be, key=lambda e: -be[e]["rain"])[1]; T["second_mm"] = be[T["second_e"]]["rain"]
T["implied_wettest"] = m["b"] * T["wettest_mm"] / 10
top = D.sort_values("rain", ascending=False).iloc[0]
T["max_seat"] = top.constituency; T["max_e"] = top.election; T["max_mm"] = float(top.rain)
T["dry_pc"] = 100 * float((D.rain < 0.1).mean())
# Holm adjustment over the secondary hypotheses H2 (postal), H3 (Con, Lab) and H4 (temperature)
sec = {"h_post01": M["h_post01"]["p"], "party_con": M["party_con"]["p"], "party_lab": M["party_lab"]["p"], "temp": M["temp"]["p"]}
o = sorted(sec, key=sec.get); holm = {}; run = 0
for i, k in enumerate(o):
    run = max(run, min(1, (len(o) - i) * sec[k])); holm[k] = run
T["holm"] = holm
# comparison with published per-centimetre effects
T["gomez_per_cm"] = 1 / 2.54            # "just under 1% per inch" (Gomez et al. 2007): at most 0.39 per cm
T["damsbo_per_cm"] = 0.95               # Damsbo-Svendsen and Hansen (2023): 0.95 points per cm (Denmark)
T["eisinga_per_cm"] = 1 / 2.5           # about 1 point per 25 mm (Eisinga et al. 2012)
T["temp_b"] = M["temp"]["b"]
# exploratory checks added at independent review
T["rad_p"] = M["rev_wild_rad"]["p"]; T["before_wild_p"] = M["rev_wild_before"]["p"]; T["before_ri_p"] = M["rev_ri_before"]["p"]
T["elreg_wild_p"] = M["rev_wild_elreg"]["p"]
T["cell_b"], T["cell_lo"], T["cell_hi"], T["cell_n"], T["cell_cells"] = (M["rev_cell"][k] for k in ("b", "lo", "hi", "n", "cells"))
T["mde"] = 2.8 * m["se"]; T["mde_el"] = 2.8 * M["sp_cl_elec"]["se"]
R["T"] = T

# page and GIF series: by election
R["by_election"] = [dict(election=e, short=ESHORT[e], year=int(e[-4:]), **{k: be[e][k] for k in ("rain", "rain_sd", "rain_max", "wet5", "turnout", "temp", "n", "hrs")})
                    for e in ELECTIONS]

# ---------- checks on statements made in words ----------
assert T["lo"] < 0 and T["hi"] < 0, "main CI (two-way clustered) excludes zero as written"
assert T["wild_p"] > 0.05 and T["ri_p"] > 0.05, "few-cluster inference does not reject, as written"
assert M["sp_cl_elec"]["lo"] < 0 < M["sp_cl_elec"]["hi"]
assert M["pl_before"]["b"] < T["b"] < 0 and M["pl_before"]["lo"] < 0 < M["pl_before"]["hi"], "day-before placebo as large and not significant"
assert M["pl_after"]["lo"] < 0 < M["pl_after"]["hi"] and abs(M["pl_after"]["b"]) < 0.3
assert M["party_con"]["lo"] < 0 < M["party_con"]["hi"] and M["party_lab"]["lo"] < 0 < M["party_lab"]["hi"]
assert T["post_b"] < T["pre_b"] < 0 and M["h_pre"]["lo"] < 0 < M["h_pre"]["hi"] and M["h_post"]["hi"] < 0
assert M["h_post01"]["b"] < 0, "H2 predicted a positive interaction: the sign is the opposite"
assert M["m_r5"]["lo"] < 0 < M["m_r5"]["hi"] and M["m_r10"]["lo"] < 0 < M["m_r10"]["hi"] and M["m_r1"]["hi"] < 0
assert all(M[f"loo_e_{e}"]["b"] < 0 for e in ELECTIONS) and all(M[f"loo_r_{r}"]["b"] < 0 for r in REGIONS)
assert M["h_urban"]["lo"] < 0 < M["h_urban"]["hi"] and M["h_marg"]["lo"] < 0 < M["h_marg"]["hi"]
assert T["wettest_e"] == "2019" and T["driest_e"] == "1997" and T["second_e"] == "2017"
assert T["rad_p"] > 0.1 and T["before_ri_p"] < T["ri_p"] and T["before_wild_p"] < T["wild_p"], "placebo at least as unusual as the main estimate"
assert T["elreg_wild_p"] > 0.05 and T["cell_hi"] < 0
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps(T, indent=1))
