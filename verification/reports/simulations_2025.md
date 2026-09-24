# 2025 season simulations: `run0_baseline` vs `run1_season_delta` vs actual

Same 60 events, real draws, form cards, seed 42 and 10,000 simulated seasons for every run; only the serve model differs (common random numbers: each match slot draws the same random number in every run). Code: commit `f7bc0ec`. The runs were made on this code just before it was committed; every CSV file and `metrics.json` was reproduced byte for byte from the committed code on 24 September 2026.

| Run | Model | Trained through | sha256 |
|---|---:|---:|---:|
| run0_baseline | `artifacts/models/run0_baseline/model.pt` | 2024 | `25f1b647dae6` |
| run1_season_delta | `artifacts/models/run1_season_delta/model.pt` | 2024 | `10d2f7c68eb4` |

## Match level

2,622 real matches of the simulated events (walkovers dropped), each scored with the model's pre-event probability for the real winner. No simulation involved: the cleanest test of the serve model. A coin flip scores log loss 0.6931.

|  | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| run0_baseline | 61.0% | 0.6895 | 0.2405 |
| run1_season_delta | 61.6% | 0.6545 | 0.2301 |
| Higher-ranked player wins | 64.3% |  |  |

Log loss by surface and category:

| Group | Matches | run0_baseline | run1_season_delta |
|---|---:|---:|---:|
| Clay | 760 | 0.6938 | 0.6527 |
| Grass | 295 | 0.6550 | 0.6575 |
| Hard | 1,567 | 0.6938 | 0.6547 |
| ATP 250 | 826 | 0.7179 | 0.6983 |
| ATP 500 | 507 | 0.6468 | 0.6267 |
| ATP Finals | 15 | 0.4902 | 0.3546 |
| Grand Slam | 505 | 0.6413 | 0.5867 |
| Masters 1000 | 769 | 0.7227 | 0.6760 |

## Tournament level

|  | Real champion was the favourite | Real champion in top 3 | Mean P(real champion) | Title log loss |
|---|---:|---:|---:|---:|
| run0_baseline | 15 of 60 | 31 | 16.2% | 3.002 |
| run1_season_delta | 17 of 60 | 27 | 18.4% | 2.855 |

Grand Slams, Masters 1000 and the ATP Finals: simulated chance of the real champion, and each run's favourite.

| Event | Real champion | run0_baseline chance | run0_baseline favourite | run1_season_delta chance | run1_season_delta favourite |
|---|---:|---:|---:|---:|---:|
| Australian Open | Jannik Sinner | 30.9% | Jannik Sinner (30.9%) | 54.0% | Jannik Sinner (54.0%) |
| Indian Wells Masters | Jack Draper | 1.4% | Alex De Minaur (27.2%) | 1.7% | Alexander Zverev (20.3%) |
| Miami Masters | Jakub Mensik | 0.0% | Carlos Alcaraz (34.3%) | 0.1% | Carlos Alcaraz (24.9%) |
| Monte Carlo Masters | Carlos Alcaraz | 30.6% | Novak Djokovic (30.6%) | 36.4% | Carlos Alcaraz (36.4%) |
| Madrid Masters | Casper Ruud | 0.8% | Novak Djokovic (30.9%) | 1.2% | Alex De Minaur (22.4%) |
| Rome Masters | Carlos Alcaraz | 19.9% | Jannik Sinner (40.2%) | 27.4% | Jannik Sinner (36.2%) |
| Roland Garros | Carlos Alcaraz | 17.3% | Jannik Sinner (38.2%) | 36.4% | Jannik Sinner (38.6%) |
| Wimbledon | Jannik Sinner | 18.9% | Jannik Sinner (18.9%) | 44.6% | Jannik Sinner (44.6%) |
| Canada Masters | Ben Shelton | 0.5% | Alex De Minaur (35.4%) | 1.2% | Alexander Zverev (32.5%) |
| Cincinnati Masters | Carlos Alcaraz | 20.2% | Jannik Sinner (42.4%) | 19.0% | Jannik Sinner (55.6%) |
| US Open | Carlos Alcaraz | 43.5% | Carlos Alcaraz (43.5%) | 20.5% | Jannik Sinner (60.7%) |
| Shanghai Masters | Valentin Vacherot | 0.0% | Jannik Sinner (66.7%) | 0.0% | Jannik Sinner (63.8%) |
| Paris Masters | Jannik Sinner | 41.2% | Carlos Alcaraz (41.6%) | 63.4% | Jannik Sinner (63.4%) |
| ATP Finals | Jannik Sinner | 39.0% | Carlos Alcaraz (43.9%) | 67.8% | Jannik Sinner (67.8%) |

## Year end

Same-table actual = the real 2025 results of the same events scored with the simulator's points table; official = ATP ranking of 2025-12-29. Real top 10 by same-table points.

