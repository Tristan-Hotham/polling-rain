**Title:** [OC] Does rain keep Britain at home? Every UK general election since 1945: seats that were wetter while the polls were open had turnout about 1.0 point lower per cm of rain, but the evidence is weak

**Body:**

I matched all 14,052 contested constituency contests at the 22 UK general elections from 1945 to 2024 to hourly weather reanalysis rain at each seat, added up over the hours the polls were open.

- Most polling days are dry: the typical contest saw 0.4 mm. The wettest by far was 12 December 2019 (8.7 mm on average; 88% of seats had 5 mm or more).
- Comparing each seat with itself: turnout 0.96 points lower per cm of rain (95% CI -1.82 to -0.11), about a tenth of a point per mm.
- But there are only 22 elections and rain falls region by region. Swapping whole rain maps between elections gives an estimate this far from zero 10% of the time, and rain on the day BEFORE polling shows a link at least as big. So: maybe a small effect, not established.
- No sign of partisan rain: no clear link with the Conservative or Labour share (Great Britain).

Interactive map (every seat at every election, slider, hourly rain in the popups): https://maps.tristanhotham.com/polling-rain/

**Source comment:**

Data: ERA5 reanalysis via the Open-Meteo archive (CC BY 4.0); constituency results from my dataset Who won here? (UK Parliament and House of Commons Library). Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper, data and code: https://github.com/Tristan-Hotham/polling-rain
