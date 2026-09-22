# Model progression index

**Story:** Run 0 = first idea. Run 1 = improvement, scored on the same holdout to see if it is actually better.
Both frozen. Future season simulations use the same run names under `artifacts/simulations/`.

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
    run0_baseline/                 # reserved — no sim yet
    run1_season_delta/             # reserved — no sim yet

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

## Simulations (not started)

When building the simulator, always run **both** Run 0 and Run 1 with the same seeds, writing to the matching `artifacts/simulations/run*/` folders so GitHub shows a clear A/B layout.
