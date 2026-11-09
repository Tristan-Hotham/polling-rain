# polling-rain: working notes

Brief: /home/claude/work/new12/BRIEFS.md section 1 (plus the shared rules it points to: new11, new10, new9, new8 tops;
/home/claude/newdata/BRIEF.md; GIF brief /home/claude/gifs/BRIEF.md).
Format refs: /home/claude/studies/pm-streets, /home/claude/studies/wiki-vs-hansard (and local-mp-bonus, same elections data).
Scratch: /home/claude/scratch/polling-rain (delete at end, by exact path).
Inputs (read in place): /home/claude/newdata/raw_new12/weather_polling.json;
/home/claude/src6/elections-since-1832/data/{contests,candidates}.csv; /home/claude/newdata/raw/geo/uk_topo.json (regions).

## Facts checked before writing the plan (exposure side only; no turnout model run)

- contests.csv 1945 to 2024: 22 general elections, 14,094 contests, every one with a point; all match a weather key
  (seat point rounded to the nearest 0.25 degree; 369 distinct cells). Weather: 72 hourly values from 00:00 local time
  on the day before polling; Open-Meteo "precipitation" at hour h is the total of the preceding hour, so the hour
  07:00 to 08:00 on polling day is index 32, and 07:00 to 22:00 is indices 32 to 46.
