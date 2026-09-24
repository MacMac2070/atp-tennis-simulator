# Simulations: `run0_baseline`

Weights: `artifacts/models/run0_baseline/model.pt` (trained through 2024, sha256 `25f1b647dae6`).

| Folder | Season | Seasons simulated | Seed | Status |
|---|---|---:|---:|---|
| `season_2025/` | 2025 file year | 10,000 | 42 | Done |

## Headline

- Match level: accuracy 61.0%, log loss 0.6895, Brier 0.2405 on 2,622 real matches (higher-ranked player wins 64.3%).
- Titles: real champion was the favourite in 15 of 60 events, in the top three in 31.
- Year end: most likely #1 Carlos Alcaraz (47.7%); the real #1 Carlos Alcaraz finished #1 in 47.7% of simulated seasons.

Full write-up: `season_2025/summary.md`. Comparison of all runs: `verification/reports/simulations_2025.md`.

## Reproduce

```bash
python scripts/simulate_season.py --model artifacts/models/run0_baseline/model.pt --season 2025 --n-sims 10000 --seed 42 --out runs/simulations/run0_baseline/season_2025/
```

Writes to `runs/` (gitignored); every CSV file and `metrics.json` should match `season_2025/` here byte for byte.
Other runs use the same season, seed and simulation count, so only the model differs.
