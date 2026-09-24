# Model progression log: Run 0 (baseline)

**Date logged:** 21 September 2026  
**Purpose:** Freeze the first holdout evaluation so later changes show real progression, not a moving target.

This was the first full train + eval of the bilinear serve model. Results originally only appeared in a terminal session; this file is the durable record.

---

## What was trained

| Item | Value |
|---|---|
| Model file | `artifacts/models/run0_baseline/model.pt` |
| Training rows | `runs/rows.parquet` (built locally by `scripts/build_rows.py`; gitignored) |
| Train through | **2024** (seasons ≤ 2024) |
| Holdout | **2025** and partial **2026** (7,664 rows) |
| Parameters | 243 (81 × Hard / Clay / Grass) |
| Formula | `z = μ + a·xᵢ − b·xⱼ + xᵢᵀ W xⱼ` |

Command re-run to capture this log:

```bash
python scripts/evaluate_model.py --rows runs/rows.parquet --model artifacts/models/run0_baseline/model.pt
```

---

## Holdout results (Run 0)

`bias = predicted − actual` (negative ⇒ under-predicts serve).  
`constant` = always guess that surface’s training-era serve rate.

### Hard (training-era rate 0.6327)

| Season | Rows | Actual | Predicted | Bias | NLL (const) | Point-MAE (const) |
|---|---|---|---|---|---|---|
| 2025 | 3,182 | 0.6467 | 0.6315 | **−0.0152** | 0.64813 (0.64990) | 0.0574 (0.0613) |
| 2026 | 1,318 | 0.6586 | 0.6317 | **−0.0268** | 0.64114 (0.64344) | 0.0613 (0.0669) |
| all | 4,500 | 0.6502 | 0.6316 | **−0.0186** | 0.64607 (0.64800) | 0.0586 (0.0630) |

### Clay (training-era rate 0.6069)

| Season | Rows | Actual | Predicted | Bias | NLL (const) | Point-MAE (const) |
|---|---|---|---|---|---|---|
| 2025 | 1,520 | 0.6211 | 0.6071 | **−0.0140** | 0.66338 (0.66395) | 0.0588 (0.0604) |
| 2026 | 1,054 | 0.6271 | 0.6084 | **−0.0188** | 0.66013 (0.66133) | 0.0636 (0.0662) |
| all | 2,574 | 0.6234 | 0.6076 | **−0.0159** | 0.66212 (0.66294) | 0.0607 (0.0626) |

### Grass (training-era rate 0.6500)

| Season | Rows | Actual | Predicted | Bias | NLL (const) | Point-MAE (const) |
|---|---|---|---|---|---|---|
| 2025 | 590 | 0.6602 | 0.6499 | **−0.0103** | 0.63951 (0.64115) | 0.0536 (0.0571) |
| 2026 | — | — | — | — | no rows (archive ends ~May) | — |

---

## What Run 0 showed (interpretation)

1. **Under-prediction everywhere:** servers win about 1 to 3 percentage points more than the model expects; worse in 2026.
2. **Beats the constant baseline**, but only modestly (NLL and point-MAE slightly better).
3. **Player terms are non-trivial** (serve / return / interaction roughly 0.05 to 0.12): ranking players helps; the level shift is the main leftover error.
4. **Data was later verified** (`DATA_SOURCE_VERIFICATION.md`): the bias is a modelling issue, not bad Sackmann numbers.
5. **2026 grass missing** in this holdout because `data/tennis_atp` stops before the grass season.

---

## Progression checklist

| Run | What changed | Holdout bias (Hard all) | Notes |
|---|---|---|---|
| **0 (this file)** | First fit through 2024 | **−0.0186** | Frozen under `artifacts/models/run0_baseline/` |
| 1 | Season intercept `δ_season`, `μ` anchored on 2024 | **−0.0078** | See [`run1_season_delta/eval.md`](../run1_season_delta/eval.md) |
| 2 | *(not yet)* | | |

After each future train/eval, write `verification/reports/runN_…/eval.md` and update `MODEL_PROGRESSION.md`.

---

## Related artefacts

| Path | Role |
|---|---|
| `artifacts/models/run0_baseline/model.pt` | Frozen Run 0 weights |
| `verification/reports/MODEL_PROGRESSION.md` | Progression index |
| `scripts/evaluate_model.py` | How these numbers were produced |
| `verification/reports/DATA_SOURCE_VERIFICATION.md` | Why we keep the data despite bias |
| `runs/build_report.md` | Training-table build (written locally by `scripts/build_rows.py`; gitignored) |
