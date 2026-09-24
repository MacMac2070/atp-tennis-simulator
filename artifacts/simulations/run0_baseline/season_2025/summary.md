# Season 2025 simulation: `run0_baseline`

Model `artifacts/models/run0_baseline/model.pt` (trained through 2024). 10,000 simulated seasons, seed 42. Season = the 2025 file year, events dated 2024-12-30 to 2025-11-09.

## What was simulated

60 events with their real draws: 4 Grand Slams, 9 Masters 1000, 16 ATP 500, 30 ATP 250, 1 ATP Finals. 2,696 entries by 292 players. Left out: 78 Davis Cup ties, United Cup, Laver Cup, Next Gen Finals.

## Match level

Every real match of the simulated events, walkovers dropped, scored with the model's pre-event probability for the real winner. No simulation involved.

|  | Matches | Accuracy | Log loss | Brier | Higher-ranked player wins |
|---|---:|---:|---:|---:|---:|
| All | 2,622 | 61.0% | 0.6895 | 0.2405 | 64.3% |
| Clay | 760 | 58.8% | 0.6938 | 0.2451 | 65.0% |
| Grass | 295 | 62.0% | 0.6550 | 0.2322 | 63.1% |
| Hard | 1,567 | 61.8% | 0.6938 | 0.2398 | 64.2% |
| ATP 250 | 826 | 57.3% | 0.7179 | 0.2553 | 59.0% |
| ATP 500 | 507 | 65.7% | 0.6468 | 0.2238 | 67.7% |
| ATP Finals | 15 | 73.3% | 0.4902 | 0.1729 | 66.7% |
| Grand Slam | 505 | 64.6% | 0.6413 | 0.2220 | 68.3% |
| Masters 1000 | 769 | 59.3% | 0.7227 | 0.2491 | 65.1% |

A coin flip scores a log loss of 0.6931. Calibration, the favourite's predicted chance against how often the favourite won:

| Favourite's chance | Matches | Predicted | Won |
|---|---:|---:|---:|
| 50% to 60% | 728 | 54.8% | 52.1% |
| 60% to 70% | 665 | 64.9% | 57.3% |
| 70% to 80% | 507 | 74.6% | 57.8% |
| 80% to 90% | 374 | 84.8% | 70.9% |
| 90% to 100% | 348 | 95.0% | 80.7% |

## Tournament level

The real champion was the simulation's favourite in 15 of 60 events and in its top three in 31. The mean simulated chance of the real champion was 16.2%.

| Event | Real champion | Sim. chance | Position | Sim. favourite | Chance |
|---|---:|---:|---:|---:|---:|
| Australian Open | Jannik Sinner | 30.9% | 1 | Jannik Sinner | 30.9% |
| Indian Wells Masters | Jack Draper | 1.4% | 9 | Alex De Minaur | 27.2% |
| Miami Masters | Jakub Mensik | 0.0% | 32 | Carlos Alcaraz | 34.3% |
| Monte Carlo Masters | Carlos Alcaraz | 30.6% | 2 | Novak Djokovic | 30.6% |
| Madrid Masters | Casper Ruud | 0.8% | 17 | Novak Djokovic | 30.9% |
| Rome Masters | Carlos Alcaraz | 19.9% | 2 | Jannik Sinner | 40.2% |
| Roland Garros | Carlos Alcaraz | 17.3% | 3 | Jannik Sinner | 38.2% |
| Wimbledon | Jannik Sinner | 18.9% | 1 | Jannik Sinner | 18.9% |
| Canada Masters | Ben Shelton | 0.5% | 18 | Alex De Minaur | 35.4% |
| Cincinnati Masters | Carlos Alcaraz | 20.2% | 2 | Jannik Sinner | 42.4% |
| US Open | Carlos Alcaraz | 43.5% | 1 | Carlos Alcaraz | 43.5% |
| Shanghai Masters | Valentin Vacherot | 0.0% | 49 | Jannik Sinner | 66.7% |
| Paris Masters | Jannik Sinner | 41.2% | 2 | Carlos Alcaraz | 41.6% |
| ATP Finals | Jannik Sinner | 39.0% | 2 | Carlos Alcaraz | 43.9% |

Grand Slams, Masters 1000 and the ATP Finals are shown; every event is in `tournaments.csv`.

## Year-end top 10

Sorted by mean simulated points. Same-table actual = the real 2025 results of the same events, scored with the simulator's points table. Official = ATP ranking of 2025-12-29.

