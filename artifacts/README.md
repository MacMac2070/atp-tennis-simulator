# Artefacts — model runs and simulations

This folder is the **versioned history** of the project’s modelling work.

## The story

| Run | Idea | Role |
|---|---|---|
| **Run 0** (`run0_baseline`) | First model trained: one surface baseline `μ` for all years | Baseline to beat |
| **Run 1** (`run1_season_delta`) | Same prediction formula; train so `μ` = 2024 serve level | Improvement to compare against Run 0 |

Both are **frozen**. Do not overwrite. New ideas become `run2_…`, `run3_…`.

## Layout

```text
artifacts/
  models/
    run0_baseline/     model.pt + README.md
    run1_season_delta/ model.pt + README.md
    archive/           side cuts (e.g. train-through 2023)
  simulations/
    run0_baseline/     README.md + season_2025/ (10,000 seasons with Run 0 weights)
    run1_season_delta/ README.md + season_2025/ (same seasons, Run 1 weights)
```

Each `season_2025/` holds `config.json`, `metrics.json`, `summary.md`, `matches.csv`,
`tournaments.csv`, `rankings_year_end.csv` and `rankings_weekly.csv`, with the same
columns in both runs. Run 0 vs Run 1 vs actual: `verification/reports/simulations_2025.md`.
How the simulator works: `docs/season_simulation.md`.

Eval write-ups (tables, bias, vs previous run):

```text
verification/reports/
  MODEL_PROGRESSION.md      ← index
  run0_baseline/eval.md
  run1_season_delta/eval.md
```

Shared training table (large, gitignored): `runs/rows.parquet`.

## Comparing runs

Same simulator, different `--model`:

```bash
python scripts/simulate_season.py --model artifacts/models/run0_baseline/model.pt \
    --season 2025 --n-sims 10000 --seed 42 --out artifacts/simulations/run0_baseline/season_2025/
python scripts/simulate_season.py --model artifacts/models/run1_season_delta/model.pt \
    --season 2025 --n-sims 10000 --seed 42 --out artifacts/simulations/run1_season_delta/season_2025/
python scripts/compare_simulations.py --season 2025 \
    artifacts/simulations/run0_baseline artifacts/simulations/run1_season_delta
```

Use the **same seeds / draws** so only the serve model changes. `compare_simulations.py`
refuses runs that differ in season, seed, simulation count or code commit.

## Default working copy

`runs/model.pt` may point at the current favourite for quick scripts.
Canonical history is always under `artifacts/models/run*/`.
