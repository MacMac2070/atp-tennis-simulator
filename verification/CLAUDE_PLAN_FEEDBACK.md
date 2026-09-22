# Feedback on Claude Code plan (from Cursor review)

Apply these before / while executing the plan in `~/.claude/plans/look-at-cursor-chat-hashed-spindle.md`. Architecture is fine; fix or explicitly accept the items below.

## Do this

1. **Frozen real form cards + no sim→form feedback**  
   Keep this choice (good for A/B’ing the serve model; matches DESIGN “substitute real results”). **State it as an intentional limitation** in every `summary.md`, both simulation READMEs, and `verification/reports/simulations_2025.md`. Do not imply a closed fantasy season where wins change later form. Tournaments couple mainly via ranking points, not form.

2. **No best-19 (and related ranking rules)**  
   Accept for v1, but **do not oversell** “year-end #1 %” / ranking distributions as real ATP ranking fidelity. Always report the **same-points-table actual race** (`actual_points_same_table`) so simulator error is separated from rule error. List best-19 / mandatory events / protected rankings as explicit limitations.

3. **ATP Finals = real 2025 groups only**  
   Keep for v1 (consistent with fixed draws). Document clearly: **qualification is not simulated**; “makes Turin” narratives are out of scope.

4. **Bracket reconstruction**  
   Keep the feeder integrity test over all 2025 events as a **hard gate**. If reconstruction fails often, **do not silently patch** — fall back to a documented simpler rule and say so in the compare note. Walkovers/byes must be handled explicitly.

5. **Antigravity soft-fail**  
   Try Antigravity reviews as planned. **If the CLI is missing or not signed in, do not stop the whole job.** Continue with cited ATP points sources, note the skip in `verification/antigravity/simulation_review/`, and finish both sims.

## Also fine / keep

- File-year 2025 (2024-12-27 → 2025-11-09), parallel `season_2025/` layout, same seed/`n_sims`, refuse writing from `runs/model.pt`, never overwrite frozen `artifacts/models/run*/`.
- Analytic `p_match` + common random numbers per (sim, event, slot).
- 500 vs 250 by tournament name (must cite source list).
- Exclude Davis Cup / Laver Cup / United Cup / Next Gen / Qualifying / Challengers — but score “actual” on the **same** event set.
- `n_sims=10000` is OK if matrices are precomputed; smoke with 100–1000 first if Stage 3 is slow.
- Obsidian / extra docs are secondary — **sims and compare note first**.

## Success unchanged

Both `artifacts/simulations/run0_baseline/season_2025/` and `…/run1_season_delta/season_2025/` with matching filenames; `verification/reports/simulations_2025.md` with Run 0 vs Run 1 vs actual; `shasum` of frozen models unchanged; `graphify update .` after code changes.
