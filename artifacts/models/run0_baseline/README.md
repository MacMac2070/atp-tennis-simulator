# Run 0: baseline bilinear serve model

Frozen snapshot of the first full train + holdout eval.

| Item | Value |
|---|---|
| Formula | `z = μ + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ` (no season intercept) |
| Train through | 2024 |
| Holdout | 2025 + partial 2026 |
| Weights | `model.pt` (this folder) |
| Eval write-up | `verification/reports/run0_baseline/eval.md` |

Do not overwrite these files. Later runs go in `run1_…`, `run2_…`.

Reproduce: Run 0 predates the season intercept. `scripts/train_model.py` now always fits the
Run 1 recipe (one level per season, with the learning-rate cool-down on by default), so these
weights are kept as the record and are not regenerated. The holdout evaluation can be re-run
on them:

```bash
python scripts/evaluate_model.py --rows runs/rows.parquet \
    --model artifacts/models/run0_baseline/model.pt
```

Simulation outputs: `artifacts/simulations/run0_baseline/` (the 2025 season simulated 10,000 times).