| Player | Mean pts | 90% range | Mean rank | P(#1) | P(top 10) | Same-table actual | Official |
|---|---:|---:|---:|---:|---:|---:|---:|
| Carlos Alcaraz | 9,694 | 6,890 to 12,710 | 1.9 | 47.7% | 100.0% | 12,050 (#1) | 12,050 (#1) |
| Jannik Sinner | 8,876 | 6,230 to 11,650 | 2.4 | 28.3% | 100.0% | 11,500 (#2) | 11,500 (#2) |
| Alex De Minaur | 8,075 | 5,550 to 10,840 | 3.0 | 14.7% | 100.0% | 4,090 (#6) | 4,080 (#7) |
| Alexander Zverev | 7,791 | 5,555 to 10,260 | 3.3 | 8.3% | 100.0% | 5,225 (#3) | 5,110 (#3) |
| Novak Djokovic | 5,719 | 3,600 to 8,150 | 5.3 | 1.2% | 98.4% | 4,830 (#4) | 4,820 (#4) |
| Taylor Fritz | 4,536 | 2,910 to 6,400 | 7.0 | 0.0% | 92.9% | 3,900 (#9) | 4,085 (#6) |
| Daniil Medvedev | 4,245 | 2,680 to 6,230 | 7.7 | 0.0% | 87.8% | 2,930 (#11) | 2,710 (#13) |
| Tommy Paul | 3,494 | 2,100 to 5,215 | 10.0 | 0.0% | 65.7% | 2,100 (#21) | 2,050 (#20) |
| Felix Auger Aliassime | 3,041 | 1,980 to 4,475 | 11.7 | 0.0% | 45.0% | 4,280 (#5) | 4,190 (#5) |
| Andrey Rublev | 2,986 | 1,980 to 4,235 | 11.8 | 0.0% | 43.0% | 2,530 (#16) | 2,510 (#16) |

- Most likely #1: **Carlos Alcaraz** (47.7%). Real same-table #1: **Carlos Alcaraz**, simulated P(#1) 47.7%.
- Top-10 overlap with same-table actual: 7 of 10; with the official top 10: 7 of 10.
- Official top 50: Spearman between mean simulated points and same-table points 0.761.
- Official top 20: mean |simulated rank - same-table rank| 7.5; against the official rank 7.4; mean |points gap| 1,335.

## Rankings through the season

52-week ledger on each official ranking Monday (2024 real results, then simulated 2025 results). Mean absolute rank error for the official top 20, taken at the last ranking of each month: simulated mean rank against the official rank, and, for scale, the same-table actual rank against the official rank (the part the simplified rules alone explain).

| Month | Simulated vs official | Same-table vs official |
|---|---:|---:|
| Jan 2025 | 1.1 | 0.2 |
| Feb 2025 | 1.2 | 0.1 |
| Mar 2025 | 2.3 | 0.3 |
| Apr 2025 | 2.8 | 0.5 |
| May 2025 | 4.5 | 0.5 |
| Jun 2025 | 4.3 | 0.8 |
| Jul 2025 | 6.0 | 0.3 |
| Aug 2025 | 5.3 | 0.3 |
| Sep 2025 | 7.9 | 0.9 |
| Oct 2025 | 7.7 | 0.6 |
| Nov 2025 | 7.5 | 0.7 |
| Dec 2025 | 7.4 | 0.8 |

## Where it misses

Official top 20, largest gaps between mean simulated points and same-table actual points.

| Player | Mean simulated | Same-table actual | Gap |
|---|---:|---:|---:|
| Alex De Minaur | 8,075 | 4,090 | +3,985 |
| Alexander Zverev | 7,791 | 5,225 | +2,566 |
| Tommy Paul | 3,494 | 2,100 | +1,394 |
| Daniil Medvedev | 4,245 | 2,930 | +1,315 |
| Jannik Sinner | 8,876 | 11,500 | -2,624 |
| Carlos Alcaraz | 9,694 | 12,050 | -2,356 |
| Ben Shelton | 1,873 | 3,970 | -2,097 |
| Alexander Bublik | 885 | 2,625 | -1,740 |

## Limitations

- Form cards are frozen at each event's real start date and built from real results only; simulated results never change later cards. Tournaments are linked through ranking points alone, so this is an A/B test of the serve model, not a closed fantasy season.
- Every real entrant plays and nobody else does: injuries, withdrawals and retirements are not simulated, and every match is played to a finish. Real walkovers are simulated as matches.
- Ranking rules are simplified: every simulated event counts in full. No best-19 rule, mandatory-event zero-pointers or protected rankings, and no points from Challengers, qualifying or the United Cup. Year-end figures are therefore compared with the same-table actual race first and the official ranking second.
- ATP Finals: the real 2025 groups are fixed (qualification is not simulated). Groups are ordered by wins, head-to-head and percentage of sets won; percentage of games won is not simulated, so an unbroken three-way tie falls to the ranking at entry.
- Points enter the ledger on the Monday after the event's estimated last day and drop 52 weeks later. The 2024 part of the ledger is the real 2024 results scored with the same table.
- Team events (Davis Cup, United Cup, Laver Cup) and the Next Gen Finals are not simulated and are left out of the actual side too.

## Files

| File | Contents |
|---|---|
| `config.json` | Season, seed, simulation count, model path and hash, code commit, event counts |
| `metrics.json` | Every headline number on this page, machine-readable |
| `matches.csv` | One row per real match: both serve probabilities, P(real winner), log loss and Brier score |
| `tournaments.csv` | One row per event: real champion, simulated chance, simulated favourite |
| `rankings_year_end.csv` | One row per player: simulated points and rank distribution, same-table and official |
| `rankings_weekly.csv` | Official top 30 on each ranking Monday: simulated, same-table and official rank |
