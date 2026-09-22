# ATP Tour website spot check (12 random matches)

Sample: 3 matches per decade, drawn with `random_state=20260921` from tour-level main-draw matches
(levels G, M, A, F) with serve stats, excluding walkovers and retirements. Drawn before any website
was opened. Rows saved in `atp_spot_check_sample.csv`. Checked on atptour.com on 2026-09-21.

Fields compared for both players: winner, score, round, aces, double faults, 1st serves in / total
service points, 1st serve points won, 2nd serve points won, break points saved / faced, duration.

| Decade | Match | Winner, score, round | All 16 serve stats | Duration (Sackmann / ATP) | ATP page |
|---|---|---|---|---|---|
| 1990s | US Open 1999 R128, Bastl d. Squillari | match | identical | 182 / 182 | /en/scores/match-stats/archive/1999/560/ms118 |
| 1990s | Prague 1992 R32, Krumrey d. Viver | match | identical | 147 / 147 | /en/scores/match-stats/archive/1992/379/ms026 |
| 1990s | Roland Garros 1997 R128, Lapentti d. Fetterlein | match | identical | 110 / 110 | /en/scores/match-stats/archive/1997/520/ms109 |
| 2000s | Stuttgart 2004 F, Canas d. Gaudio | match | identical | 220 / 220 | /en/scores/match-stats/archive/2004/321/ms001 |
| 2000s | Basel 2003 SF, Coria d. Ljubicic | match | identical | 77 / 77 | /en/scores/match-stats/archive/2003/328/ms003 |
| 2000s | Queen's Club 2003 R32, Malisse d. Karlovic | match | identical | 77 / 77 | /en/scores/match-stats/archive/2003/311/ms028 |
| 2010s | Nice 2016 QF, Sousa d. Anderson | match | identical | **97 / 98** | /en/scores/match-stats/archive/2016/6120/ms006 |
| 2010s | Geneva 2016 R32, Bellucci d. Kukushkin | match | identical | **67 / 68** | /en/scores/match-stats/archive/2016/322/ms025 |
| 2010s | Barcelona 2014 R16, Nadal d. Dodig | match | identical | 84 / 84 | /en/scores/match-stats/archive/2014/425/ms008 |
| 2020s | Madrid 2024 R128, Fonseca d. Michelsen | match | identical | **121 / 122** | /en/scores/stats-centre/archive/2024/1536/ms077 |
| 2020s | Wimbledon 2023 R128, Thompson d. Nakashima | match | identical | 210 / 210 | /en/scores/match-stats/archive/2023/540/ms126 |
| 2020s | Shanghai 2023 R64, Khachanov d. Zhukayev | match | identical | 122 / 122 | /en/scores/stats-centre/archive/2023/5014/ms035 |

Result: 12 of 12 agree on winner, score, round and every serve statistic (192 of 192 numbers).
Three durations differ by one minute; the model does not use duration.

## Extra, not random: two matches where Sackmann and TML disagree (Australian Open 2026 R128)

| Match | Stat (winner) | Sackmann | TML | ATP website |
|---|---|---|---|---|
| Hijikata d. Mannarino | 1st serves in / service points | 55 / 89 | 87 / 92 | 87 / 92 |
| Hijikata d. Mannarino | 1st won, 2nd won | 43, 17 | 59, 1 | 59, 1 |
| Cilic d. Altmaier | 1st serves in / service points | 40 / 71 | 53 / 72 | 53 / 72 |
| Cilic d. Altmaier | 1st won, 2nd won | 35, 20 | 44, 11 | 44, 11 |

TML matches the ATP website exactly here, so TML is scraping atptour.com. But the ATP numbers are not
believable for these Grand Slam matches (95% of first serves in, "0 service games played"), while
Sackmann's are plausible. Grand Slams are run by the ITF, not the ATP, and the ATP site's Slam feed
looks faulty. Total serve points won is the same in both (60 for Hijikata), so the effect on the
model's target is a few service points per match. The true figures would need the Slam's own site.
