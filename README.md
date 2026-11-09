# Does rain keep Britain at home?

Polling-day rain and turnout at every UK general election from 1945 to 2024: 14,052 contested constituency contests at 22 elections, each matched to hourly ERA5 reanalysis rain at the seat's grid cell during that election's actual polling hours. Hypotheses, model and checks were pre-specified in a written plan before any outcome model was run (see `NOTES.md`).

Interactive page: https://maps.tristanhotham.com/polling-rain/
Paper: https://doi.org/10.5281/zenodo.24094534
Blog post: https://blog.tristanhotham.com/2026/10/31/polling-rain/
Code and data: https://github.com/Tristan-Hotham/polling-rain

## Headline results

- **Main (planned):** each centimetre of rain in polling hours goes with turnout -0.96 (95% CI -1.82 to -0.11; N = 13,731) percentage points (seat and election fixed effects; SE clustered by seat and by election x region). About 0.10 points per mm; a 5 mm polling day about 0.5 points.
- **But few elections:** clustered by election only, -0.96 (95% CI -2.17 to 0.25; N = 13,731); wild cluster bootstrap by election p = 0.14; randomisation inference swapping whole rain maps between elections p = 0.10. Not established by these standards.
- **Placebos:** rain on the day before polling day -1.68 (95% CI -3.46 to 0.10; N = 13,731), at least as large as the main estimate; the day after -0.12 (95% CI -0.72 to 0.49; N = 13,731).
- **Exploratory (added at review):** the day-before placebo is at least as unusual as the main estimate under the few-cluster checks (wild bootstrap p = 0.08, map-swap p = 0.04); the planned Rademacher bootstrap gives p = 0.13; one row per grid cell and election gives -1.17 (95% CI -1.93 to -0.41).
- **Robustness:** negative under every alternative specification (-1.12 to -0.55) and measure of rain (-1.11 to -0.93); leaving out any one election -1.49 to -0.75, any one region -1.13 to -0.57. Several intervals include zero.
- **Party shares (Great Britain):** Conservative -0.24 (95% CI -1.70 to 1.22; N = 13,113); Labour -0.27 (95% CI -4.11 to 3.57; N = 13,387). No detectable partisan effect.
- **Postal votes (H2):** expected a weaker effect from 2001; the estimate is -0.49 for 1945 to 1997 and -1.10 for 2001 to 2024 (interaction Holm p 0.11).
- **Wettest polling day:** 12 December 2019, 8.7 mm on average in polling hours; 88% of seats had 5 mm or more. 1951, 1992 and 1997 were almost dry.

These are reduced-form associations. ERA5 is coarse (about 31 km), turnout is per seat, and there are only 22 elections.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js`, `img/` | Interactive page: every constituency at every election coloured by rain in polling hours, election slider, search, popups with turnout and hourly rain |
| `data/panel.csv` | One row per contest 1945 to 2024 (14,090): turnout, party shares, margins, region, crowding, rain in polling hours, whole day, evening, day before and after, 50 km mean, temperature, sample flags |
| `data/models.json` | Every estimate (coefficient, SE, 95% CI, p, N) |
| `data/ri_draws.csv` | The 1,000 randomisation-inference estimates |
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

- Rain: hourly ERA5 precipitation (Open-Meteo archive) at the grid point nearest the seat point rounded to 0.25 degree (369 cells), summed over polling hours: 8am to 9pm in 1945 (assumed), 7am to 9pm 1950 to 1966, 7am to 10pm from 1970 (House of Commons Library SN/PC/05517).
- Sample: contested seats with turnout; university seats and 22 seats whose 1945 poll was, or may have been, postponed for wakes weeks dropped.
- Model: turnout on rain (cm) with seat-name and election fixed effects; two-way clustered SE; wild cluster bootstrap by election (Webb weights); randomisation inference permuting national rain maps between elections.

## Sources and licences

- ERA5 hourly reanalysis (Hersbach et al. 2020), Copernicus Climate Change Service, via the Open-Meteo Historical Weather API (Zippenfenig 2023): CC BY 4.0. Weather data by Open-Meteo.com.
- Hotham (2026) Who won here? (Zenodo 10.5281/zenodo.23761425), from UK Parliament and House of Commons Library results: Open Parliament Licence v3.0.
- ONS regions: Open Government Licence v3.0. Base map: OpenFreeMap, OpenStreetMap contributors (ODbL).
- Code MIT; text, figures and data CC BY 4.0 (see `LICENSE`).

## Citation

Hotham, T. (2026) Does rain keep Britain at home? Polling-day weather, turnout and party support at UK general elections, 1945 to 2024. Zenodo. https://doi.org/10.5281/zenodo.24094534

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
