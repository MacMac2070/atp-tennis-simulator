# Season 2025 simulation: run1_season_delta

Model `artifacts/models/run1_season_delta/model.pt` (trained through 2024). 10,000 simulated seasons, seed 42. Season = the 2025 file year, events dated 2024-12-30 to 2025-11-09.

## What was simulated

60 events with their real draws: 4 Grand Slams, 9 Masters 1000, 16 ATP 500, 30 ATP 250, 1 ATP Finals. 2,696 entries by 292 players. Left out: 78 Davis Cup ties, United Cup, Laver Cup, Next Gen Finals.

## Match level

Every real match of the simulated events, walkovers dropped, scored with the model's pre-event probability for the real winner. No simulation involved.

|  | Matches | Accuracy | Log loss | Brier | Higher-ranked player wins |
|---|---:|---:|---:|---:|---:|
| All | 2,622 | 61.6% | 0.6545 | 0.2301 | 64.3% |
| Clay | 760 | 60.4% | 0.6527 | 0.2305 | 65.0% |
| Grass | 295 | 60.7% | 0.6575 | 0.2329 | 63.1% |
| Hard | 1,567 | 62.3% | 0.6547 | 0.2294 | 64.2% |
| 250 | 826 | 56.3% | 0.6983 | 0.2507 | 59.0% |
| 500 | 507 | 63.1% | 0.6267 | 0.2186 | 67.7% |
| F | 15 | 86.7% | 0.3546 | 0.1026 | 66.7% |
| G | 505 | 68.1% | 0.5867 | 0.2036 | 68.3% |
| M | 769 | 61.4% | 0.6760 | 0.2355 | 65.1% |

A coin flip scores a log loss of 0.6931. Calibration, favourite's predicted chance against how often the favourite won:

| Favourite's chance | Matches | Predicted | Won |
|---|---:|---:|---:|
| (0.499, 0.6] | 818 | 55.0% | 51.5% |
| (0.6, 0.7] | 689 | 64.9% | 55.7% |
| (0.7, 0.8] | 521 | 74.6% | 64.7% |
| (0.8, 0.9] | 356 | 84.4% | 74.4% |
| (0.9, 1.0] | 238 | 94.7% | 87.0% |

## Tournament level

Real champion was the simulation's favourite in 17 of 60 events and in its top three in 27. Mean simulated chance of the real champion 18.4%.

| Event | Real champion | Sim. chance | Position | Sim. favourite | Chance |
|---|---:|---:|---:|---:|---:|
| Australian Open | Jannik Sinner | 54.0% | 1 | Jannik Sinner | 54.0% |
| Indian Wells Masters | Jack Draper | 1.7% | 12 | Alexander Zverev | 20.3% |
| Miami Masters | Jakub Mensik | 0.1% | 35 | Carlos Alcaraz | 24.9% |
| Monte Carlo Masters | Carlos Alcaraz | 36.4% | 1 | Carlos Alcaraz | 36.4% |
| Madrid Masters | Casper Ruud | 1.2% | 14 | Alex De Minaur | 22.4% |
| Rome Masters | Carlos Alcaraz | 27.4% | 2 | Jannik Sinner | 36.2% |
| Roland Garros | Carlos Alcaraz | 36.4% | 2 | Jannik Sinner | 38.6% |
| Wimbledon | Jannik Sinner | 44.6% | 1 | Jannik Sinner | 44.6% |
| Canada Masters | Ben Shelton | 1.2% | 10 | Alexander Zverev | 32.5% |
| Cincinnati Masters | Carlos Alcaraz | 19.0% | 2 | Jannik Sinner | 55.6% |
| Us Open | Carlos Alcaraz | 20.5% | 2 | Jannik Sinner | 60.7% |
| Shanghai Masters | Valentin Vacherot | 0.0% | 52 | Jannik Sinner | 63.8% |
| Paris Masters | Jannik Sinner | 63.4% | 1 | Jannik Sinner | 63.4% |
| Tour Finals | Jannik Sinner | 67.8% | 1 | Jannik Sinner | 67.8% |

Slams, Masters and the ATP Finals shown; every event is in `tournaments.csv`.

## Year-end top 10

Sorted by mean simulated points. Same-table actual = the real 2025 results of the same events, scored with the simulator's points table. Official = ATP ranking of 2025-12-29.

