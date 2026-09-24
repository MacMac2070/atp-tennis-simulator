# Simulator code review, 2026-09-23

Two independent read-only reviews of `atp_sim/{match,points,draws,season,report}.py`,
`scripts/simulate_season.py` and the tests, before the final runs: Antigravity (Gemini 3.5,
conversation `f5bc1710-5083-4d3a-80c6-62862ec4ac58`) and the ecc `python-reviewer` agent.
Neither reviewer was shown the second simulator, which was built separately for comparison
only and not kept.

## Findings and what was done

| # | Reviewer | Where | Finding | Action |
|---|---|---|---|---|
| 1 | ecc | `match.py` `_arrays` | NaN passed the [0, 1] check (every NaN comparison is false), so a NaN model output would make a player silently lose every simulation | Fixed: the check is now "inside the range", which rejects NaN. Test added |
| 2 | Antigravity | `draws.py` `build_knockout` | A player could appear in two matches of one round, letting one feeder node feed two matches | Fixed: one match per player per round. Test added |
| 3 | Antigravity | `draws.py` `build_knockout` | A two-round draw accepted a "bye" straight into the final | Fixed: byes only into a second round that is not the final. Test added |
| 4 | Antigravity | `draws.py` `build_knockout` | Two bye players could meet in their first match | Fixed: raises, as it means a first-round result is missing. Test added |
| 5 | Antigravity | `draws.py` `build_knockout` | One missing first-round row became a fifth bye and a 27 draw (caught later by the points table, not by the rebuild) | Fixed: odd draw sizes raise. Test added |
| 6 | ecc | `report.py` `weekly_table` | The ledger walk relied on `groupby`'s default sort order | Fixed: dates sorted explicitly |
| 7 | ecc | `report.py` `write_run` | `groupby.apply(include_groups=False)` needs pandas 2.2; `requirements.txt` allows 2.0 | Fixed: replaced by a plain column aggregation |
| 8 | Antigravity | `report.py` summary | "Where it misses" could list a player twice with fewer than 8 in the top 20 | Fixed: de-duplicated |
| 9 | Antigravity | `report.py` `match_table` | Retirement flag was case-sensitive | Fixed |
| 10 | ecc | `draws.py`, `match.py` | `entry_rank` annotated without `None`; untyped probability parameters | Fixed |
| 11 | ecc | several | A few short helpers lack docstrings | Partly: added where the name is not self-explanatory |

## Checked by the reviewers and found sound

Tennis recursions (probability conservation to 1e-15, serve order, 10-point Grand Slam decider),
points and the bye rule, common random numbers (a match slot's random number is identical
in every run), ATP Finals set counting and group tie-breaks, the 52-week window, rank ties, int16
points, fancy-index assignments, and the card merge.

## Effect on the results

None. After the fixes every output file of both runs was byte-identical to the runs made
before the review, apart from the 16th decimal place of one averaged number in Run 1's
`metrics.json` (summation order). Every real 2024 and 2025 draw passes the stricter checks.
