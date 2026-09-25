# Data provenance: where the match data comes from

Every number in this project traces back to one archive, through one mirror. The licence terms are
in [`LICENSE-DATA.md`](../LICENSE-DATA.md); how far the data can be trusted is in
[`DATA_SOURCE_VERIFICATION.md`](../verification/reports/DATA_SOURCE_VERIFICATION.md).

## Chain of custody

1. **Origin.** Jeff Sackmann (Tennis Abstract) compiled tour-level ATP results and match
   statistics from the ATP's official records and published them at
   `github.com/JeffSackmann/tennis_atp` under CC BY-NC-SA 4.0. His own notes travel with the data
   as `data/tennis_atp/UPSTREAM_README.md`: statistics are integer totals, exist for tour-level
   matches from 1991, are missing for some matches (the ATP has none, or they failed his sanity
   checks), and Davis Cup statistics are missing until the last few seasons (from 2016 in these
   files).
2. **Withdrawal.** The original repository was taken down before August 2026 and returns 404. The
   Wayback Machine's last capture of the live repository is dated 14 March 2026.
3. **Mirror.** `fetch_data.sh` downloads `github.com/Aneeshers/tennis-sackmann-archive`, pinned
   to commit `8373358` (June 2026). The mirror states that all data was collected and compiled by
   Jeff Sackmann, links the upstream repositories, keeps the upstream README and redistributes
   under the same licence. Only the main-tour singles files, the players file, the ranking files
   and the licence are copied; qualifying, challenger, futures and doubles files are left out.
4. **On disk.** 59 season files, 1968 to 2026, last event 25 May 2026 (Roland Garros).
5. **Cross-checked.** On 21 September 2026 the files were compared with TennisMyLife and with the
   official ATP website: [`DATA_SOURCE_VERIFICATION.md`](../verification/reports/DATA_SOURCE_VERIFICATION.md).

What the build does to it is recorded in `runs/build_report.md` (written by
`scripts/build_rows.py`; not in the repository): identity merges, every excluded match by rule,
and the three players whose date of birth contradicts the archive's own age column by decades.
The raw files and the finished table were then checked independently by Gemini 3.5 (in Google
Antigravity), working from the specification alone; see
[`verification/antigravity/`](../verification/antigravity/).

There is no live feed of this archive any more. It stops with Roland Garros 2026, so the project
replays completed seasons, scored against what actually happened, rather than forecasting the
season in progress.

## What the archive can support

From the audit of the raw files (`audit_data.py`):

| Question | Answer | Figure |
| --- | --- | --- |
| Matches in the archive | 1968 to 2026, tour level | 199,389 |
| When serve statistics start | nothing usable before this year | 1991 |
| Coverage 1991 to 2015 | stable plateau; the gap is mostly Davis Cup ties | about 88% |
| Coverage 2016 to 2024 | near complete | 94 to 99% |
| With serve statistics, three surfaces | hard 52,302 / clay 33,343 / grass 10,403, before exclusions | 96,048 |
| Rows (two servers per match) | before exclusions; the built table has 186,482 | 192,096 |
| Median matches per player per season | 2016 onward (5 from 1991 onward); mostly one-off qualifiers | 4 |

Carpet was retired as a tour surface around 2009, so it is never trained or simulated; carpet
matches still count towards the form cards. That median of four is the uncomfortable number: a
player with four matches behind him has a very unreliable profile, which is why the cards pull
thinly observed players back towards the tour average rather than believing their small sample.

## Files built from it

| What | Where | Contents | Size |
| --- | --- | --- | --- |
| **The raw archive** (read-only, never edited) | `data/tennis_atp/atp_matches_YYYY.csv` | One line per match: date, tournament, surface, both players, score, counting statistics for each side | 59 files, about 37 MB |
| **The training table** | `runs/rows.parquet` | One row per server per match: both form cards, surface, points served, points won | 186,482 rows |
| **The card table** (audit trail for the rows) | `runs/cards.parquet`, `runs/constants.csv` | Every card with its window counts, raw and shrunk rates, and the per-season constants used to standardise it | 105,195 cards |
| **The fitted models** | `artifacts/models/run*/model.pt` | Every number the model learned | 243 numbers each |

`data/` and `runs/` are gitignored: `fetch_data.sh` downloads the archive and
`scripts/build_rows.py` rebuilds the tables. The exact definitions are in
[`verification/VERIFY_SPEC.md`](../verification/VERIFY_SPEC.md).
