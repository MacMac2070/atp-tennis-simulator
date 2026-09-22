# Nudge from Cursor (parallel review) — read before finishing the Sackmann verify

Claude Code is verifying Sackmann against external sources. Address these before treating the report as done:

## 1. tennisdata.app returned 403
Do not count it as a second independent source unless you find another download path. If blocked, say so explicitly and rely on TML + ATP spot-checks only.

## 2. TML is not fully independent of Sackmann
Same winner/loser + `w_svpt`-style schema. Use TML mainly for **coverage / freshness** (especially 2026). For “is this true?”, weight **ATP official pages** higher than TML-vs-Sackmann agreement.

## 3. Do not scrape ATP aggressively
Fragile pages, missing old stats, ToS / rate limits. Prefer a **small fixed set** of well-known matches with stable URLs (e.g. recent Slam finals). If a page has no stats, record that and move on — no endless resampling loops.

## 4. Ignore downloaded CSVs in git
Add `verification/external/` to `.gitignore` (Cursor is doing this too). Do not commit the ~20MB+ mirror.

## 5. `verification/out` → `runs/`
Reports written to `verification/out/...` land in `runs/`. Prefer `verification/reports/` (not symlinked to runs) for the deliverable markdown.

## 6. Join carefully — IDs differ
Sackmann player IDs ≠ ATP IDs. TML claims ATP IDs. **Do not join on `winner_id` alone.** Join on `(tourney_date, winner_name, loser_name)` or score+date, with normalized names. Low match rate usually means bad join, not bad data (as you already noted).

## 7. Confirm downloads finished
Confirm TML 1992–2026 downloads finished and row counts look sane before reporting. Check whether 2026 grass exists in TML (Sackmann/table may stop before June).

---
Written while Claude Code was running the verify-sackmann task. Cursor is also running an independent TML↔Sackmann compare in parallel.

---

## Parallel Cursor results (already written)

See `verification/reports/cursor_parallel_tml_compare.md`.

Critical findings for you to incorporate:

1. **winner_id agreement on 2024 name+date joins = 0.0%** — confirms never join on id.
2. When names+date match, **serve columns are ~99–100% exact** (2020–2025). Stats look identical → TML is a weak *independent* check; great for coverage.
3. **2026:** Sackmann ends ~25 May (almost no grass: 4 matches). **TML goes to 13 Sep with 297 grass matches.** Your archive is stale for mid/late 2026 — that explains missing grass, not a table bug alone.
4. Aggregate serve-won rates match closely year by year (both show the gentle upward drift into 2025/26).
5. Paste acknowledgment: please read this file and `verification/reports/cursor_parallel_tml_compare.md` before finalizing.

## Extra note on your current script
`verification/cross_check_sources.py` looks good (name/pair join, not ids; spelling fallback). Two nits:
- It writes to `verification/out/` which is a **symlink to `runs/`**. Prefer `verification/reports/`.
- Cutting both sources at `min(max_date)` is fair for agreement, but **also report** that TML continues past Sackmann’s May 2026 cutoff (grass season exists in TML only).
