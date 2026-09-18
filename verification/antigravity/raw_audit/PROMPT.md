BACKGROUND
Raw ATP tennis match files are in data/tennis_atp/: atp_matches_1991.csv .. atp_matches_2026.csv (36 season files, tour-level singles) and atp_players.csv. The rules that define a valid match, identity merges, the season of a match and the date-of-birth checks are in verification/VERIFY_SPEC.md sections 1, 2, 3 and 8. Python with pandas is available as python3 and as "<repo>/.venv/bin/python".

GOAL
Independently audit the raw files against those rules and produce exact counts that a separately produced build report will later be compared with.

TASKS (write your own Python; apply section 2 merges first, then section 3 rules in order, first failing rule wins)
B1 Per season (file year): total matches; matches excluded under each of the 8 rules; valid matches; valid matches with surface in Hard, Clay, Grass; number of appearances (2 x valid).
B2 List the duplicate rows found by rule 8: tourney_id and match_num of the kept row and of each dropped row.
B3 List every match failing rule 6 or rule 7 with tourney_id, match_num and the condition that failed.
B4 DOB audit per section 8: players (id, name, dob) whose DOB is invalid; players without a parseable DOB who appear in valid matches (id, number of appearances); the distribution of |age from DOB - Sackmann age| over all valid appearances with a parseable DOB (median, 99th percentile, maximum, count above 0.11).
B5 Number of (player_id, tourney_date) pairs that have valid matches in more than one tourney_id.
B6 Per season, the share of matches with all 16 stat columns present.
B7 Per season: minimum and maximum tourney_date; confirm that the maximum of season Y-1 is below the minimum of season Y for every Y; state the last tourney_date in the 2026 file.
B8 Matches whose tourney_name matches the rule-4 regex, counted by season and by name.

ACCEPTANCE
A report verification/antigravity/raw_audit/raw_audit.md with one table per task and exact integers, the complete script you ran saved as verification/antigravity/raw_audit/raw_audit.py, and the report printed in full to stdout at the end.

SCOPE (must follow)
Write only inside verification/antigravity/raw_audit/. Do not open, read or modify atp_sim/, tests/, scripts/, runs/ or any file outside data/tennis_atp/ and verification/. Do not modify any data file. Do not install packages. Do not use the network.
