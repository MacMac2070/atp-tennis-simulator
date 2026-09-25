# Independent checks with Antigravity

This folder holds independent checks run with Gemini 3.5 in Google Antigravity. Each data check
worked from the prompt saved in its `PROMPT.md`, which points it at the specification
[`../VERIFY_SPEC.md`](../VERIFY_SPEC.md) where needed, and was barred from reading the project's own
code (`atp_sim/`, `scripts/`). `source_check/` has no saved prompt.

Model outputs are kept verbatim, except that third-party email addresses and personal paths were
redacted, and the `|` characters inside two table cells of `table_check/table_check.md` were escaped
so its tables render.

| Folder | What it holds |
|---|---|
| [`provenance/`](provenance/) | Chain of custody for `data/tennis_atp/` (mirror, surviving forks, file hashes), 20 matches spot-checked against public sources, and the licence. |
| [`raw_audit/`](raw_audit/) | Exact per-season counts of valid and excluded matches, recomputed from the raw CSVs under sections 1, 2, 3 and 8 of the specification, with the script used. |
| [`source_check/`](source_check/) | Web research on where the Sackmann, TennisMyLife and mirror data come from, and an independent 2026 comparison of Sackmann against TennisMyLife, with the script used. |
| [`table_check/`](table_check/) | The training table, cards and constants recomputed from the raw files against the full specification, with the script used. Every check passes. |
| [`simulation_review/`](simulation_review/) | Project-written summaries, not verbatim output: a code review of the season simulator (alongside a separate Claude-based reviewer) and a check of the 2025 points table and rules. |

## Known caveats

- `provenance/provenance_report.md` concludes that "all 20 spot-checked matches agree", but its own
  table marks row 10 (2014 US Open final, Cilic's aces 18 against 17) as "PARTIALLY".
- `source_check/source_check.md` includes some speculation (about when and why the original Sackmann
  repository went offline) and a summary of forum opinion. Its per-event match counts are
  approximate: it gives 31 matches for every ATP 500 event, which does not hold for the 48-draw events.

Treat these as the model's commentary. The project's own conclusions are in
[`../reports/`](../reports/), mainly [`DATA_SOURCE_VERIFICATION.md`](../reports/DATA_SOURCE_VERIFICATION.md).
