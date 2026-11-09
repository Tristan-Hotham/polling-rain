"""Step 9: README.md and reddit/post.md, every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]; n = R["n"]
ci = lambda m, d=2: f"{m['b']:.{d}f} (95% CI {m['lo']:.{d}f} to {m['hi']:.{d}f}; N = {m['n']:,})"
readme = f"""# Does rain keep Britain at home?

Polling-day rain and turnout at every UK general election from 1945 to 2024: {n['sample']:,} contested constituency contests at 22 elections, each matched to hourly ERA5 reanalysis rain at the seat's grid cell during that election's actual polling hours. Hypotheses, model and checks were pre-specified in a written plan before any outcome model was run (see `NOTES.md`).

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24094534}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/polling-rain/}}
Code and data: {REPO}

## Headline results

- **Main (planned):** each centimetre of rain in polling hours goes with turnout {ci(M['main'])} percentage points (seat and election fixed effects; SE clustered by seat and by election x region). About {abs(T['b_mm']):.2f} points per mm; a 5 mm polling day about {abs(T['b_5mm']):.1f} points.
- **But few elections:** clustered by election only, {ci(M['sp_cl_elec'])}; wild cluster bootstrap by election p = {T['wild_p']:.2f}; randomisation inference swapping whole rain maps between elections p = {T['ri_p']:.2f}. Not established by these standards.
- **Placebos:** rain on the day before polling day {ci(M['pl_before'])}, at least as large as the main estimate; the day after {ci(M['pl_after'])}.
- **Exploratory (added at review):** the day-before placebo is at least as unusual as the main estimate under the few-cluster checks (wild bootstrap p = {T['before_wild_p']:.2f}, map-swap p = {T['before_ri_p']:.2f}); the planned Rademacher bootstrap gives p = {T['rad_p']:.2f}; one row per grid cell and election gives {T['cell_b']:.2f} (95% CI {T['cell_lo']:.2f} to {T['cell_hi']:.2f}).
- **Robustness:** negative under every alternative specification ({T['alt_min']:.2f} to {T['alt_max']:.2f}) and measure of rain ({T['meas_min']:.2f} to {T['meas_max']:.2f}); leaving out any one election {T['loo_e_min']:.2f} to {T['loo_e_max']:.2f}, any one region {T['loo_r_min']:.2f} to {T['loo_r_max']:.2f}. Several intervals include zero.
- **Party shares (Great Britain):** Conservative {ci(M['party_con'])}; Labour {ci(M['party_lab'])}. No detectable partisan effect.
- **Postal votes (H2):** expected a weaker effect from 2001; the estimate is {T['pre_b']:.2f} for 1945 to 1997 and {T['post_b']:.2f} for 2001 to 2024 (interaction Holm p {T['holm']['h_post01']:.2f}).
- **Wettest polling day:** 12 December 2019, {T['wettest_mm']:.1f} mm on average in polling hours; {T['wettest_wet5']:.0f}% of seats had 5 mm or more. 1951, 1992 and 1997 were almost dry.

