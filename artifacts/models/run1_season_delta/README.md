# Run 1 — serve level anchored on the last training season

Frozen snapshot of the second train + holdout eval. One change against Run 0.

| Item | Value |
|---|---|
| Prediction formula | `z = μ + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ` (identical to Run 0) |
| Training formula | `z = μ + δ_season + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ`, `δ_2024 = 0` |
| What changed | `μ` now means the 2024 serve level, not the 1992 to 2024 average. `δ` is discarded on save |
| Train through | 2024 |
| Holdout | 2025 + partial 2026 |
| Parameters saved | 243 (81 × Hard / Clay / Grass), same as Run 0 |
| Recipe | 40 epochs, Adam lr 0.05 cooled linearly to 5%, L2 on `a`, `b` (1e-4) and `W` (1e-2), none on the season levels |
| Weights | `model.pt` (this folder) |
| Eval write-up | `verification/reports/run1_season_delta/eval.md` |
| Explainer | `docs/serve_level_fix.md` |

Reproduce:

```bash
python scripts/train_model.py --rows runs/rows.parquet --train-through 2024 \
    --out artifacts/models/run1_season_delta/model.pt
python scripts/evaluate_model.py --rows runs/rows.parquet \
    --model artifacts/models/run1_season_delta/model.pt
```

Do not overwrite these files.

Future simulation outputs: `artifacts/simulations/run1_season_delta/` (empty until sim exists).
