"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24094534, https://doi.org/10.5281/zenodo.24094534 and https://blog.tristanhotham.com/2026/10/31/polling-rain/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json"); T = R["T"]; M = R["M"]
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Polling_Rain"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
assert 30 < T["dry_pc"] < 37, "about a third of contests dry"
assert T["rain_median"] < 1
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Does rain keep Britain at home?",
        "slug": "polling-rain",
        "excerpt": f"Every UK general election since 1945, seat by seat, against the rain that fell while the polls were open. Wetter seats saw turnout about {abs(T['b_mm']):.1f} points lower per millimetre, but with only 22 elections that is not established, and there is no sign that rain helps any party.",
        "seo_description": f"Rain while the polls were open at 22 UK general elections: turnout about {abs(T['b']):.1f} point lower per cm of rain, but not established. No partisan effect.",
        "tags": ["maps", "data visualisation", "elections", "turnout", "weather", "rain", "UK politics", "general elections"],
        "header_alt": "Title card reading 'Does rain keep Britain at home?' beside a map of the UK with a dot for every constituency coloured by rain while the polls were open on 12 December 2019, most of England dark blue."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("panel.csv", "models.json", "results.json", "rain_classes.json", "ri_draws.csv"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    z.write(os.path.join(DATA, "site", "hours.json"), f"{SLUG}/data/site/hours.json")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("{,}", ",").replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("\\times", "x")
zmeta = {"title": "Does Rain Keep Britain at Home? Polling-Day Weather, Turnout and Party Support at UK General Elections, 1945 to 2024",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/polling-rain/}}.</p><p>Sources: ERA5 hourly reanalysis (Copernicus Climate Change Service) via the Open-Meteo Historical Weather API (CC BY 4.0); Hotham (2026) Who won here? (UK Parliament and House of Commons Library results, Open Parliament Licence v3.0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["turnout", "weather", "rainfall", "cost of voting", "British general elections", "randomisation inference", "ERA5"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23761425", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.5281/zenodo.7970649", "relation": "references", "resource_type": "software"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj and "DSIT" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2, keepdash=True)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