- The grid point reported is the same for every election (Open-Meteo's best-match archive; ERA5 family). Effective
  resolution of the precipitation field is that of ERA5 (about 31 km): many urban seats share one value.
- Polling-hours rain (07 to 22, all seats): median 0.4 mm, mean 1.6 mm, 38% of contests at least 1 mm, 9.6% at least
  5 mm, 2.6% at least 10 mm. Election means range from 0.0 mm (1997) to 8.7 mm (2019).
- Polling hours (House of Commons Library, Standard Note SN/PC/05517, White 2012, p.3, citing Rallings and Thrasher,
  British Electoral Facts 1832 to 2006, Table 5.12): 1885 to 1913, 8am to 8pm; 1913 to 1950, 8am to 8pm, extendable by
  an hour at either end at any candidate's request; 1950 to 1970, 7am to 9pm; from 1970, 7am to 10pm.
  So: 1945 = 08 to 21 (the usual extended hours; uncertain, see robustness), 1950 to 1966 = 07 to 21, 1970 on = 07 to 22.
- 1945 postponed polls: polling in some seats moved to 12 July and in Nelson and Colne to 19 July because of local
  wakes weeks (Postponement of Polling Day Act 1945). The enacted schedule could not be retrieved. Seats named in
  Hansard: the provisional list read by the Prime Minister on 31 May 1945 (HC Deb 31 May 1945 vol 411 c373 to 374:
  Carlisle, Bolton, Farnworth, Nelson and Colne, Darwen, Westhoughton, Barrow-in-Furness, Lonsdale, Crewe, the five
  Edinburgh seats, Midlothian and Peebles Northern, Greenock, Stirling and Falkirk Burghs, Renfrewshire West, Peebles
  and Southern Midlothian, Berwick and Haddington, Clackmannan and Eastern Stirlingshire) and Warrington (named as
  postponed in the second-reading debate, HC Deb 11 June 1945 vol 411 c1382 to 1393). These seats are dropped for
  1945 in every model; all of 1945 is dropped in a robustness check.
- University seats (1945 only) dropped: no place where their electors voted.

## ANALYSIS PLAN (written before any turnout or vote-share model was run)

### Hypotheses
- H1 (main): more rain during polling hours at a seat lowers its turnout. Prediction: beta < 0.
- H2 (postal voting): the effect is weaker from 2001, when postal votes on demand began in Great Britain
  (Representation of the People Act 2000), than in 1945 to 1997. Prediction: interaction (rain x 2001 on) > 0.
- H3 (partisan): rain raises the Conservative share and lowers the Labour share (the US and German pattern of rain
  helping the right). Two separate outcomes; predictions beta_Con > 0, beta_Lab < 0.
- H4 (temperature): colder polling days lower turnout (two-sided; reported, not a main hypothesis).
- Heterogeneity, two-sided, no strong priors: nation; urban vs rural (seat crowding: number of other constituency
  points within 15 km at the same election, above vs below the median of that election); marginality (winning
  margin at the previous election in the same seat name below 10 points vs not).

### Unit, sample, variables
- Unit: a constituency contest at a UK general election, 1945 to 2024. Contested, turnout recorded, not a
  university seat, not a 1945 postponed seat. Two-member seats of 1945 kept (one turnout per contest).
- Outcome: turnout (percent, as in the source). Partisan outcomes: candidate vote share (percent) of the
  Conservative family and of the Labour family in Great Britain, contests where that family stood.
- Exposure (main): rain in polling hours at the seat's cell, in centimetres (10 mm), summing the hourly values
  for the actual hours of each election (above). Also reported per within-election standard deviation.
- Controls: none in the main model beyond fixed effects (weather is as good as random given place and date);
  temperature (mean over polling hours, and its square) in an alternative.
- Fixed effects (main): seat lineage (constituency name, normalised; names persist across boundary changes) and
  election. Identification is from within-seat deviations in rain relative to the national election average.
- Standard errors (main): two-way clustered by seat lineage and by election x region (12 regions: 9 English
  regions, Scotland, Wales, Northern Ireland; region of the seat point; 264 clusters), because rain is spatially
  correlated within an election. Because there are only 22 elections, also: (a) wild cluster bootstrap by election
  (Rademacher, 999 draws, null imposed); (b) randomisation inference in the spirit of Cooperman (2017): re-assign
  whole national rain maps between elections (each seat gets the rain its cell had on a different election's polling
  day, same hours), 1,000 permutations, keeping the spatial structure of real weather; the p-value is the share of
  permuted |beta| at least as large as the real one.

### Pre-specified robustness and checks
- Alternative specifications: seat x boundary-period FE (boundary periods: 1945; 1950 to 1951; 1955 to 1970;
  Feb 1974 to 1979; 1983 to 1992; 1997 to 2001; 2005 (England, Wales, NI 1997 boundaries; Scotland new); 2010 to
  2019; 2024); first differences (change in turnout on change in rain between consecutive elections in the same
  seat name with no redistribution between them, election FE); election x region FE (rain varying within region
  only); election x nation FE; adding temperature; no seat FE (region FE); one-way clustering by election x region.
- Measurement: whole polling day (00 to 24); rain at least 1 mm, 5 mm, 10 mm (indicators); log(1 + mm);
  07 to 22 for every election; evening only (16 to 22); rain averaged over all cells within 50 km of the seat cell
  (a smoother field, less noise from the coarse grid).
- Placebos: rain on the day before polling day (same hours) and on the day after (same hours; data end at 23:00 the
  day after, so the window is complete) should not predict turnout once polling-day rain is held fixed; each
  entered alone and together with polling-day rain. Randomisation inference (above).
- Leave-one-out: drop each election in turn; drop each region in turn; drop 1945; drop Northern Ireland; drop 2017
  and 2019 (the two wettest).
- Partisan outcomes: same models; also the Liberal family (exploratory).
- What counts against H1: a 95% CI that includes zero. Then I report the range of effects the data rule out
  (the CI) as the finding: a precise null is the result, not a failure.
- Power: 22 elections; the national component of rain is absorbed by election FE, so only within-election variation
  identifies beta. With ERA5's coarse grid, classical measurement error would attenuate beta toward zero; the smoothed
  50 km exposure and the threshold indicators show how far the conclusion depends on this.
- Multiple testing: one main test (H1). H2 to H4 and heterogeneity reported with unadjusted CIs and Holm-adjusted p.

## Log
- Plan written first (above). Then 01_build.py (panel), 02_models.py, 03_results.py, 04_figures.py, 05_export.py, 06_build_site.py.
- Main result (planned spec): -0.96 points per cm (95% CI -1.82 to -0.11, two-way clusters), but wild bootstrap by election
  p = 0.14 and map-swap randomisation p = 0.10; day-before placebo -1.68 (CI -3.46 to 0.10). Reported as weak / not established.
- H2 contradicted in sign (larger after 2001); H3 null; temperature -1.87 per 10 C (Holm p 0.12).
- Deviation from plan: the wild bootstrap uses Webb six-point weights (22 clusters) instead of Rademacher (only 2^22
  sign patterns, coarse p); the equal-weight version is not reported. Everything else as planned.

## References verified online (2026)
Gomez, Hansford, Krause 2007 JOP 69(3) 649-663; Fraga and Hersh 2010 QJPS 5(4) 339-356; Eisinga et al 2012 IJB 56(4) 783-786
and 56(6) 1161-1165; Persson, Sundell, Ohrvall 2014 ES 33 335-342; Arnold and Freier 2015 DIW DP 1463; Artes 2014 EJPE 34 126-141;
Horiuchi and Kang 2018 APR 46(5) 869-889; Cooperman 2017 PA 25(3) 277-288; Meier, Schmid, Stutzer 2019 EER 119 434-451;
Fujiwara, Meng, Vogl 2016 AEJ Applied 8(4) 160-188; Knack 1994 Public Choice 79(1-2) 187-209; Lind 2020 EJPE 61;
Hansford and Gomez 2010 APSR 104(2) 268-288; Stockemer and Wigginton 2018 IJB 62(6) 1027-1037; Bassi 2019 JEPS 6(1) 17-32;
Mellon 2025 AJPS 69(3); Garcia Rodriguez and Redmond 2020 ES 64 102128; Damsbo-Svendsen and Hansen 2023 ES 81 102573;
Hersbach et al 2020 QJRMS 146 1999-2049; Munoz-Sabater et al 2021 ESSD 13 4349-4383; Zippenfenig 2023 Zenodo;
Cameron, Gelbach, Miller 2008 REStat 90(3) 414-427 and 2011 JBES 29(2) 238-249; Webb 2023 CJE 56(3) 839-858;
Blais 2006 ARPS 9 111-125; Geys 2006 ES 25(4) 637-663; Denver and Hands 1974 BJPolS 4(1) 17-35 and 1985 15(3) 381-388;
Riker and Ordeshook 1968 APSR 62(1) 25-42; Downs 1957; Gerber, Green, Shachar 2003 AJPS 47(3) 540-550; Hodler et al 2015 AEJ Policy 7(1) 141-171;
Funk 2010 JEEA 8(5) 1077-1103; Heath 2007 Pol Behav 29(4) 493-516; Rallings, Thrasher, Borisyuk 2010 BJPIR 12(2) 223-238;
Franklin 2004 CUP; Shachar and Nalebuff 1999 AER 89(3) 525-547; White 2012 HoC Library SN/PC/05517; Rallings and Thrasher 2007.
Not verifiable (dropped): Gatrell and Bierly 2002 (pages), Lasala-Blanco et al 2017, Arnold and Freier 2016 ES 41 (cited via the DIW paper instead), Lo Prete and Revelli.


## Independent review (2026)

Reproduction: reran 01 to 03 from the raw inputs; panel.csv byte-identical and results.json identical to the built version
(main -0.963, CI -1.820 to -0.106, N 13,731; wild Webb p 0.143; map-swap RI p 0.099). Hour indexing checked against
Open-Meteo's "preceding hour" convention (07 to 22 = indices 32 to 46). All public numbers are templated from results.json.

References spot-checked online (abstracts or publisher/repository pages): Damsbo-Svendsen and Hansen 2023 (0.95 points per cm,
2013 and 2017 Danish municipal elections, via videnskab.dk report and author slides); Eisinga et al. 2012a (25 mm about 1 point;
10 C about +1 point); Gomez et al. 2007 (just under 1% per inch; snow; 22,000 stations); Stockemer and Wigginton 2018 (more than
0.1 points per mm; reversed in a winter election); Lind (rain raised turnout about 0.7 points, Norway); Artes 2014; Arnold and
Freier DIW DP 1463 (NRW 1975 to 2010); Mellon AJPS 69(3) 2025; Fraga and Hersh QJPS 5(4); Persson et al. 2014; Garcia Rodriguez
and Redmond 2020; Cooperman 2017; Horiuchi and Kang 2018; Knack 1994; Zippenfenig DOI; White 2012 SN/PC/05517 (hours); Hansard
15 Mar 1945 (extension not beyond 9pm), 31 May 1945 (provisional list), 11 June 1945 (Warrington only "I am not quite sure");
Political Studies guidelines (8,000 words excl. references; no fees). Note: Arnold and Freier also appeared in Electoral
Studies 41 (2016) per a citing paper; the DIW version is cited and is accurate.

Fixed: deviation note wrongly said 2^22 Rademacher patterns give a coarse p (they do not): now reports the planned Rademacher
bootstrap (p 0.13) and that the joint placebo model replaces the planned pairwise ones; Cooperman, Stockemer, Damsbo review
and "Danish and Dutch similar" wording corrected to what the sources say; 1945 hours stated as an assumption with the March 1945
Hansard; Warrington wording softened; Holm footnote labels; Table A1 now referenced; abstract trimmed (247 words); cover note
Political Studies limit corrected and summary rewritten (151 words, adds placebo). Public copy reframed as suggestive, not
established (page heading "Maybe a little", double negative fixed, "No partisan rain" to "No sign of partisan rain", Reddit
title, meta, collage subtitle "and turnout in the same seats", GIF final box); 1945 hours marked as assumed and postponed
seats as "was, or may have been". GIF year label shrunk for "Feb/Oct 1974" (was touching the title).

Exploratory checks added at review (02_models.py, rev_*; paper section 6.4): day-before placebo wild bootstrap p 0.08 and
map-swap RI p 0.04, i.e. at least as unusual as polling-day rain; election x region FE wild p 0.05 (b -0.71); one row per
cell and election -1.17 (CI -1.93 to -0.41, 367 cells, N 6,194).

What a referee would still ask: why the eve-of-poll placebo is as strong (seasonal or regional confounding: 2019 was a December
election with wet west/north); a spatial HAC or Conley SE; finer rain (radar, Met Office HadUK-Grid daily 1 km) to test
attenuation; postal-vote share by seat after 2001; the enacted 1945 schedule; constituency boundary crosswalks rather than
name lineage; local elections for many more weather draws.
