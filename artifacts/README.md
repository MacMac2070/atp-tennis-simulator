# Artefacts: model runs and simulations

This folder is the **versioned history** of the project's modelling work.

## The story

| Run | Idea | Role |
|---|---|---|
| **Run 0** (`run0_baseline`) | First model trained: one baseline `μ` per surface, fitted on 1992 to 2024 | Baseline to beat |
| **Run 1** (`run1_season_delta`) | Same prediction formula; train so `μ` = 2024 serve level | Improvement to compare against Run 0 |

Both are **frozen**. Do not overwrite. New ideas become `run2_…`, `run3_…`.

## Layout

```text
artifacts/
  models/
    run0_baseline/     model.pt + README.md
    run1_season_delta/ model.pt + README.md
  simulations/
    run0_baseline/     README.md + season_2025/ (10,000 seasons with Run 0 weights)
    run1_season_delta/ README.md + season_2025/ (same seasons, Run 1 weights)
```

Each `season_2025/` holds `config.json`, `metrics.json`, `summary.md`, `matches.csv`,
`tournaments.csv`, `rankings_year_end.csv` and `rankings_weekly.csv`, with the same
columns in both runs. Run 0 vs Run 1 vs actual: `verification/reports/simulations_2025.md`.
How the simulator works: `docs/season_simulation.md`.

Each `config.json` records `code.commit` (224f503) as the local commit the run was made from,
while the simulator code was not yet committed (`code_uncommitted: true`); 224f503 is not in
the public history. `code.committed_as` (9cd3984) is the public commit that holds the same code.

Eval write-ups (tables, bias, vs previous run):

```text
verification/reports/
  MODEL_PROGRESSION.md      ← index
  run0_baseline/eval.md
  run1_season_delta/eval.md
```

Shared training table (large, gitignored; built by `scripts/build_rows.py`): `runs/rows.parquet`.

## Comparing runs

Same simulator, different `--model`. To reproduce the frozen runs without touching them,
write into `runs/` (gitignored):

```bash
python scripts/simulate_season.py --model artifacts/models/run0_baseline/model.pt \
    --season 2025 --n-sims 10000 --seed 42 --out runs/simulations/run0_baseline/season_2025/
python scripts/simulate_season.py --model artifacts/models/run1_season_delta/model.pt \
    --season 2025 --n-sims 10000 --seed 42 --out runs/simulations/run1_season_delta/season_2025/
python scripts/compare_simulations.py --season 2025 --out runs/simulations/simulations_2025.md \
    runs/simulations/run0_baseline runs/simulations/run1_season_delta
```

Every CSV file and `metrics.json` should match the frozen copies byte for byte. Keep the
season, seed and simulation count the same so only the serve model changes:
`compare_simulations.py` refuses runs that differ in season, seed, simulation count or code
commit. A new run that is kept gets its own `run2_…` folder here.

## Default working copy

`runs/model.pt` (local, gitignored) may hold a copy of the current favourite for quick scripts.
Canonical history is always under `artifacts/models/run*/`.
