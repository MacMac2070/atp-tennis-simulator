# Raw ATP Match Data Audit Report

This report presents an independent audit of the raw ATP tennis match files (`atp_matches_1991.csv` through `atp_matches_2026.csv`) and `atp_players.csv` in `data/tennis_atp/` against the specifications defined in `verification/VERIFY_SPEC.md` (Sections 1, 2, 3, and 8).

All counts are exact integers produced by `raw_audit.py` with section 2 identity merges applied first, followed by section 3 exclusion rules evaluated in strict order (first failing rule wins).

## Task B1: Match Validation and Exclusion Breakdown per Season

Applied rules in order (first failing rule wins):
1. `stats_missing`: any of 16 stat columns is NaN.
2. `svpt_zero`: `w_svpt <= 0` or `l_svpt <= 0`.
3. `walkover`: `score` matches `W/O|Walkover` (case-insensitive).
4. `exhibition_format`: `tourney_name` matches `Next ?Gen|Laver Cup` (case-insensitive).
5. `same_player`: `winner_id == loser_id` (after identity merges).
6. `negative_stat`: any of 16 stat columns is below 0.
7. `impossible_stat`: logical tennis contradictions on serve/return/break points.
8. `duplicate`: duplicate `(tourney_id, winner_id, loser_id, round, score, w_svpt, l_svpt)` among matches passing rules 1-7.

| Season | Total | R1 (Missing) | R2 (Svpt 0) | R3 (W/O) | R4 (Exhib) | R5 (Same) | R6 (Neg) | R7 (Imposs) | R8 (Dup) | Valid Matches | Valid H/C/G | Appearances |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1991 | 3727 | 491 | 1 | 1 | 0 | 0 | 2 | 0 | 0 | 3232 | 2615 | 6464 |
| 1992 | 3792 | 419 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 3364 | 2824 | 6728 |
| 1993 | 3890 | 407 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3483 | 2933 | 6966 |
| 1994 | 3938 | 458 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 3474 | 2908 | 6948 |
| 1995 | 3800 | 425 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3375 | 2852 | 6750 |
| 1996 | 3774 | 449 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 3324 | 2786 | 6648 |
| 1997 | 3623 | 399 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 3220 | 2775 | 6440 |
| 1998 | 3591 | 366 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 3219 | 2836 | 6438 |
| 1999 | 3334 | 391 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2943 | 2673 | 5886 |
| 2000 | 3378 | 436 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2941 | 2802 | 5882 |
| 2001 | 3307 | 338 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2968 | 2798 | 5936 |
| 2002 | 3213 | 374 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2839 | 2668 | 5678 |
| 2003 | 3218 | 409 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2809 | 2640 | 5618 |
| 2004 | 3288 | 408 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2880 | 2679 | 5760 |
| 2005 | 3264 | 352 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2912 | 2665 | 5824 |
| 2006 | 3267 | 359 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2908 | 2708 | 5816 |
| 2007 | 3192 | 384 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2807 | 2714 | 5614 |
| 2008 | 3123 | 359 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2764 | 2733 | 5528 |
| 2009 | 3085 | 359 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2726 | 2726 | 5452 |
| 2010 | 3030 | 344 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2686 | 2686 | 5372 |
| 2011 | 3015 | 328 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2685 | 2685 | 5370 |
| 2012 | 3009 | 329 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2680 | 2680 | 5360 |
| 2013 | 2944 | 331 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2613 | 2613 | 5226 |
| 2014 | 2901 | 327 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2573 | 2573 | 5146 |
| 2015 | 2943 | 323 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2620 | 2620 | 5240 |
| 2016 | 2941 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2916 | 2905 | 5832 |
| 2017 | 2911 | 41 | 3 | 0 | 15 | 0 | 0 | 0 | 0 | 2852 | 2845 | 5704 |
| 2018 | 2897 | 35 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 2846 | 2846 | 5692 |
| 2019 | 2806 | 112 | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 2679 | 2679 | 5358 |
| 2020 | 1462 | 47 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1415 | 1415 | 2830 |
| 2021 | 2733 | 97 | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 2621 | 2621 | 5242 |
| 2022 | 2917 | 172 | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 2730 | 2730 | 5460 |
| 2023 | 2986 | 171 | 0 | 0 | 15 | 0 | 0 | 0 | 0 | 2800 | 2800 | 5600 |
| 2024 | 3076 | 60 | 0 | 0 | 24 | 0 | 0 | 1 | 0 | 2991 | 2991 | 5982 |
| 2025 | 2944 | 259 | 15 | 0 | 24 | 0 | 0 | 0 | 0 | 2646 | 2646 | 5292 |
| 2026 | 1449 | 258 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 1186 | 1186 | 2372 |
| **Total** | **112768** | **10842** | **56** | **1** | **139** | **0** | **2** | **1** | **0** | **101727** | **95856** | **203454** |

