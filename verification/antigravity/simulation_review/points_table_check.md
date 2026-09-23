# 2025 ATP points table and rules: independent check

Checked on 2026-09-23 by Antigravity (Gemini 3.5, read-only web run, conversation
`c7274086-9fc5-4876-a545-a6a802d6eed2`) before `atp_sim/points.py` was finalised, then
tested against the real 2025 results.

## Verdict

Every value in `atp_sim/points.py` agrees with the check. Nothing had to change.

| Item | Check result | In `points.py` |
|---|---|---|
| Points by round (Slam 128; Masters 96 and 56; 500 with 32 and 48; 250 with 28/32 and 48) | Table below, introduced January 2024, unchanged in 2025 | Same |
| ATP Finals | 200 per round-robin win, +400 semi-final win, +500 final win, 1,500 undefeated | Same |
| Bye then loss | "Any player who reaches the second round by drawing a bye and then loses shall be considered to have lost in the first round and shall receive first round loser's points." | `BYE_LOSS_SCORES_FIRST_ROUND = True` |
| ATP 500 events in 2025 | 16: Rotterdam, Dallas, Doha, Rio de Janeiro, Acapulco, Dubai, Barcelona, Munich, Hamburg, Queen's Club, Halle, Washington, Tokyo, Beijing, Vienna, Basel. Dallas, Doha and Munich promoted from 250 | Same list |
| Masters 1000 draws in 2025 | 96: Indian Wells, Miami, Madrid, Rome, Canada, Cincinnati, Shanghai. 56: Monte Carlo, Paris | Read from the rebuilt draws, which agree |
| Match format | Slams best of 5 with a 10-point tiebreak at 6-6 in the deciding set; all other events, ATP Finals included, best of 3 with 7-point tiebreaks | `atp_sim/match.py` |
| ATP Finals group order | Wins; head-to-head for two tied; for three tied, sets won %, then games won %, then ranking, dropping to head-to-head as soon as two remain | `atp_sim/season.py` (games % is not simulated, see limitations) |
| Counting rules | Best 19 (4 Slams + 8 mandatory Masters + best 7 others), Finals as a 20th result, zero-pointers for missed mandatory events, United Cup awards up to 500 | Not implemented: every simulated event counts in full |

| Category | Draw | W | F | SF | QF | R16 | R32 | R64 | R128 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Grand Slam | 128 | 2000 | 1300 | 800 | 400 | 200 | 100 | 50 | 10 |
| Masters 1000 | 96 | 1000 | 650 | 400 | 200 | 100 | 50 | 30 | 10 |
| Masters 1000 | 56 | 1000 | 650 | 400 | 200 | 100 | 50 | 10 | |
| ATP 500 | 48 | 500 | 330 | 200 | 100 | 50 | 25 | 0 | |
| ATP 500 | 32 | 500 | 330 | 200 | 100 | 50 | 0 | | |
| ATP 250 | 48 | 250 | 165 | 100 | 50 | 25 | 13 | 0 | |
| ATP 250 | 28 / 32 | 250 | 165 | 100 | 50 | 25 | 0 | | |

## Sources and their strength

Cited: ATP rulebook chapter IX (PIF ATP Rankings), the ATP 2025 calendar announcement
(atptour.com, 22 March 2024), the Nitto ATP Finals rules page, and Wikipedia's ATP rankings
and 2025 ATP Tour pages. **atptour.com returned HTTP 403 to the automated fetch**, so the
rulebook values and the quoted bye-rule text were cross-referenced from the other sources
rather than read off the rulebook PDF itself.

## Check against the real season

The stronger evidence is empirical. Scoring the real 2025 results of the 60 simulated
events with this table (`atp_sim.draws.real_points`) reproduces the official year-end
totals of the top two exactly:

| Player | Same-table 2025 total | Official 2025-12-29 | Gap |
|---|---:|---:|---:|
| Carlos Alcaraz | 12,050 | 12,050 | 0 |
| Jannik Sinner | 11,500 | 11,500 | 0 |
| Alexander Zverev | 5,225 | 5,110 | +115 |
| Novak Djokovic | 4,830 | 4,820 | +10 |

Their two totals draw on the Slam, both Masters draw sizes, ATP 500 and ATP Finals rows,
so an error in any of those rows would show. The 250 rows are not exercised by them. The
gaps further down come from the rules not implemented (best 19, United Cup, Challengers).
