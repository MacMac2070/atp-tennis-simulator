# Brief for Claude Code — build + run 2025 season sims (Run 0 and Run 1)

**User request:** Build the season simulator if it does not exist yet, then run it for **both** frozen models on **calendar year 2025**. Do not overwrite frozen model weights.

Cursor agent already set the artefact layout. Follow it exactly.

---

## 1. Artefact formatting (already done — do not invent a new layout)

Story: **Run 0 = first model**, **Run 1 = improvement**. Same run names for models, evals, and simulations.

| Run | Frozen weights (read-only) | Eval | Simulation outputs (write here) |
|---|---|---|---|
| **0** | `artifacts/models/run0_baseline/model.pt` | `verification/reports/run0_baseline/eval.md` | `artifacts/simulations/run0_baseline/` |
| **1** | `artifacts/models/run1_season_delta/model.pt` | `verification/reports/run1_season_delta/eval.md` | `artifacts/simulations/run1_season_delta/` |

Also read:

- `artifacts/README.md`
- `verification/CLAUDE_ARTEFACT_LAYOUT.md`
- `verification/reports/MODEL_PROGRESSION.md`
- Design: `DESIGN.md` §10 (point → match → tournament → season → rankings)

Folders `artifacts/simulations/run0_baseline/` and `…/run1_season_delta/` already exist with placeholder READMEs. **Fill them; do not rename.**

### Rules

1. **Never overwrite** `artifacts/models/run0_baseline/` or `artifacts/models/run1_season_delta/`.
2. `runs/model.pt` is only a working copy — sims must load from `artifacts/models/run*/model.pt`.
3. Run **both** sims with the **same random seeds / same draws** so only the serve model changes.
4. New model ideas later → `run2_…`, not edits to 0/1.

### Target output layout

```text
artifacts/simulations/run0_baseline/
  README.md                 ← update status after run
  season_2025/
    config.json             ← season, n_sims, seed(s), model path, code version
    summary.md              ← short results vs actual 2025 (year-end top, bias notes)
    rankings_year_end.parquet   ← or .csv: player_id, name, points, rank per sim / aggregates
    # optional: match_log sample, tournament winners, week-by-week snapshots

artifacts/simulations/run1_season_delta/
  README.md
  season_2025/              ← same filenames, parallel to Run 0
```

After both runs, add a short compare note (either in both READMEs or one file under `verification/reports/`) showing Run 0 vs Run 1 vs **actual 2025** (e.g. year-end #1 frequency, top-10 overlap, match winner accuracy if you log that).

---

## 2. What to simulate

- **Season:** ATP singles calendar **2025** (full year).
- **Surfaces:** Hard, Clay, Grass only (same validity rules as `atp_sim.data`).
- **Not** the whole archive 1991–2026. **Not** incomplete 2026 as the main experiment.
- **Mode:** Monte Carlo season replay — many simulated seasons (start with something feasible, e.g. 100–1000; document the count). Output distributions, not one pick.
- **Draws:** Use real 2025 tournament structure / entrants from Sackmann `data/tennis_atp/` where possible (real draws preferred over inventing a fantasy field). If full draw reconstruction is hard, document the simplification and keep it identical for Run 0 and Run 1.
- **Form cards:** Causal — for each simulated match date, cards may only use matches **before** that date (same rule as training). Prefer reusing `atp_sim.form_cards` + existing constants / `runs/rows.parquet` infrastructure.
- **Serve probs:** Load each run’s `model.pt` via existing `atp_sim.model` / train helpers. Formula unchanged: `z = μ + a·x_i − b·x_j + x_iᵀ W x_j` (per surface).

Stack (from DESIGN §10):

1. Form cards + surface → two serve %
2. Points → games → sets → match winner
3. Play tournament draw round by round
4. Award ATP ranking points; roll 52-week ledger where feasible
5. Repeat N times → year-end ranking distribution

---

## 3. Code that exists today (simulation does **not** exist yet)

Package only has training/eval plumbing:

- `atp_sim/data.py`, `form_cards.py`, `dataset.py`, `model.py`, `train.py`
- Scripts: `scripts/build_rows.py`, `scripts/train_model.py`, `scripts/evaluate_model.py`
- **No** `simulate_*.py`, no match/tournament/season modules yet — **you must build them**.

Python: project `.venv` if present (`.venv/bin/python`). Data under `data/tennis_atp/` (gitignored). Training table: `runs/rows.parquet`.

---

## 4. Suggested implementation order

1. **Match engine:** given two serve probs + best-of-3/5, simulate point-by-point (or game-level with correct Bernoulli stacking) → winner. Unit-test a known case.
2. **Tournament engine:** take a real 2025 draw (or reconstructed bracket from match list), play rounds, return champion + match wins.
3. **Season loop:** all 2025 tournaments in date order; update rankings/points; refresh form cards causally between events.
4. **CLI** e.g. `scripts/simulate_season.py --model PATH --season 2025 --n-sims N --seed S --out DIR`
5. Run twice:

```bash
python scripts/simulate_season.py \
  --model artifacts/models/run0_baseline/model.pt \
  --season 2025 --n-sims <N> --seed 42 \
  --out artifacts/simulations/run0_baseline/season_2025/

python scripts/simulate_season.py \
  --model artifacts/models/run1_season_delta/model.pt \
  --season 2025 --n-sims <N> --seed 42 \
  --out artifacts/simulations/run1_season_delta/season_2025/
```

Same `--seed` and `--n-sims` for both.

6. Update simulation READMEs + progression index note that sims exist.
7. Run `graphify update .` after code changes (project rule).

---

## 5. Success criteria

- [ ] Simulator code lives under `atp_sim/` + `scripts/simulate_season.py` (or clear equivalent).
- [ ] Both `artifacts/simulations/run*/season_2025/` populated with config + summary + ranking outputs.
- [ ] Identical seeds; only model path differs.
- [ ] Frozen model folders untouched.
- [ ] Short Run 0 vs Run 1 vs actual 2025 comparison written down.
- [ ] Limitations documented (injuries/retirements, walkovers, ranking-rule simplifications, etc.).

**Do not** retrain. **Do not** overwrite Run 0 / Run 1 weights. **Do** build the missing stack and run both sims into the reserved folders.
