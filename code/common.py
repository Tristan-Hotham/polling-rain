"""Shared paths, constants and helpers for the polling-rain study ("Does rain keep Britain at home?").

Inputs (read in place, never modified):
  W    weather_polling.json  ERA5-family reanalysis from the Open-Meteo Historical Weather API (CC BY 4.0; ERA5 from
                             Copernicus): keys "YYYY-MM-DD|lat,lon" for each general election date 1945 to 2024 and each
                             0.25-degree cell used by a seat (seat point rounded to the nearest 0.25 degree); values
                             {p: hourly precipitation mm, t: hourly 2 m temperature C, glat, glon}; 72 hourly values from
                             00:00 local time (Europe/London) on the day BEFORE polling day. Open-Meteo precipitation at
                             hour h is the total of the preceding hour, so index 24 + h + 1 is the hour h to h + 1 on
                             polling day.
  ELE  contests.csv          Who won here? (Hotham 2026, Zenodo 10.5281/zenodo.23761425): every contest with date,
       candidates.csv        constituency, turnout, point, nation; every candidacy with party family and share.
  GEO  uk_topo.json          ONS regions and countries (Open Government Licence v3.0), to give each seat point a region.
Intermediates go to SCR, outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.environ.get("PR_W", "/home/claude/newdata/raw_new12/weather_polling.json")
ELE = os.environ.get("PR_ELE", "/home/claude/src6/elections-since-1832/data")
GEO = os.environ.get("PR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PR_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("PR_SCRATCH", "/home/claude/scratch/polling-rain")
DATA = os.path.join(ROOT, "data")
for d in (DATA, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "polling-rain"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
SEED = 20261109

ELECTIONS = ['1945', '1950', '1951', '1955', '1959', '1964', '1966', '1970', 'February 1974', 'October 1974', '1979',
             '1983', '1987', '1992', '1997', '2001', '2005', '2010', '2015', '2017', '2019', '2024']
EIDX = {e: i for i, e in enumerate(ELECTIONS)}
ESHORT = {e: (e.replace("February ", "Feb ").replace("October ", "Oct ")) for e in ELECTIONS}


def hours(e):
    """Polling hours (start, end) in local clock hours (HoC Library SN/PC/05517, p.3)."""
    y = int(e[-4:])
    if y < 1950: return (8, 21)          # 8am to 8pm, extendable by an hour each end on request; 8 to 9pm usual
    if y < 1970: return (7, 21)
    return (7, 22)


# boundary periods (redistributions took effect at 1950, 1955, Feb 1974, 1983, 1997, 2005 Scotland, 2010, 2024)
def period(e, nation):
    y = int(e[-4:])
    if y == 1945: return "1945"
    if y <= 1951: return "1950"
    if e == "February 1974" or e == "October 1974" or y == 1979: return "1974"
    if y < 1974: return "1955"
    if y < 1997: return "1983"
    if y < 2005: return "1997"
    if y == 2005: return "2005s" if nation == "Scotland" else "1997"
    if y < 2024: return "2010"
    return "2024"


# 1945 seats whose poll was postponed for wakes weeks (HC Deb 31 May 1945 provisional list, plus Warrington, 11 June)
POSTPONED_1945 = ["Carlisle", "Bolton", "Farnworth", "Nelson and Colne", "Darwen", "Westhoughton", "Barrow in Furness",
                  "Lonsdale", "Crewe", "Edinburgh Central", "Edinburgh North", "Edinburgh East", "Edinburgh South",
                  "Edinburgh West", "Midlothian and Peebles Northern", "Greenock", "Stirling and Falkirk",
                  "West Renfrewshire", "Peebles and South Midlothian", "Berwick and Haddington",
                  "Clackmannan and East Stirlingshire", "Warrington"]

REGIONS = ["North East", "North West", "Yorkshire and The Humber", "East Midlands", "West Midlands", "East of England",
           "London", "South East", "South West", "Wales", "Scotland", "Northern Ireland"]


def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def pval(p):
    p = float(p)
    if p < 0.001: return "below 0.001"
    if p < 0.01: return f"{p:.3f}"
    return f"{p:.2f}"


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{round(float(v))}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "s1": return f"{float(v):+.1f}"
    if f == "s2": return f"{float(v):+.2f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    if f == "abs2": return f"{abs(float(v)):.2f}"
    if f == "p": return pval(v)
    raise ValueError(f)
