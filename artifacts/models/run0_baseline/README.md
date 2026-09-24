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

Simulation outputs: `artifacts/simulations/run0_baseline/` (the 2025 season simulated 10,000 times).
