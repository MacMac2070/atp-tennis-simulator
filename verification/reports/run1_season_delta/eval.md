# Model progression log — Run 1 (serve level anchored on 2024)

**Date logged:** 22 September 2026
**Purpose:** Fix the systematic serve under-prediction found in Run 0 with one change, and score it on the same holdout.

---

## What was trained

| Item | Value |
|---|---|
| Model file | `artifacts/models/run1_season_delta/model.pt` |
| Training rows | `runs/rows.parquet` (same table as Run 0) |
| Train through | **2024** (seasons ≤ 2024) |
| Holdout | **2025** and partial **2026** (7,664 rows, same as Run 0) |
| Parameters | 243 (81 × Hard / Clay / Grass), same as Run 0 |
| Prediction formula | `z = μ + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ` (unchanged) |
| Training formula | `z = μ + δ_season + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ`, `δ_2024 = 0`, δ discarded on save |

Command:

```bash
python scripts/train_model.py --rows runs/rows.parquet --train-through 2024 --out artifacts/models/run1_season_delta/model.pt
python scripts/evaluate_model.py --rows runs/rows.parquet --model artifacts/models/run1_season_delta/model.pt
```

### The change, in one paragraph

The form cards are standardised per season, so `x = 0` means "average for that season" and the cards carry no information about the era's serve level. Only `μ` does, and in Run 0 it was fitted on every row since 1992 and settled on the 33-year average, 1.1 to 1.5 pp below the 2024 tour. Run 1 gives every season its own intercept during training, with the last training season as the anchor; on save `μ` is set to the anchor's level and the rest is dropped. Older seasons still shape `a`, `b`, `W`; they just no longer drag `μ` back in time. Full explainer with diagrams: `docs/serve_level_fix.md`.

### Recipe notes (what had to change to make the anchor hold)

- **Per-season levels, not μ plus a delta.** μ and a per-season delta are nearly collinear (only the anchor's 6% of rows separate them) and Adam crawled along that direction. Fitting one full intercept per season, each set by its own rows, converges cleanly. Reported as δ = level − level(2024).
- **No L2 on the season levels.** Even a 1e-4 penalty summed over 32 seasons pulled the 2024 level 0.5 pp off its data. Removed.
- **Learning-rate cool-down** (linear to 5% over the run, `--lr-decay`, default on). At a fixed lr of 0.05 the intercepts jitter by about 1 pp; with the cool-down the in-sample 2024 level lands within 0.06 pp of the data on two seeds. Run 0's frozen weights are unaffected. Side effect: the fit is tighter overall (training point-MAE on Hard 0.0584 → 0.0563) and the interaction term is smaller (0.05 → 0.02 mean |contribution|), so part of the NLL/MAE gain below is better convergence, not only the anchor. The bias change is the anchor.

### Fitted season offsets (log-odds relative to 2024, discarded on save)

| Surface | 1992 | 2000 | 2010 | 2020 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Hard | −0.148 | −0.064 | −0.012 | +0.010 | +0.008 | 0 |
| Clay | −0.103 | −0.066 | −0.008 | −0.047 | −0.030 | 0 |
| Grass | −0.189 | −0.103 | −0.003 | −0.057 | −0.043 | 0 |

They track the per-season rate table (1992 about 3 pp below 2024, flat since ~2010, Covid-era dip on clay and grass).

---

## Holdout results (Run 1)

`bias = predicted − actual` (negative ⇒ under-predicts serve).
`pooled` = always guess that surface's 1992 to 2024 rate (Run 0's baseline). `last` = always guess its 2024 rate (the bar an anchored μ must beat). `drift` = actual − 2024 rate, i.e. how far the tour moved after the cutoff.

### Hard (pooled 0.6327, 2024 rate 0.6443, model μ → 0.6370)

| Season | Rows | Actual | Predicted | Bias | Drift | NLL (pooled / last) | Point-MAE (pooled / last) |
|---|---|---|---|---|---|---|---|
| 2025 | 3,182 | 0.6467 | 0.6424 | **−0.0042** | +0.0024 | 0.64705 (0.64990 / 0.64949) | 0.0543 (0.0613 / 0.0603) |
| 2026 | 1,318 | 0.6586 | 0.6422 | **−0.0164** | +0.0143 | 0.63975 (0.64344 / 0.64243) | 0.0571 (0.0669 / 0.0642) |
| all | 4,500 | 0.6502 | 0.6424 | **−0.0078** | +0.0059 | 0.64490 (0.64800 / 0.64741) | 0.0551 (0.0630 / 0.0614) |

### Clay (pooled 0.6069, 2024 rate 0.6203, model μ → 0.6237)

