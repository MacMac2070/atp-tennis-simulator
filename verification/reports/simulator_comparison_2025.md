# Two independent season simulators: Cursor vs Claude

**Verdict:** the two builds agree on every result that matters, which is good evidence that
both compute the model correctly. They differ in one points value, the ATP Finals rules and
how they handle bad input. Keep Claude's build.

Cursor's build is uncommitted in the main project folder (branch `Cursor-attempt`).
Claude's is uncommitted in `.claude/worktrees/claude-attempt` (branch `Claude-attempt`).
Both branches still point at commit `224f503`, so git cannot diff them; this note does.
Claude read Cursor's code only after its own build was finished and reviewed.

Paths below starting `C:` are in the main folder, `K:` in the Claude worktree.

---

## 1. The results agree

Both builds replay the same 60 events of the 2025 file year with the same frozen models.

| | Cursor | Claude |
|---|---:|---:|
| Seasons simulated, seed | 2,000, 42 | 10,000, 42 |
| Real matches scored | 2,622 | 2,622 (same matches) |
| Run 0 match log loss / accuracy | 0.6895 / 61.0% | 0.6895 / 61.0% |
| Run 1 match log loss / accuracy | 0.6545 / 61.6% | 0.6545 / 61.6% |
| Largest gap in P(real winner), any match | 0.0001 (rounding) | |
| Run 0 P(Alcaraz #1) | 47.9% | 47.7% |
| Run 1 P(Sinner #1) | 70.2% | 70.9% |
| Real champion in the top three, Run 0 / Run 1 | 31 / 27 | 31 / 27 |

The year-end and title differences are Monte Carlo noise: with 2,000 and 10,000 seasons the
standard error of a difference in P(#1) is about 1.2 percentage points, and every P(#1) gap
is within 1.4 of those except one tiny one (Djokovic at about 1%).

Cursor reports the real champion as the favourite in 17 of 60 events for Run 0, Claude 15.
That is four near-ties flipping, not a code difference: at Monte Carlo the top two were
0.01 pp apart in Claude's run, at Paris 0.4 pp, at Winston-Salem 0.5 pp, and at the
Australian Open the gap was 3.7 pp in Cursor's run with a standard error of 1.7 pp.

## 2. The four real differences

| # | What | Cursor | Claude | Effect |
|---|---|---|---|---|
| 1 | ATP 250 with a 48 draw, round-of-32 loser | 0 points (`C: atp_sim/points.py:25`) | 13 points (`K: atp_sim/points.py:31`), the official value | Winston-Salem only. Ten players who won a first match there are 13 points short in Cursor's same-table totals |
| 2 | ATP Finals round robin | Match winner from `p_match`; the set score is then drawn with a flat 65% chance of 2-0, whoever is playing. Tied groups sort by head-to-head, set %, then **lowest player id**, and do not return to head-to-head once set % splits a three-way tie (`C: atp_sim/draws.py:217-259`) | Played set by set from `p_set`, so stronger players win more in straight sets; ATP order with the return to head-to-head; entry rank last (`K: atp_sim/season.py:136-202`) | The only title gap bigger than noise: Run 1 gives Sinner the Finals 63.9% (Cursor) vs 67.8% (Claude). Sinner and Alcaraz have the highest ids in their groups, so the id rule counts against them |
| 3 | "Higher-ranked player wins" baseline | A missing rank counts as a miss (`C: atp_sim/season.py:334-338`) | The ranked player counts as higher (`K: atp_sim/report.py:85-96`) | 64.1% vs 64.3%. Exactly four matches with an unranked loser: Kyrgios twice, Brooksby, Dan Martin |
| 4 | Tied ranks | Arbitrary order (`argsort`, `C: atp_sim/season.py:270-280`) | Shared places, 1, 2, 2, 4 (`K: atp_sim/season.py:224-234`) | Claude's P(#1) column sums to 1.0025 because a shared first place counts for both. No effect in the top 20 |

On difference 1, the 13 comes from the Antigravity rules check
(`K: verification/antigravity/simulation_review/points_table_check.md`), which could not
fetch atptour.com directly and cross-referenced other sources. It reports the 2024 points
reform lifting this round from 10 to 13; 0 is not a value the table has had. On
difference 2, Cursor's flat 65% makes the set-percentage tie-break partly random, and the
player-id fallback has no basis in the ATP rules; the real 2025 Connors group (Fritz,
De Minaur and Musetti all 1-2) is exactly the kind of tie where these rules decide who
plays the semi-finals.

## 3. What happens when the input is bad

This is where the builds differ most. A simulator that quietly repairs bad input gives a
plausible-looking wrong answer; one that stops tells you something is wrong.

| Situation | Cursor | Claude |
|---|---|---|
| A first-round result missing from a draw | Its winner becomes a fake bye entrant, the loser vanishes, and the bye rule then pays him 0 instead of 25. Reported as `bracket_ok` false but the run continues (`C: atp_sim/draws.py:117-140`) | Raises `DrawError` for ten impossible shapes, including this one when it makes the draw size odd (`K: atp_sim/draws.py:116-198`) |
| A final missing | The first semi-final winner is crowned (`C: atp_sim/draws.py:208`) | Raises |
| An entrant with no form card | Simulated as a tour-average player (zero vector), counted but not stopped (`C: atp_sim/season.py:85-93`) | Every card built with `build_cards`; a missing one raises (`K: atp_sim/season.py:55-72`) |
| A NaN serve probability | `p_hold(nan)` returns uninitialised memory (`C: atp_sim/match.py:18-24`) | Rejected (`K: atp_sim/match.py:51-56`) |
| Same random numbers for both models | True because each event happens to use a fixed number of draws; untested, and any extra random draw would shift every later event | Seeded per event and per match slot, and tested (`K: tests/test_season.py`) |
| A model trained on the season being simulated | Not checked | Refused; model file hashed before and after the run |
| Comparing two runs | Labels columns by position, no checks | Refuses runs that differ in season, seed, simulation count, events or commit |
| Merged player ids | Not applied to the draws (latent: no merged id plays in 2024 or 2025) | Applied |

## 4. Tests and extras

| | Cursor | Claude |
|---|---|---|
| Tests | 19 | 43 cases |
| Covered only by Claude | | Point-by-point replay of the maths, serve order, 10-point Slam tiebreak, hand-computed title odds, bye points inside a simulation, same random numbers, the real 2025 Finals three-way tie, the 52-week window, cards equal the training table, the real 2025 totals of Alcaraz and Sinner |
| Extras | | 52-week ranking ledger with the 2024 results as its base, week-by-week rankings, comparison with the official ranking, `metrics.json`, per-run README |

## 5. Claude's own weak points

Stated so the verdict is fair; none changes a 2025 number.

- Two missing first-round results could still pass the draw checks if the draw size stays
  even and the two false byes do not meet. The 2025 test cross-checks every draw against
  the csv; the 2024 draws used for the ledger have no such check.
- The Monday on which an event's points enter the ranking is estimated from its length, so
  the weekly table can be a week out around some events. Year-end figures do not use it.
- The comparison script cannot tell two different uncommitted code states apart: both runs
  record the same commit plus "uncommitted changes".
- The metric `spearman_official_top50` correlates simulated points with same-table points
  over the official top 50, not with the official ranking; the name is misleading.
- An ATP Finals where an alternate played would stop the run, with an error that does not
  name the event.
- `tests/test_draws.py` imports a helper from `tests/test_season.py`, which depends on
  pytest's default import mode.

## 6. Recommendation

Keep Claude's build. Cursor's has nothing that Claude's lacks, and it carries one wrong
points value, cruder ATP Finals rules and several silent repairs. The agreement at match
level (every probability to four decimals) is the most useful thing the second build gave:
it confirms the match maths, card lookup and model loading in both.

The two cannot be merged as they stand: both write `verification/reports/simulations_2025.md`
and `artifacts/simulations/run*/README.md`, and both add `atp_sim/{match,points,draws,season,report}.py`
with different contents. One has to be chosen, and the other kept on its own branch if
wanted for reference.
