# ATP Training Table Independent Verification Report

Generated on: 2026-09-17 22:57:18  
Specification: `verification/VERIFY_SPEC.md`  
Overall Verdict: **PASS**  

## Executive Summary

| Check | Description | Status | Details |
|---|---|---|---|
| **C1** | Random sample of 1,000 rows recomputed from raw files | **PASS** | 1,000/1,000 rows agree across all cards and row columns (Seed: 20260917) |
| **C2** | Recomputed priors and constants (1995, 2010, 2024) | **PASS** | 24/24 attr specs agree: m_prior & mu <= 1e-9, sigma rel <= 1e-8, n_pop exact |
| **C3** | Delete-the-future (50 cards, season >= 1992) & Control | **PASS** | 50/50 DTF cards agree; Control confirms temporal boundary (Seed: 20260917) |
| **C4a** | Row count equals twice valid H/C/G matches (>= 1992) | **PASS** | Rows = 186,482 == 2 * 93,241 valid matches |
| **C4b** | Every match_id appears exactly twice with swapped IDs | **PASS** | 93,241 unique match_ids, each exactly 2 rows with swapped server/returner |
| **C4c** | svpt and won equal raw file values for server | **PASS** | 186,482/186,482 rows match raw match statistics exactly |
| **C4d** | Column set matches Section 10 exactly, no forbidden regex | **PASS** | Exactly 36 columns; 0 match regex `win\|los\|score\|rank\|minutes\|name\|seed` |
| **C4e** | Every x value is finite | **PASS** | 2,983,712 x values evaluated; 100% finite (no NaN, Inf, -Inf) |
| **C4f** | No Carpet, missing surface, season < 1992, or Next Gen/Laver Cup | **PASS** | 0 Carpet/missing surface, 0 season < 1992, 0 Next Gen / Laver Cup rows |
| **C4g** | Two rows of each match ordered by server_id | **PASS** | 93,241/93,241 match pairs have server_id(row 1) < server_id(row 2) |
| **C4h** | Every (server_id, tourney_date) exists in cards.parquet | **PASS** | 100% of row server cards exist in cards.parquet (0 missing) |
| **C4i** | Zero-history cards (n_52w = 0) have shrunk rates = m_prior and form = 0 | **PASS** | 4,367 zero-history cards verified; all have form = 0 and shr_* = m_prior |
| **C4j** | Rows with i_dob_missing = True have x_i_7 = 0 | **PASS** | 22 rows with i_dob_missing = True all have x_i_7 = 0.0 |
| **C4k** | Distribution of x_i_* per season & attribute (flag outliers) | **PASS** | 280 distributions computed; 3 flagged outliers reported |
| **C4l** | Standardising P(Y-1) with season Y constants gives mean 0, SD 1 | **PASS** | 272 season-attr checks (1993-2026): max mean err 1.05e-14, max SD err 8.88e-15 |

---
## Check C1: 1,000 Sampled Rows Recomputation
**Verdict**: **PASS**
- **Random Seed**: `20260917`
- **Sample Size**: 1,000 rows from `runs/rows.parquet` (covering 2,000 player-date cards)
- **Agreement Count**: **1000 / 1000** rows agreed in every single field across cards and row columns
- **Disagreements**: **0**
- Every recomputed integer sum (`svpt_52, svwon_52, ace_52, df_52, bpf_52, bps_52, rpt_52, rwon_52, obpf_52, obps_52, svpt_10, svwon_10, n_52w, n_10`) was exact.
- Every raw rate, shrunk rate, form, and age agreed within 1e-9 (with NaN == NaN).
- Every standardised attribute (`x_i_0..x_i_7` and `x_j_0..x_j_7`) agreed within 1e-6.

---
## Check C2: Recomputed Priors and Standardisation Constants (1995, 2010, 2024)
**Verdict**: **PASS**

