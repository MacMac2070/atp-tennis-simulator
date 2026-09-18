# VERIFY_SPEC: definitions of the ATP training table

This is the complete specification of `runs/rows.parquet`, `runs/cards.parquet` and
`runs/constants.csv`. An independent checker needs only this file, the raw CSVs in
`data/tennis_atp/` and the output files. Python with pandas and pyarrow is available
as `python3` and as `.venv/bin/python` (the project's virtual environment).

## 1. Files and seasons
Match files: `data/tennis_atp/atp_matches_YYYY.csv` for YYYY = 1991 .. 2026 (tour-level
singles only). Players: `data/tennis_atp/atp_players.csv`.
**season** := the year in the file name the match came from, never the calendar year of
`tourney_date` (a handful of events dated 30 or 31 December sit in the next season's file).

## 2. Identity merges (applied to winner_id and loser_id before anything else)
211776 -> 212021 (Martin Landaluce), 209870 -> 211326 (Gunawan Trismuwantara).

## 3. Valid match: exclusion rules, applied in this order; a match is counted under the FIRST rule it fails
The 16 stat columns are, for side in (w, l): `{side}_svpt, {side}_1stIn, {side}_1stWon,
{side}_2ndWon, {side}_ace, {side}_df, {side}_bpSaved, {side}_bpFaced`.
1. `stats_missing`: any of the 16 is NaN.
2. `svpt_zero`: `w_svpt <= 0` or `l_svpt <= 0`.
3. `walkover`: `score` matches the regex `W/O|Walkover` (case-insensitive).
4. `exhibition_format`: `tourney_name` matches the regex `Next ?Gen|Laver Cup` (case-insensitive).
5. `same_player`: `winner_id == loser_id` (after merges).
6. `negative_stat`: any of the 16 is below 0.
7. `impossible_stat`: for either side: `1stIn > svpt`, or `1stWon > 1stIn`, or
   `2ndWon > svpt - 1stIn`, or `df > svpt - 1stIn`, or `ace + df > svpt`, or `bpSaved > bpFaced`.
8. `duplicate`: among matches passing rules 1 to 7, a later row with the same
   `(tourney_id, winner_id, loser_id, round, score, w_svpt, l_svpt)` as an earlier row
   (file order: season file, then row order). The first row is kept.
Flags on valid matches: `retired` := score contains `RET`; `defaulted` := score contains `DEF`.
`match_id` := `tourney_id + "#" + match_num`.

## 4. Appearances (the log)
Each valid match gives two appearances. For the appearance of player P against opponent O:
`svpt = P svpt; svwon = P 1stWon + P 2ndWon; ace = P ace; df = P df; bpf = P bpFaced;
bps = P bpSaved; rpt = O svpt; rwon = O svpt - (O 1stWon + O 2ndWon); obpf = O bpFaced;
obps = O bpSaved`.
Appearance order (used for "last 10"): sort by `(player_id, tourney_date, tourney_id, match_num)`.
Cards use appearances from valid matches of ANY surface (Carpet and missing surface
included) and any `tourney_level`, retirements and defaults included.

## 5. Card
A card is keyed by `(player_id, tourney_date D)`; one card per player per distinct
`tourney_date` at which the player has a valid match. The card's season is the season of
the matches played at D.
52-week window: appearances with `tourney_date` in `[D - 364 days, D)`. Inclusive lower
bound, exclusive upper bound. Every appearance dated D (any event) is excluded.
`n_52w` = number of appearances in the window. Window sums: `svpt_52, svwon_52, ace_52,
df_52, bpf_52, bps_52, rpt_52, rwon_52, obpf_52, obps_52`.
Last-10: the last 10 appearances of the window in appearance order (all of them when
`n_52w <= 10`). `n_10` = its size. Sums: `svpt_10, svwon_10`.
Raw rates (NaN when the denominator is 0): `raw_serve = svwon_52/svpt_52`,
`raw_ace = ace_52/svpt_52`, `raw_df = df_52/svpt_52`, `raw_ret = rwon_52/rpt_52`,
`raw_bps = bps_52/bpf_52`, `raw_bpc = (obpf_52 - obps_52)/obpf_52`,
`raw_serve10 = svwon_10/svpt_10`.

## 6. Priors
For season Y, `m_prior[attr, Y]` is the pooled rate over ALL appearances (any surface) of
season Y-1: serve `sum(svwon)/sum(svpt)`; ace `sum(ace)/sum(svpt)`; df `sum(df)/sum(svpt)`;
ret `sum(rwon)/sum(rpt)`; bps `sum(bps)/sum(bpf)`; bpc `sum(obpf - obps)/sum(obpf)`.
The first season loaded (1991) has no previous season: its prior is pooled over its own
appearances.

## 7. Shrinkage
`K = {serve: 200, ace: 50, df: 250, ret: 300, bps: 200, bpc: 350}`.
`shr_attr = (num_52 + K[attr] * m_prior[attr, Y]) / (den_52 + K[attr])`, where Y is the
card's season and `(num, den)` are the numerator and denominator of the raw rate. A card
with `n_52w = 0` therefore has `shr_attr = m_prior[attr, Y]` exactly.
`shr_serve10 = (svwon_10 + K[serve] * m_prior[serve, Y]) / (svpt_10 + K[serve])`.
`form = shr_serve10 - shr_serve`. When `n_52w <= 10` the two windows coincide and `form = 0` exactly.

## 8. Age
DOB is parsed from `atp_players.csv` column `dob` as an 8-digit `YYYYMMDD`; anything that
does not parse as a real date (including values ending in `0000`) is missing.
A DOB is treated as INVALID (= missing) when, for any valid match of that player in the
loaded files, `|(tourney_date - DOB) in days / 365.25 - Sackmann's winner_age or loser_age| > 1`.
`age = (D - DOB) in days / 365.25`; NaN when DOB is missing or invalid, and then
`dob_missing = True`.

## 9. Standardisation
Rows population `P(Y)` := for every valid match of season Y with surface in
`{Hard, Clay, Grass}`, the two server cards (the winner's card at D and the loser's card at
D). A card is counted once per such match.
Constants for season Y come from `P(Y-1)`: for each of `shr_serve, shr_ace, shr_df, shr_ret,
shr_bps, shr_bpc, form, age`: `mu` = mean, `sigma` = population standard deviation (ddof = 0),
ignoring NaN (only age can be NaN); `n_pop = |P(Y-1)|`.
`x = (value - mu) / sigma`; if `sigma = 0` then `x = 0`; if the value is NaN (age) then `x = 0`.
Season 1991 has no constants: its cards have `x = NaN` and it produces no rows.
Order of the x vector: 0 serve, 1 ace, 2 df, 3 ret, 4 bps, 5 bpc, 6 form, 7 age.

## 10. Rows (`runs/rows.parquet`)
For every valid match with a season that has constants (1992 onward) and surface in
`{Hard, Clay, Grass}`: two rows, one with the winner serving and one with the loser serving.
Columns: `match_id, tourney_id, tourney_date, season, tourney_level, surface, round, best_of,
server_id, returner_id, x_i_0..x_i_7` (the server's x), `x_j_0..x_j_7` (the returner's x),
`svpt` (server's svpt), `won` (server's 1stWon + 2ndWon), `retired, defaulted, i_n_52w,
i_n_10, j_n_52w, j_n_10, i_dob_missing, j_dob_missing`.
Sorted by `(tourney_date, tourney_id, match_num, server_id)`. No column may reveal the
result: there are no winner, loser, score, rank, name, seed or minutes columns, and the two
rows of a match are ordered by `server_id`, never winner-first.

## 11. Other outputs
`runs/cards.parquet`: one row per card (seasons 1991 onward): `player_id, tourney_date, season,
n_52w, n_10`, the 12 sums, `raw_*`, `shr_*`, `form, age, dob_missing, x_0..x_7`.
`runs/constants.csv`: `season, attr, k, m_prior, mu, sigma, n_pop` (attr in serve, ace, df, ret,
bps, bpc, form, age; k and m_prior are blank for form and age).
`runs/build_report.md`: exclusion counts by rule, id merges, invalid DOBs, per-season counts.