## Task B2: Duplicate Rows Audit (Rule 8)

Under strict sequential filtering (first failing rule wins), **0 matches** are excluded under Rule 8 because any potential duplicates in the raw files fail earlier rules (specifically Rule 1, `stats_missing`).

When evaluating the duplicate criterion `(tourney_id, winner_id, loser_id, round, score, w_svpt, l_svpt)` across all raw match rows in the dataset, exactly 2 duplicate pairs (4 rows) exist. Both pairs have missing stat values (`w_svpt` and `l_svpt` are NaN) from Davis Cup ties and are therefore eliminated by Rule 1 before Rule 8 is reached.

| Pair | Kept Tourney ID | Kept Match Num | Dropped Tourney ID | Dropped Match Num | Winner | Loser | Score | Round | Reason Dropped by Rule 1 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `2024-M-DC-2024-WG1-M-AUT-TUR-01` | 2 | `2024-M-DC-2024-WG1-M-AUT-TUR-01` | 3 | Lukas Neumayer | Cem Ilkel | 7-6(3) 6-2 | RR | All 16 stats are NaN |
| 2 | `2025-M-DC-2025-WG2-M-ESA-ROU-01` | 2 | `2025-M-DC-2025-WG2-M-ESA-ROU-01` | 3 | Gabriel Ghetu | Cesar Cruz | 6-1 2-6 6-2 | RR | All 16 stats are NaN |

## Task B3: Matches Failing Rule 6 (Negative Stat) or Rule 7 (Impossible Stat)

Exactly 2 matches fail Rule 6 and exactly 1 match fails Rule 7:

| Rule | Season | Tourney ID | Match Num | Winner | Loser | Score | Condition Failed |
|---|---|---|---|---|---|---|---|
| Rule 6 (negative_stat) | 1991 | `1991-329` | 54 | Ivan Lendl | Jim Courier | 6-4 6-1 | `Negative stat in l_bpSaved = -4.0` |
| Rule 6 (negative_stat) | 1991 | `1991-329` | 55 | Stefan Edberg | Ivan Lendl | 6-1 7-5 6-0 | `Negative stat in l_bpSaved = -6.0` |
| Rule 7 (impossible_stat) | 2024 | `2024-520` | 345 | Tomas Machac | Mariano Navone | 6-2 6-1 3-6 1-6 6-1 | `w_2ndWon (21.0) > w_svpt - w_1stIn (13.0)` |

## Task B4: Date-of-Birth (DOB) and Age Audit per Section 8

### B4.1 Players Whose DOB is Invalid
Per Section 8, a DOB is invalid (= missing) when for any valid match of that player, `|(tourney_date - DOB) in days / 365.25 - Sackmann's winner_age or loser_age| > 1.0`.

| Player ID | Player Name | Raw DOB | Valid Appearances | Max Age Discrepancy (Years) | Status |
|---|---|---|---|---|---|
| 101495 | Miguel Tobon | 20060619 | 13 | 37.99 | Invalid (flagged `dob_missing = True`) |
| 102060 | Ignacio Martinez | 19990113 | 4 | 26.61 | Invalid (flagged `dob_missing = True`) |
| 102772 | Yu Zhang | 20020822 | 2 | 26.35 | Invalid (flagged `dob_missing = True`) |

### B4.2 Players Without a Parseable DOB Appearing in Valid Matches

| Player ID | Player Name | Raw DOB in `atp_players.csv` | Valid Appearances |
|---|---|---|---|
| 107093 | Gil Kovalski | NaN (Empty) | 1 |
| 107653 | Marco Cacopardo | NaN (Empty) | 1 |
| 108136 | Roberto Raffa | NaN (Empty) | 1 |
| 108235 | Sergej Skakun | NaN (Empty) | 1 |
| 108999 | Dan Cantwell | NaN (Empty) | 1 |
| 127195 | Hamza Karmoussi | NaN (Empty) | 1 |
| 209294 | Diego Duran | NaN (Empty) | 1 |

