# Model progression index

**Story:** Run 0 = first idea. Run 1 = improvement, scored on the same holdout to see if it is actually better.
Both frozen. Season simulations use the same run names under `artifacts/simulations/`.

| Run | Weights | Eval | Formula | Train through | Holdout bias (Hard, all) | Status |
|---|---|---|---|---|---|---|
| **0** | [`artifacts/models/run0_baseline`](../../artifacts/models/run0_baseline/) | [`eval.md`](run0_baseline/eval.md) | `μ + a·x − b·x + xᵀWx` | 2024 | **−0.0186** | Frozen |
| **1** | [`artifacts/models/run1_season_delta`](../../artifacts/models/run1_season_delta/) | [`eval.md`](run1_season_delta/eval.md) | Train with `δ_season` (`δ_2024=0`); save so `μ` = 2024 level | 2024 | **−0.0078** (2025: −0.0042) | Frozen |

## Folder layout

```text
artifacts/
  models/
    run0_baseline/model.pt + README.md
    run1_season_delta/model.pt + README.md
    archive/                       # side experiments
  simulations/
    run0_baseline/season_2025/     # 10,000 seasons, seed 42
    run1_season_delta/season_2025/ # same seasons and seed, Run 1 weights

verification/reports/
  MODEL_PROGRESSION.md             # this index
  run0_baseline/eval.md
  run1_season_delta/eval.md        # includes delta vs Run 0
```

Shared training table: `runs/rows.parquet` (gitignored) — not copied per run.
Explainer for Run 1: `docs/serve_level_fix.md`.

## How to add Run N

1. Train → `artifacts/models/runN_<name>/model.pt` + README
2. Eval → `verification/reports/runN_<name>/eval.md` (same tables + vs previous run)
3. Reserve `artifacts/simulations/runN_<name>/` for later sim outputs
4. Add a row to the table above
5. Optional: copy favourite weights to `runs/model.pt` for default scripts

## Simulations

Both runs replay the 2025 season (60 events, real draws) 10,000 times with seed 42 and the same random numbers, so only the model differs. Full comparison: [`simulations_2025.md`](simulations_2025.md). How it works: [`docs/season_simulation.md`](../../docs/season_simulation.md).

| Run | Match accuracy | Match log loss | Real champion favourite | Most likely year-end #1 | Rank error, top 20 | Outputs |
|---|---:|---:|---:|---|---:|---|
| **0** | 61.0% | 0.6895 | 15 of 60 | Alcaraz (47.7%) | 7.5 | [`season_2025/`](../../artifacts/simulations/run0_baseline/season_2025/) |
| **1** | 61.6% | 0.6545 | 17 of 60 | Sinner (70.9%) | 6.6 | [`season_2025/`](../../artifacts/simulations/run1_season_delta/season_2025/) |

Reference: the higher-ranked player won 64.3% of the same 2,622 matches; the real year-end #1 was Alcaraz. Always run every model with the same season, seed and simulation count.
