"""Step 6: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24094534, https://doi.org/10.5281/zenodo.24094534 and https://blog.tristanhotham.com/2026/10/31/polling-rain/ stay as placeholders for the publisher. Also asserts every statement made in words."""
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
# ---- facts stated in words (page, blog, paper), checked against the results ----
assert T["lo"] < 0 and T["hi"] < 0 and T["wild_p"] > 0.1 and T["ri_p"] > 0.05
assert 0.08 < -T["b_mm"] < 0.12, "about a tenth of a point per mm"
assert 0.4 < -T["b_5mm"] < 0.6, "5 mm: about half a point"
assert -T["b"] > T["gomez_per_cm"], "larger per cm than Gomez et al."
assert abs(-T["b"] - T["damsbo_per_cm"]) < 0.1, "close to the Danish estimate"
be = M["desc"]["by_election"]
assert be["2001"]["rain"] < M["desc"]["rain_mean"] and be["1997"]["turnout"] - be["2001"]["turnout"] > 10, "2001 not unusually wet, big fall"
assert M["pl_before"]["b"] <= T["b"] and M["pl_before"]["lo"] < 0 < M["pl_before"]["hi"] and abs(M["pl_after"]["b"]) < 0.2
neg = ["sp_seatperiod", "sp_elreg", "sp_elnat", "sp_temp", "sp_noseat", "sp_fd", "sp_cl_elec", "m_0722", "m_day", "m_eve", "m_50km", "m_log", "m_r1", "m_r5", "m_r10", "drop1945", "dropNI", "drop1719"]
assert all(M[k]["b"] < 0 for k in neg), "negative under every other choice"
assert sum(M[k]["lo"] < 0 < M[k]["hi"] for k in neg) >= 3, "several intervals include zero"
assert all(M[f"loo_e_{e}"]["b"] < 0 for e in ELECTIONS) and all(M[f"loo_r_{r}"]["b"] < 0 for r in REGIONS)
assert M["party_con"]["lo"] < 0 < M["party_con"]["hi"] and M["party_lab"]["lo"] < 0 < M["party_lab"]["hi"]
assert T["post_b"] < T["pre_b"] and M["h_pre"]["lo"] < 0 < M["h_pre"]["hi"]
assert M["h_urban"]["lo"] < 0 < M["h_urban"]["hi"] and M["h_marg"]["lo"] < 0 < M["h_marg"]["hi"]
assert all(be[e]["rain"] < 0.1 for e in ("1951", "1992", "1997")) and T["wettest_e"] == "2019"
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261109")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