### B4.3 Distribution of |Age from DOB - Sackmann Age| Over Valid Appearances with Parseable DOB

| Metric | All Parseable DOB Appearances | Valid DOB Appearances Only (Excl. 3 Invalid Players) |
|---|---|---|
| Appearance Count (N) | 203441 | 203422 |
| Median Discrepancy | 0.050582 | 0.050582 |
| 99th Percentile | 0.099316 | 0.099316 |
| Maximum Discrepancy | 37.988090 | 0.118823 |
| Count Discrepancies > 0.11 | 116 | 97 |

*Note: 6 appearances with parseable DOB have NaN Sackmann age in the match file (leaving N = 203,441). The 19 appearances with invalid DOB belong to the 3 players above (diffs between 26 and 38 years), which accounts exactly for 116 - 97 = 19 discrepancies > 0.11.*

## Task B5: Players with Valid Matches in More Than One Tournament on the Same Date

Total number of `(player_id, tourney_date)` pairs with valid matches in more than one `tourney_id`: **1**.

| Player ID | Player Name | Tourney Date | Tourney IDs |
|---|---|---|---|
| 105292 | Alejandro Gonzalez | 20160715 | `2016-M-DC-2016-G1-AM-M-CHI-COL-01, 2016-M-DC-2016-G2-AM-M-ESA-VEN-01` |

## Task B6: Share of Matches with All 16 Stat Columns Present per Season

| Season | Total Matches | Matches with All 16 Stats | Matches with Missing Stats | Share with All Stats Present |
|---|---|---|---|---|
| 1991 | 3727 | 3236 | 491 | 86.8259% |
| 1992 | 3792 | 3373 | 419 | 88.9504% |
| 1993 | 3890 | 3483 | 407 | 89.5373% |
| 1994 | 3938 | 3480 | 458 | 88.3697% |
| 1995 | 3800 | 3375 | 425 | 88.8158% |
| 1996 | 3774 | 3325 | 449 | 88.1028% |
| 1997 | 3623 | 3224 | 399 | 88.9870% |
| 1998 | 3591 | 3225 | 366 | 89.8079% |
| 1999 | 3334 | 2943 | 391 | 88.2723% |
| 2000 | 3378 | 2942 | 436 | 87.0930% |
| 2001 | 3307 | 2969 | 338 | 89.7793% |
| 2002 | 3213 | 2839 | 374 | 88.3598% |
| 2003 | 3218 | 2809 | 409 | 87.2902% |
| 2004 | 3288 | 2880 | 408 | 87.5912% |
| 2005 | 3264 | 2912 | 352 | 89.2157% |
| 2006 | 3267 | 2908 | 359 | 89.0113% |
| 2007 | 3192 | 2808 | 384 | 87.9699% |
| 2008 | 3123 | 2764 | 359 | 88.5046% |
| 2009 | 3085 | 2726 | 359 | 88.3630% |
| 2010 | 3030 | 2686 | 344 | 88.6469% |
| 2011 | 3015 | 2687 | 328 | 89.1211% |
| 2012 | 3009 | 2680 | 329 | 89.0661% |
| 2013 | 2944 | 2613 | 331 | 88.7568% |
| 2014 | 2901 | 2574 | 327 | 88.7280% |
| 2015 | 2943 | 2620 | 323 | 89.0248% |
| 2016 | 2941 | 2916 | 25 | 99.1499% |
| 2017 | 2911 | 2870 | 41 | 98.5915% |
| 2018 | 2897 | 2862 | 35 | 98.7919% |
| 2019 | 2806 | 2694 | 112 | 96.0086% |
| 2020 | 1462 | 1415 | 47 | 96.7852% |
| 2021 | 2733 | 2636 | 97 | 96.4508% |
| 2022 | 2917 | 2745 | 172 | 94.1035% |
| 2023 | 2986 | 2815 | 171 | 94.2733% |
| 2024 | 3076 | 3016 | 60 | 98.0494% |
| 2025 | 2944 | 2685 | 259 | 91.2024% |
| 2026 | 1449 | 1191 | 258 | 82.1946% |
| **Total** | **112768** | **101926** | **10842** | **90.3856%** |