These are reduced-form associations. ERA5 is coarse (about 31 km), turnout is per seat, and there are only 22 elections.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js`, `img/` | Interactive page: every constituency at every election coloured by rain in polling hours, election slider, search, popups with turnout and hourly rain |
| `data/panel.csv` | One row per contest 1945 to 2024 ({n['contests']:,}): turnout, party shares, margins, region, crowding, rain in polling hours, whole day, evening, day before and after, 50 km mean, temperature, sample flags |
| `data/models.json` | Every estimate (coefficient, SE, 95% CI, p, N) |
| `data/ri_draws.csv` | The {M['ri']['draws']:,} randomisation-inference estimates |
| `data/results.json` | Every number quoted in the page, paper, blog, collage and post |
| `data/rain_classes.json`, `data/site/` | Rain colour classes and compact page data (hourly rain per cell and polling day) |
| `code/` | The pipeline (below) |
| `NOTES.md` | Working notes, the analysis plan written before estimation, and the verified references |
| `release/paper/` | Paper (PDF and LaTeX), figures and `cover_note.md` |
| `release/blog/` | Blog post (WordPress block markup), figures and `meta.json` |
| `release/zenodo/` | Zenodo files and metadata |
| `reddit/` | Collage, its script, the GIF and the post text |
| `header.png` | Social card (1200 by 630) |

## How to rerun

Inputs and paths are in `code/common.py` (the weather file is the Open-Meteo archive extract described there; results from Who won here?).

```
python3 code/01_build.py      # panel: seats, turnout, rain and temperature measures
python3 code/02_models.py     # every model, wild bootstrap and randomisation inference
python3 code/03_results.py    # results.json and checks on statements made in words
python3 code/04_figures.py    # figures and header.png
python3 code/05_export.py     # page data
python3 code/06_build_site.py # index.html
python3 code/07_paper.py      # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py     # collage
python3 code/09_readme.py     # README and Reddit post
python3 code/08_release.py    # blog post, Zenodo files
node code/qa.js               # screenshots (Playwright)
```

Python 3 with pandas, numpy, shapely, pyproj, matplotlib, pyfixest; xelatex.

## Method in brief

- Rain: hourly ERA5 precipitation (Open-Meteo archive) at the grid point nearest the seat point rounded to 0.25 degree ({n['cells']} cells), summed over polling hours: 8am to 9pm in 1945 (assumed), 7am to 9pm 1950 to 1966, 7am to 10pm from 1970 (House of Commons Library SN/PC/05517).
- Sample: contested seats with turnout; university seats and {n['postponed']} seats whose 1945 poll was, or may have been, postponed for wakes weeks dropped.
- Model: turnout on rain (cm) with seat-name and election fixed effects; two-way clustered SE; wild cluster bootstrap by election (Webb weights); randomisation inference permuting national rain maps between elections.

## Sources and licences

- ERA5 hourly reanalysis (Hersbach et al. 2020), Copernicus Climate Change Service, via the Open-Meteo Historical Weather API (Zippenfenig 2023): CC BY 4.0. Weather data by Open-Meteo.com.
- Hotham (2026) Who won here? (Zenodo 10.5281/zenodo.23761425), from UK Parliament and House of Commons Library results: Open Parliament Licence v3.0.
- ONS regions: Open Government Licence v3.0. Base map: OpenFreeMap, OpenStreetMap contributors (ODbL).
- Code MIT; text, figures and data CC BY 4.0 (see `LICENSE`).

## Citation

Hotham, T. (2026) Does rain keep Britain at home? Polling-day weather, turnout and party support at UK general elections, 1945 to 2024. Zenodo. {{https://doi.org/10.5281/zenodo.24094534}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
post = f"""**Title:** [OC] Does rain keep Britain at home? Every UK general election since 1945: seats that were wetter while the polls were open had turnout about {abs(T['b']):.1f} point lower per cm of rain, but the evidence is weak

**Body:**

I matched all {n['sample']:,} contested constituency contests at the 22 UK general elections from 1945 to 2024 to hourly weather reanalysis rain at each seat, added up over the hours the polls were open.

- Most polling days are dry: the typical contest saw {T['rain_median']:.1f} mm. The wettest by far was 12 December 2019 ({T['wettest_mm']:.1f} mm on average; {T['wettest_wet5']:.0f}% of seats had 5 mm or more).
- Comparing each seat with itself: turnout {abs(T['b']):.2f} points lower per cm of rain (95% CI {T['lo']:.2f} to {T['hi']:.2f}), about a tenth of a point per mm.
- But there are only 22 elections and rain falls region by region. Swapping whole rain maps between elections gives an estimate this far from zero {T['ri_share_beyond']:.0f}% of the time, and rain on the day BEFORE polling shows a link at least as big. So: maybe a small effect, not established.
- No sign of partisan rain: no clear link with the Conservative or Labour share (Great Britain).

Interactive map (every seat at every election, slider, hourly rain in the popups): {PAGE}

**Source comment:**

Data: ERA5 reanalysis via the Open-Meteo archive (CC BY 4.0); constituency results from my dataset Who won here? (UK Parliament and House of Commons Library). Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper, data and code: {REPO}
"""
for s in (readme.replace("|---|---|", ""), post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "pre-registered"):
        assert bad not in s, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()))
