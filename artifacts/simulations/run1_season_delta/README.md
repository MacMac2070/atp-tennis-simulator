# Simulations: run1_season_delta

Weights: `artifacts/models/run1_season_delta/model.pt` (trained through 2024, sha256 `10d2f7c68eb4`).

| Folder | Season | Seasons simulated | Seed | Status |
|---|---|---:|---:|---|
| `season_2025/` | 2025 file year | 10,000 | 42 | Done |

## Headline

- Match level: accuracy 61.6%, log loss 0.6545, Brier 0.2301 on 2,622 real matches (higher-ranked player wins 64.3%).
- Titles: real champion was the favourite in 17 of 60 events, in the top three in 27.
- Year end: most likely #1 Jannik Sinner (70.9%); the real #1 Carlos Alcaraz finished #1 in 18.5% of simulated seasons.

Full write-up: `season_2025/summary.md`. Comparison with the other runs: `verification/reports/simulations_2025.md`.

## Reproduce

```bash
python scripts/simulate_season.py --model artifacts/models/run1_season_delta/model.pt --season 2025 --n-sims 10000 --seed 42 --out artifacts/simulations/run1_season_delta/season_2025/
```

Other runs use the same season, seed and simulation count, so only the model differs.