## Task B7: Season Date Ranges, Ordering Verification, and Last Date in 2026

Ordering verification: Confirmation that `max(tourney_date)` of Season Y-1 < `min(tourney_date)` of Season Y for every Y from 1992 to 2026.

| Season | Min Tourney Date | Max Tourney Date | Previous Season Max Date | `max(Y-1) < min(Y)`? |
|---|---|---|---|---|
| 1991 | 19901231 | 19911210 | - | True |
| 1992 | 19911230 | 19921208 | 19911210 | True |
| 1993 | 19930104 | 19931207 | 19921208 | True |
| 1994 | 19940103 | 19941206 | 19931207 | True |
| 1995 | 19950102 | 19951205 | 19941206 | True |
| 1996 | 19960101 | 19961203 | 19951205 | True |
| 1997 | 19961230 | 19971128 | 19961203 | True |
| 1998 | 19980105 | 19981204 | 19971128 | True |
| 1999 | 19990104 | 19991203 | 19981204 | True |
| 2000 | 20000103 | 20001208 | 19991203 | True |
| 2001 | 20010101 | 20011130 | 20001208 | True |
| 2002 | 20011231 | 20021129 | 20011130 | True |
| 2003 | 20021230 | 20031128 | 20021129 | True |
| 2004 | 20040105 | 20041203 | 20031128 | True |
| 2005 | 20050103 | 20051202 | 20041203 | True |
| 2006 | 20060102 | 20061201 | 20051202 | True |
| 2007 | 20070101 | 20071130 | 20061201 | True |
| 2008 | 20071231 | 20081121 | 20071130 | True |
| 2009 | 20090104 | 20091204 | 20081121 | True |
| 2010 | 20100103 | 20101203 | 20091204 | True |
| 2011 | 20110102 | 20111202 | 20101203 | True |
| 2012 | 20120101 | 20121116 | 20111202 | True |
| 2013 | 20121230 | 20131115 | 20121116 | True |
| 2014 | 20131229 | 20141121 | 20131115 | True |
| 2015 | 20150104 | 20151127 | 20141121 | True |
| 2016 | 20160104 | 20161125 | 20151127 | True |
| 2017 | 20170102 | 20171124 | 20161125 | True |
| 2018 | 20180101 | 20181123 | 20171124 | True |
| 2019 | 20181231 | 20191124 | 20181123 | True |
| 2020 | 20200106 | 20201116 | 20191124 | True |
| 2021 | 20210104 | 20211205 | 20201116 | True |
| 2022 | 20220103 | 20221127 | 20211205 | True |
| 2023 | 20230102 | 20231127 | 20221127 | True |
| 2024 | 20240101 | 20241218 | 20231127 | True |
| 2025 | 20241227 | 20251217 | 20241218 | True |
| 2026 | 20260104 | 20260525 | 20251217 | True |

- **Strict Season Chronological Ordering**: **CONFIRMED** across all 35 season boundaries.
- **Last `tourney_date` in the 2026 file**: **`20260525`** (2026-05-25).

## Task B8: Matches Matching Rule-4 Exhibition Regex (`Next ?Gen|Laver Cup`)

In the raw files, a total of **180 matches** match the Rule-4 regex across 8 seasons (2017–2025).

| Season | Laver Cup | NextGen Finals | Next Gen Finals | Total Matches Matching Regex | Excluded by Rule 1 (Missing Stats) | Excluded by Rule 4 (Exhibition Format) |
|---|---|---|---|---|---|---|
| 2017 | 9 | 16 | 0 | 25 | 10 | 15 |
| 2018 | 8 | 16 | 0 | 24 | 8 | 16 |
| 2019 | 9 | 15 | 0 | 24 | 9 | 15 |
| 2021 | 6 | 15 | 0 | 21 | 6 | 15 |
| 2022 | 8 | 15 | 0 | 23 | 8 | 15 |
| 2023 | 0 | 15 | 0 | 15 | 0 | 15 |
| 2024 | 9 | 0 | 15 | 24 | 0 | 24 |
| 2025 | 9 | 0 | 15 | 24 | 0 | 24 |
| **Total** | **58** | **92** | **30** | **180** | **41** | **139** |