| Season | Attribute | Recomputed m_prior | Stored m_prior | Diff | Recomputed mu | Stored mu | Diff | Recomputed sigma | Stored sigma | Rel Diff | n_pop Calc | n_pop Stored | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1995 | serve | 0.615098 | 0.615098 | 0.0e+00 | 0.614100 | 0.614100 | 0.0e+00 | 0.027940 | 0.027940 | 2.6e-15 | 5816 | 5816 | PASS |
| 1995 | ace | 0.061215 | 0.061215 | 1.4e-17 | 0.057039 | 0.057039 | 7.6e-17 | 0.030664 | 0.030664 | 1.6e-15 | 5816 | 5816 | PASS |
| 1995 | df | 0.040784 | 0.040784 | 7.6e-17 | 0.040359 | 0.040359 | 4.2e-17 | 0.012785 | 0.012785 | 1.8e-15 | 5816 | 5816 | PASS |
| 1995 | ret | 0.384902 | 0.384902 | 0.0e+00 | 0.388573 | 0.388573 | 1.1e-16 | 0.022970 | 0.022970 | 4.1e-15 | 5816 | 5816 | PASS |
| 1995 | bps | 0.593307 | 0.593307 | 0.0e+00 | 0.596216 | 0.596216 | 0.0e+00 | 0.021476 | 0.021476 | 1.3e-15 | 5816 | 5816 | PASS |
| 1995 | bpc | 0.406693 | 0.406693 | 5.6e-17 | 0.409559 | 0.409559 | 5.6e-17 | 0.016859 | 0.016859 | 4.3e-15 | 5816 | 5816 | PASS |
| 1995 | form | - | - | - | -0.003386 | -0.003386 | 6.8e-17 | 0.017340 | 0.017340 | 1.0e-15 | 5816 | 5816 | PASS |
| 1995 | age | - | - | - | 24.765126 | 24.765126 | 0.0e+00 | 3.135218 | 3.135218 | 0.0e+00 | 5816 | 5816 | PASS |
| 2010 | serve | 0.632825 | 0.632825 | 0.0e+00 | 0.635279 | 0.635279 | 0.0e+00 | 0.030284 | 0.030284 | 1.0e-15 | 5452 | 5452 | PASS |
| 2010 | ace | 0.076332 | 0.076332 | 4.2e-17 | 0.075432 | 0.075432 | 8.3e-17 | 0.036883 | 0.036883 | 5.6e-16 | 5452 | 5452 | PASS |
| 2010 | df | 0.035174 | 0.035174 | 3.5e-17 | 0.034891 | 0.034891 | 9.7e-17 | 0.009390 | 0.009390 | 8.9e-15 | 5452 | 5452 | PASS |
| 2010 | ret | 0.367175 | 0.367175 | 5.6e-17 | 0.369885 | 0.369885 | 5.6e-17 | 0.023846 | 0.023846 | 2.8e-15 | 5452 | 5452 | PASS |
| 2010 | bps | 0.605054 | 0.605054 | 0.0e+00 | 0.610558 | 0.610558 | 1.1e-16 | 0.022061 | 0.022061 | 3.6e-15 | 5452 | 5452 | PASS |
| 2010 | bpc | 0.394946 | 0.394946 | 5.6e-17 | 0.395842 | 0.395842 | 1.1e-16 | 0.016043 | 0.016043 | 4.8e-15 | 5452 | 5452 | PASS |
| 2010 | form | - | - | - | -0.003558 | -0.003558 | 8.5e-17 | 0.016473 | 0.016473 | 2.7e-15 | 5452 | 5452 | PASS |
| 2010 | age | - | - | - | 26.165866 | 26.165866 | 7.1e-15 | 3.314814 | 3.314814 | 1.3e-16 | 5452 | 5452 | PASS |
| 2024 | serve | 0.638208 | 0.638208 | 0.0e+00 | 0.638848 | 0.638848 | 0.0e+00 | 0.027785 | 0.027785 | 3.7e-16 | 5600 | 5600 | PASS |
| 2024 | ace | 0.076694 | 0.076694 | 6.9e-17 | 0.075531 | 0.075531 | 6.9e-17 | 0.034187 | 0.034187 | 1.6e-15 | 5600 | 5600 | PASS |
| 2024 | df | 0.035024 | 0.035024 | 3.5e-17 | 0.034597 | 0.034597 | 6.9e-18 | 0.011784 | 0.011784 | 6.9e-15 | 5600 | 5600 | PASS |
| 2024 | ret | 0.361792 | 0.361792 | 5.6e-17 | 0.364476 | 0.364476 | 5.6e-17 | 0.023315 | 0.023315 | 2.4e-15 | 5600 | 5600 | PASS |
| 2024 | bps | 0.612609 | 0.612609 | 0.0e+00 | 0.612593 | 0.612593 | 0.0e+00 | 0.019513 | 0.019513 | 2.3e-15 | 5600 | 5600 | PASS |
| 2024 | bpc | 0.387391 | 0.387391 | 5.6e-17 | 0.392191 | 0.392191 | 5.6e-17 | 0.014592 | 0.014592 | 2.4e-15 | 5600 | 5600 | PASS |
| 2024 | form | - | - | - | -0.002832 | -0.002832 | 7.0e-17 | 0.014911 | 0.014911 | 2.9e-15 | 5600 | 5600 | PASS |
| 2024 | age | - | - | - | 26.879125 | 26.879125 | 0.0e+00 | 4.311797 | 4.311797 | 0.0e+00 | 5600 | 5600 | PASS |

