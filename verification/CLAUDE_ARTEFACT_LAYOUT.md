# Note for Claude Code — artefact layout

**Story for GitHub:** Run 0 = first model. Run 1 = improvement. Simulations use the **same run names**.

## Canonical paths

| Run | Weights | Eval | Simulations |
|---|---|---|---|
| 0 | `artifacts/models/run0_baseline/` | `verification/reports/run0_baseline/eval.md` | `artifacts/simulations/run0_baseline/` |
| 1 | `artifacts/models/run1_season_delta/` | `verification/reports/run1_season_delta/eval.md` | `artifacts/simulations/run1_season_delta/` |

Index: `verification/reports/MODEL_PROGRESSION.md`
Overview: `artifacts/README.md`
**Simulation brief (build + run):** `verification/CLAUDE_SIMULATION_BRIEF.md`

## Rules

1. **Do not overwrite** frozen `run0_baseline` or `run1_season_delta` model folders.
2. New ideas → `run2_…` (models + reports + empty simulations/ stub).
3. Run **both** models with the **same seeds**; write under `artifacts/simulations/run*/season_2025/`.
4. User has asked to **build and run** the 2025 season simulator for Run 0 and Run 1 — follow `CLAUDE_SIMULATION_BRIEF.md`.
5. `runs/model.pt` is only a working copy; history lives under `artifacts/`.