| Player | Mean pts | 90% range | Mean rank | P(#1) | P(top 10) | Same-table actual | Official |
|---|---:|---:|---:|---:|---:|---:|---:|
| Jannik Sinner | 10,757 | 7,950 to 13,350 | 1.4 | 70.9% | 100.0% | 11,500 (#2) | 11,500 (#2) |
| Carlos Alcaraz | 8,753 | 6,040 to 11,600 | 2.4 | 18.5% | 100.0% | 12,050 (#1) | 12,050 (#1) |
| Alexander Zverev | 8,131 | 5,600 to 10,895 | 2.8 | 10.0% | 100.0% | 5,225 (#3) | 5,110 (#3) |
| Alex De Minaur | 5,657 | 3,770 to 7,870 | 5.0 | 0.4% | 99.2% | 4,090 (#6) | 4,080 (#7) |
| Novak Djokovic | 5,284 | 3,235 to 7,600 | 5.7 | 0.3% | 96.4% | 4,830 (#4) | 4,820 (#4) |
| Taylor Fritz | 5,035 | 3,250 to 7,105 | 6.0 | 0.1% | 96.7% | 3,900 (#9) | 4,085 (#6) |
| Daniil Medvedev | 3,971 | 2,530 to 5,730 | 8.2 | 0.0% | 82.9% | 2,930 (#11) | 2,710 (#13) |
| Felix Auger Aliassime | 3,736 | 2,345 to 5,440 | 9.0 | 0.0% | 75.4% | 4,280 (#5) | 4,190 (#5) |
| Andrey Rublev | 3,449 | 2,220 to 4,950 | 9.8 | 0.0% | 66.9% | 2,530 (#16) | 2,510 (#16) |
| Tommy Paul | 3,027 | 1,765 to 4,690 | 12.3 | 0.0% | 44.4% | 2,100 (#21) | 2,050 (#20) |

- Most likely #1: **Jannik Sinner** (70.9%). Real same-table #1: **Carlos Alcaraz**, simulated P(#1) 18.5%.
- Top-10 overlap with same-table actual: 7 of 10; with the official top 10: 7 of 10.
- Official top 50: Spearman between mean simulated points and same-table points 0.785.
- Official top 20: mean |simulated rank - same-table rank| 6.6; against the official rank 6.4; mean |points gap| 1,118.

## Rankings through the season

52-week ledger on each official ranking Monday (2024 real results, then simulated 2025 results). Mean absolute rank error for the official top 20, taken at the last ranking of each month: simulated mean rank against the official rank, and, for scale, the same-table actual rank against the official rank (the part the simplified rules alone explain).

| Month | Simulated v official | Same-table v official |
|---|---:|---:|
| Jan 2025 | 1.1 | 0.2 |
| Feb 2025 | 1.0 | 0.1 |
| Mar 2025 | 2.0 | 0.3 |
| Apr 2025 | 2.9 | 0.5 |
| May 2025 | 4.3 | 0.5 |
| Jun 2025 | 4.0 | 0.8 |
| Jul 2025 | 5.7 | 0.3 |
| Aug 2025 | 5.0 | 0.3 |
| Sep 2025 | 7.4 | 0.9 |
| Oct 2025 | 6.8 | 0.6 |
| Nov 2025 | 6.5 | 0.7 |
| Dec 2025 | 6.4 | 0.8 |

## Where it misses

Official top 20, largest gaps between mean simulated points and same-table actual points.

| Player | Mean simulated | Same-table actual | Gap |
|---|---:|---:|---:|
| Alexander Zverev | 8,131 | 5,225 | +2,906 |
| Alex De Minaur | 5,657 | 4,090 | +1,567 |
| Taylor Fritz | 5,035 | 3,900 | +1,135 |
| Daniil Medvedev | 3,971 | 2,930 | +1,041 |
| Carlos Alcaraz | 8,753 | 12,050 | -3,297 |
| Ben Shelton | 2,244 | 3,970 | -1,726 |
| Alexander Bublik | 1,068 | 2,625 | -1,557 |
| Lorenzo Musetti | 2,676 | 4,060 | -1,384 |

## Limitations

- Form cards are frozen at each event's real start date and built from real results only; simulated results never change later cards. Tournaments are linked through ranking points alone, so this is an A/B test of the serve model, not a closed fantasy season.
- Every real entrant plays and nobody else does: injuries, withdrawals and retirements are not simulated, and every match is played to a finish. Real walkovers are simulated as matches.
- Ranking rules are simplified: every simulated event counts in full. No best-19 rule, mandatory-event zero-pointers or protected rankings, and no points from Challengers, qualifying, the United Cup or Davis Cup. Year-end figures are therefore compared with the same-table actual race first and the official ranking second.
- ATP Finals: the real 2025 groups are fixed (qualification is not simulated). Groups are ordered by wins, head-to-head and sets won %; games won % is not simulated, so an unbroken three-way tie falls to the ranking at entry.
- Points enter the ledger on the Monday after the event's estimated last day and drop 52 weeks later. The 2024 part of the ledger is the real 2024 results scored with the same table.
- Team events (Davis Cup, United Cup, Laver Cup) and the Next Gen Finals are not simulated and are left out of the actual side too.

## Files

| File | Contents |
|---|---|
| `config.json` | Season, seed, simulation count, model path and hash, code commit, event counts |
| `metrics.json` | Every headline number on this page, machine-readable |
| `matches.csv` | One row per real match: both serve probabilities, P(real winner), scores |
| `tournaments.csv` | One row per event: real champion, simulated chance, simulated favourite |
| `rankings_year_end.csv` | One row per player: simulated points and rank distribution, same-table and official |
| `rankings_weekly.csv` | Official top 30 on each ranking Monday: simulated, same-table and official rank |