---
## Check C3: Delete-the-Future Temporal Boundary Audit
**Verdict**: **PASS**
- **Random Seed**: `20260917`
- **Sample Size**: 50 cards from `runs/cards.parquet` with season >= 1992
- **Primary Test (matches dated on or after D removed from raw matches)**: **50 / 50** cards agreed exactly with stored cards (0 disagreements).
- **Control 1 (matches strictly after D removed, same-day matches kept in raw data; card built per Section 5 spec window `[D - 364 days, D)`)**: **0 / 50** cards changed.
  - *Explanation*: Section 5 strictly defines the 52-week window as `[D - 364 days, D)` with an exclusive upper bound ("Every appearance dated D (any event) is excluded"). Thus, retaining matches dated D in the raw dataset does not alter the reconstructed card because same-day matches are never admitted into the window.
- **Control 2 (same-day matches kept in raw data AND included in the window `[D - 364 days, D]`)**: **50 / 50** cards changed (100% changed).
  - *Explanation*: Every card corresponds to a player who played on date D; if same-day matches were mistakenly admitted into the window, all 50 cards would deviate from their stored values. This confirms the table strictly enforces future-leakage prevention.

---
## Check C4: Full-Table Invariants (C4a through C4l)

### C4a: Row Count vs Valid Matches
- **Verdict**: **PASS**
- Valid matches with season >= 1992 on Hard, Clay, Grass: **93,241**
- Expected rows (2 * valid matches): **186,482**
- Stored rows in `runs/rows.parquet`: **186,482** (Exact match)

### C4b: Match ID Multiplicity and Player Swap
- **Verdict**: **PASS**
- Total unique `match_id` values: **93,241**
- All `match_id` appear exactly twice: **True**
- Across all row pairs, `server_id` and `returner_id` are strictly swapped: **True**

### C4c: svpt and won Equal Raw File Server Statistics
- **Verdict**: **PASS**
- Rows evaluated: **186,482**
- Mismatches in `svpt` or `won`: **0**

### C4d: Schema and Column Name Audit
- **Verdict**: **PASS**
- Total columns: **36** (Section 10 requires 36 columns)
- Exact order and name match: **True**
- Columns matching regex `win|los|score|rank|minutes|name|seed`: **0**