| Season | Rows | Actual | Predicted | Bias | Drift | NLL (pooled / last) | Point-MAE (pooled / last) |
|---|---|---|---|---|---|---|---|
| 2025 | 1,520 | 0.6211 | 0.6203 | **−0.0008** | +0.0008 | 0.66159 (0.66395 / 0.66353) | 0.0539 (0.0604 / 0.0595) |
| 2026 | 1,054 | 0.6271 | 0.6226 | **−0.0045** | +0.0068 | 0.65854 (0.66133 / 0.66057) | 0.0587 (0.0662 / 0.0640) |
| all | 2,574 | 0.6234 | 0.6212 | **−0.0022** | +0.0031 | 0.66041 (0.66294 / 0.66239) | 0.0558 (0.0626 / 0.0613) |

### Grass (pooled 0.6500, 2024 rate 0.6655, model μ → 0.6597)

| Season | Rows | Actual | Predicted | Bias | Drift | NLL (pooled / last) | Point-MAE (pooled / last) |
|---|---|---|---|---|---|---|---|
| 2025 | 590 | 0.6602 | 0.6671 | **+0.0070** | −0.0054 | 0.63907 (0.64115 / 0.64099) | 0.0518 (0.0571 / 0.0568) |
| 2026 | — | — | — | — | — | no rows (archive ends ~May) | — |

Term magnitudes on the holdout (mean |contribution|, log-odds): Hard serve 0.112 / return 0.085 / interaction 0.017; Clay 0.075 / 0.077 / 0.013; Grass 0.127 / 0.072 / 0.017.

---

## Delta vs Run 0

Run 0 numbers from `verification/reports/run0_baseline/eval.md`. Positive Δbias means less under-prediction; negative ΔNLL and ΔMAE mean better.

| Surface | Season | Bias Run 0 | Bias Run 1 | Δ bias | NLL Run 0 | NLL Run 1 | Δ NLL | MAE Run 0 | MAE Run 1 | Δ MAE |
|---|---|---|---|---|---|---|---|---|---|---|
| Hard | 2025 | −0.0152 | −0.0042 | **+0.0110** | 0.64813 | 0.64705 | −0.00108 | 0.0574 | 0.0543 | −0.0031 |
| Hard | 2026 | −0.0268 | −0.0164 | **+0.0104** | 0.64114 | 0.63975 | −0.00139 | 0.0613 | 0.0571 | −0.0042 |
| Hard | all | −0.0186 | −0.0078 | **+0.0108** | 0.64607 | 0.64490 | −0.00117 | 0.0586 | 0.0551 | −0.0035 |
| Clay | 2025 | −0.0140 | −0.0008 | **+0.0132** | 0.66338 | 0.66159 | −0.00179 | 0.0588 | 0.0539 | −0.0049 |
| Clay | 2026 | −0.0188 | −0.0045 | **+0.0143** | 0.66013 | 0.65854 | −0.00159 | 0.0636 | 0.0587 | −0.0049 |
| Clay | all | −0.0159 | −0.0022 | **+0.0137** | 0.66212 | 0.66041 | −0.00171 | 0.0607 | 0.0558 | −0.0049 |
| Grass | 2025 | −0.0103 | +0.0070 | **+0.0173** | 0.63951 | 0.63907 | −0.00044 | 0.0536 | 0.0518 | −0.0018 |

---

## What Run 1 showed (interpretation)

1. **The level shift is gone on 2025.** Hard −0.4 pp, Clay −0.1 pp: within the noise of a single season's rate. The 1.1 to 1.5 pp gap was the pooled μ, as diagnosed.
2. **Beats the harder baseline.** Run 1 has lower NLL and point-MAE than the last-season constant on every surface and season. Run 0 only beat the pooled constant, which is a straw man once μ is anchored.
3. **2026 still reads low on Hard (−1.6 pp), and that is drift.** The 2026 tour is +1.4 pp above 2024 (`drift` column). The archive stops in May 2026 and the model has never seen a 2026 match, so this is data freshness, not model error. Refreshing 2026 from TML would move the anchor, not the method.
4. **Grass now over-predicts by 0.7 pp.** 2024 was an unusually strong grass season (66.6%, the highest in the table) and 2025 came back down (66.0%). Anchoring on one season inherits that season's noise; grass has the fewest rows (~600 per season) so it is the most exposed. Still better than Run 0 on NLL and MAE.
5. **Interaction term shrank** from ~0.05 to ~0.02 mean |contribution|. That is the learning-rate cool-down letting `W` settle under its L2 rather than jittering, not the anchor. It strengthens the design-note suspicion that `W` earns little.

---

## Related artefacts

| Path | Role |
|---|---|
| `artifacts/models/run1_season_delta/model.pt` | Frozen Run 1 weights (also copied to `runs/model.pt` for script defaults) |
| `artifacts/models/run0_baseline/model.pt` | Frozen Run 0 weights, untouched |
| `verification/reports/run0_baseline/eval.md` | Run 0 holdout tables |
| `verification/reports/MODEL_PROGRESSION.md` | Progression index |
| `docs/serve_level_fix.md` | Explainer with diagrams |
| `scripts/evaluate_model.py` | How these numbers were produced |