| Player | Same-table actual | Official | run0_baseline mean pts | run0_baseline mean rank | run0_baseline P(#1) | run1_season_delta mean pts | run1_season_delta mean rank | run1_season_delta P(#1) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Carlos Alcaraz | 12,050 | #1 | 9,694 | 1.9 | 47.7% | 8,753 | 2.4 | 18.5% |
| Jannik Sinner | 11,500 | #2 | 8,876 | 2.4 | 28.3% | 10,757 | 1.4 | 70.9% |
| Alexander Zverev | 5,225 | #3 | 7,791 | 3.3 | 8.3% | 8,131 | 2.8 | 10.0% |
| Novak Djokovic | 4,830 | #4 | 5,719 | 5.3 | 1.2% | 5,284 | 5.7 | 0.3% |
| Felix Auger Aliassime | 4,280 | #5 | 3,041 | 11.7 | 0.0% | 3,736 | 9.0 | 0.0% |
| Alex De Minaur | 4,090 | #7 | 8,075 | 3.0 | 14.7% | 5,657 | 5.0 | 0.4% |
| Lorenzo Musetti | 4,060 | #8 | 2,796 | 13.0 | 0.0% | 2,676 | 14.3 | 0.0% |
| Ben Shelton | 3,970 | #9 | 1,873 | 22.4 | 0.0% | 2,244 | 17.9 | 0.0% |
| Taylor Fritz | 3,900 | #6 | 4,536 | 7.0 | 0.0% | 5,035 | 6.0 | 0.1% |
| Jack Draper | 2,990 | #10 | 2,311 | 18.5 | 0.0% | 2,426 | 17.3 | 0.0% |

|  | Most likely #1 | P(real #1) | Top-10 overlap (same-table) | Top-10 overlap (official) | Spearman, official top 50 | Rank error vs same-table, official top 20 |
|---|---:|---:|---:|---:|---:|---:|
| run0_baseline | Carlos Alcaraz (47.7%) | 47.7% | 7 of 10 | 7 of 10 | 0.761 | 7.5 |
| run1_season_delta | Jannik Sinner (70.9%) | 18.5% | 7 of 10 | 7 of 10 | 0.785 | 6.6 |

## Rankings through the season

Mean absolute gap between simulated mean rank and official rank, official top 20, last ranking of each month. The same-table column is the part the simplified ranking rules alone explain.

| Month | run0_baseline | run1_season_delta | Same-table |
|---|---:|---:|---:|
| Jan 2025 | 1.1 | 1.1 | 0.2 |
| Feb 2025 | 1.2 | 1.0 | 0.1 |
| Mar 2025 | 2.3 | 2.0 | 0.3 |
| Apr 2025 | 2.8 | 2.9 | 0.5 |
| May 2025 | 4.5 | 4.3 | 0.5 |
| Jun 2025 | 4.3 | 4.0 | 0.8 |
| Jul 2025 | 6.0 | 5.7 | 0.3 |
| Aug 2025 | 5.3 | 5.0 | 0.3 |
| Sep 2025 | 7.9 | 7.4 | 0.9 |
| Oct 2025 | 7.7 | 6.8 | 0.6 |
| Nov 2025 | 7.5 | 6.5 | 0.7 |
| Dec 2025 | 7.4 | 6.4 | 0.8 |

## Limitations (all runs)

- Form cards are frozen at each event's real start date and built from real results only; simulated results never change later cards. Tournaments are linked through ranking points alone, so this is an A/B test of the serve model, not a closed fantasy season.
- Every real entrant plays and nobody else does: injuries, withdrawals and retirements are not simulated, and every match is played to a finish. Real walkovers are simulated as matches.
- Ranking rules are simplified: every simulated event counts in full. No best-19 rule, mandatory-event zero-pointers or protected rankings, and no points from Challengers, qualifying or the United Cup. Year-end figures are therefore compared with the same-table actual race first and the official ranking second.
- ATP Finals: the real 2025 groups are fixed (qualification is not simulated). Groups are ordered by wins, head-to-head and percentage of sets won; percentage of games won is not simulated, so an unbroken three-way tie falls to the ranking at entry.
- Points enter the ledger on the Monday after the event's estimated last day and drop 52 weeks later. The 2024 part of the ledger is the real 2024 results scored with the same table.
- Team events (Davis Cup, United Cup, Laver Cup) and the Next Gen Finals are not simulated and are left out of the actual side too.

## Reproduce

Writes to `runs/` (gitignored), so the frozen files are never overwritten; every CSV file and `metrics.json` should match them byte for byte.

```bash
python scripts/simulate_season.py --model artifacts/models/run0_baseline/model.pt --season 2025 --n-sims 10000 --seed 42 --out runs/simulations/run0_baseline/season_2025/
python scripts/simulate_season.py --model artifacts/models/run1_season_delta/model.pt --season 2025 --n-sims 10000 --seed 42 --out runs/simulations/run1_season_delta/season_2025/
python scripts/compare_simulations.py --season 2025 --out runs/simulations/simulations_2025.md runs/simulations/run0_baseline runs/simulations/run1_season_delta
```