### C4e: Finite Feature Values
- **Verdict**: **PASS**
- Evaluated 16 features (`x_i_0..7`, `x_j_0..7`) across all 186,482 rows (2,983,712 values)
- All values finite (no NaN, Inf, -Inf): **True**

### C4f: Surface, Season, and Tournament Exclusions
- **Verdict**: **PASS**
- Distinct surfaces present: `['Clay', 'Grass', 'Hard']`
- Carpet or missing surface rows: **0**
- Rows with season < 1992: **0** (Minimum season: 1992)
- Rows matching `Next ?Gen|Laver Cup`: **0**

### C4g: Ordering Within Each match_id
- **Verdict**: **PASS**
- Match row pairs checked: **93,241**
- All pairs satisfy `server_id(row 1) < server_id(row 2)`: **True**

### C4h: Coverage of (server_id, tourney_date) in cards.parquet
- **Verdict**: **PASS**
- Distinct `(server_id, tourney_date)` pairs in `rows.parquet`: **96,420**
- Missing keys in `cards.parquet`: **0**

### C4i: Zero-History Cards Shrinkage and Form
- **Verdict**: **PASS**
- Cards in `cards.parquet` with `n_52w = 0`: **4,367**
- Cards with `form != 0.0` or shrunk rates differing from `m_prior`: **0**

### C4j: Missing DOB Zero Age Feature
- **Verdict**: **PASS**
- Rows with `i_dob_missing = True`: **22**
- All have `x_i_7 = 0.0`: **True**

### C4k: Distribution of x_i_* Across Seasons and Outlier Flags
- **Verdict**: **PASS**
- Total distributions computed: **280** (35 seasons x 8 attributes)
- Outlier criteria: `|mean| > 0.5` or `SD < 0.7` or `SD > 1.3`
- Outliers flagged: **3**

#### Flagged Outlier Attributes:
| Season | Feature | Attribute Name | Mean | Population SD | Flag Reason |
|---|---|---|---:|---:|---|
| 1992 | `x_i_5` | bpc | -0.1299 | 1.3067 | SD = 1.3067 > 1.3 |
| 1992 | `x_i_6` | form | -0.2732 | 1.3290 | SD = 1.3290 > 1.3 |
| 2012 | `x_i_5` | bpc | +0.5378 | 1.0623 | \|mean\| = 0.5378 > 0.5 |

#### Full Summary of Mean and Population SD for x_i_* by Season:

| Season | serve (x0) | ace (x1) | df (x2) | ret (x3) | bps (x4) | bpc (x5) | form (x6) | age (x7) |
|---|---|---|---|---|---|---|---|---|
| 1992 | +0.20 (1.05) | +0.12 (1.14) | +0.05 (1.12) | -0.15 (1.05) | +0.26 (1.27) | -0.13 (1.31)* | -0.27 (1.33)* | +0.10 (1.04) |
| 1993 | +0.03 (1.02) | +0.12 (1.02) | +0.17 (1.04) | -0.03 (1.00) | +0.25 (1.00) | -0.31 (0.97) | +0.08 (1.01) | -0.01 (0.90) |
| 1994 | +0.03 (0.95) | +0.11 (1.09) | +0.19 (1.05) | -0.04 (1.05) | +0.02 (0.92) | -0.10 (1.12) | -0.04 (1.01) | +0.06 (1.01) |
| 1995 | +0.16 (1.03) | +0.16 (1.05) | +0.03 (1.00) | -0.12 (1.03) | +0.15 (1.05) | -0.14 (1.03) | -0.06 (1.02) | +0.05 (1.02) |
| 1996 | -0.03 (0.96) | +0.03 (1.02) | +0.01 (0.95) | +0.01 (0.96) | -0.05 (1.03) | +0.03 (0.88) | +0.06 (0.97) | -0.01 (1.00) |
| 1997 | +0.07 (1.03) | +0.10 (1.05) | +0.18 (1.01) | -0.11 (0.95) | -0.17 (0.96) | +0.23 (1.02) | +0.02 (0.97) | +0.03 (0.96) |
| 1998 | -0.01 (1.00) | +0.06 (0.94) | +0.09 (0.99) | +0.04 (0.93) | +0.14 (0.98) | -0.20 (0.93) | -0.06 (1.14) | +0.06 (1.04) |
| 1999 | +0.03 (0.99) | -0.03 (0.98) | -0.07 (0.94) | -0.06 (0.98) | +0.08 (0.98) | -0.09 (0.98) | +0.02 (0.96) | +0.00 (1.04) |
| 2000 | +0.03 (0.97) | +0.04 (1.02) | -0.02 (1.10) | -0.08 (1.03) | +0.25 (0.96) | -0.37 (1.00) | +0.11 (0.94) | +0.02 (1.02) |
| 2001 | +0.04 (0.98) | +0.06 (0.95) | +0.03 (1.02) | -0.03 (1.02) | +0.09 (1.04) | -0.13 (0.93) | -0.13 (1.04) | -0.02 (1.03) |
| 2002 | +0.04 (0.97) | +0.00 (1.02) | -0.07 (0.98) | -0.03 (1.00) | -0.08 (1.12) | +0.11 (1.15) | +0.01 (0.98) | +0.01 (0.96) |
| 2003 | +0.00 (1.05) | -0.04 (1.11) | -0.05 (0.92) | -0.06 (1.19) | -0.32 (0.94) | +0.44 (1.02) | +0.08 (0.98) | +0.03 (1.02) |
| 2004 | +0.11 (1.08) | +0.08 (1.07) | -0.02 (1.00) | -0.12 (1.02) | -0.03 (1.04) | +0.13 (1.00) | +0.03 (1.02) | +0.02 (1.04) |
| 2005 | +0.05 (1.01) | -0.04 (0.98) | -0.25 (0.93) | +0.01 (1.04) | +0.30 (1.07) | -0.44 (1.09) | -0.09 (1.08) | +0.03 (1.02) |
| 2006 | -0.09 (0.99) | -0.02 (0.92) | -0.22 (0.98) | +0.06 (0.95) | -0.09 (0.99) | +0.10 (0.87) | +0.01 (0.95) | +0.04 (0.98) |
| 2007 | +0.16 (1.02) | +0.06 (1.10) | -0.25 (0.87) | -0.10 (1.02) | +0.06 (0.92) | -0.01 (1.18) | -0.00 (1.00) | +0.04 (1.01) |
| 2008 | +0.16 (0.98) | +0.07 (0.99) | -0.04 (1.04) | -0.21 (0.98) | +0.09 (0.95) | -0.09 (0.94) | +0.02 (0.97) | -0.03 (0.98) |
| 2009 | +0.03 (1.03) | +0.00 (1.01) | +0.15 (1.00) | -0.00 (0.95) | +0.28 (1.02) | -0.44 (0.97) | -0.04 (0.97) | +0.14 (0.94) |
| 2010 | -0.02 (0.98) | +0.05 (0.99) | -0.08 (0.98) | -0.05 (1.02) | -0.06 (1.03) | +0.04 (0.98) | +0.03 (1.03) | +0.04 (0.94) |
| 2011 | -0.02 (1.03) | -0.01 (1.04) | +0.05 (0.98) | +0.05 (1.02) | -0.07 (1.00) | +0.10 (1.03) | -0.12 (1.00) | +0.09 (1.03) |
| 2012 | -0.14 (1.07) | -0.11 (0.95) | +0.15 (1.04) | +0.17 (0.98) | -0.31 (1.10) | +0.54 (1.06)* | +0.16 (0.90) | +0.15 (1.01) |
| 2013 | +0.12 (0.96) | +0.08 (0.99) | -0.05 (1.06) | -0.18 (1.02) | +0.31 (1.08) | -0.50 (0.91) | -0.07 (1.13) | +0.13 (1.05) |
| 2014 | +0.07 (1.03) | +0.09 (1.13) | +0.15 (1.06) | -0.09 (1.06) | +0.18 (0.91) | -0.39 (1.06) | +0.09 (0.96) | +0.09 (1.06) |
| 2015 | +0.23 (1.00) | +0.11 (1.09) | -0.12 (0.95) | -0.20 (1.05) | +0.05 (1.01) | +0.07 (1.02) | -0.10 (0.95) | +0.02 (1.06) |
| 2016 | -0.11 (0.92) | -0.06 (0.93) | +0.14 (0.93) | +0.02 (0.92) | +0.06 (0.97) | -0.18 (0.92) | -0.03 (0.99) | -0.01 (1.11) |
| 2017 | -0.11 (1.01) | -0.06 (0.97) | +0.16 (0.98) | +0.19 (1.01) | -0.36 (0.95) | +0.49 (1.02) | +0.08 (0.98) | +0.02 (1.06) |
| 2018 | +0.08 (0.99) | +0.04 (1.01) | -0.01 (1.11) | -0.10 (0.95) | +0.19 (0.85) | -0.27 (0.90) | -0.02 (1.05) | -0.07 (1.02) |
| 2019 | +0.07 (1.01) | +0.03 (1.08) | -0.07 (1.08) | -0.07 (1.06) | +0.17 (1.09) | -0.25 (1.07) | +0.01 (1.07) | +0.01 (1.02) |
| 2020 | -0.02 (0.99) | -0.01 (0.97) | -0.12 (1.04) | +0.01 (0.94) | -0.01 (0.94) | -0.06 (0.92) | -0.02 (0.87) | -0.09 (0.96) |
| 2021 | -0.37 (1.01) | -0.20 (0.91) | +0.01 (1.04) | +0.37 (0.97) | -0.27 (1.04) | +0.30 (1.07) | +0.22 (0.94) | +0.03 (1.01) |
| 2022 | +0.18 (0.96) | +0.07 (1.04) | -0.03 (1.04) | -0.09 (1.02) | +0.00 (1.01) | +0.19 (0.96) | -0.17 (1.19) | -0.06 (0.97) |
| 2023 | +0.14 (0.97) | +0.01 (0.86) | -0.13 (0.95) | -0.24 (0.98) | +0.14 (0.94) | -0.28 (0.99) | -0.04 (0.91) | -0.04 (0.95) |
| 2024 | +0.06 (0.95) | +0.06 (0.91) | -0.08 (0.95) | -0.06 (0.89) | +0.33 (1.13) | -0.33 (0.95) | +0.04 (1.05) | -0.05 (1.02) |
| 2025 | +0.05 (1.08) | +0.12 (1.09) | +0.10 (0.99) | -0.09 (1.16) | +0.15 (0.99) | -0.27 (1.10) | -0.03 (1.06) | +0.02 (0.95) |
| 2026 | +0.08 (0.95) | +0.07 (0.99) | +0.03 (1.00) | -0.07 (0.98) | +0.07 (0.91) | -0.15 (1.03) | +0.32 (0.97) | +0.02 (1.03) |

*(Entries marked with `*` indicate flagged attributes outside nominal ranges).*

### C4l: Standardisation of P(Y-1) Against Season Y Constants (1993 - 2026)
- **Verdict**: **PASS**
- Seasons verified: 1993 to 2026 (34 seasons x 8 attributes = 272 evaluations)
- Maximum absolute error in mean: **1.05e-14** (Tolerance: 1.0e-09)
- Maximum absolute error in population SD: **8.88e-15** (Tolerance: 1.0e-09)
- Violations: **0**

---
## Final Overall Verdict: **PASS**
Total verification execution time: **9.57 seconds**.
