# Is the Sackmann data trustworthy? Data source verification

Date of check: 21 September 2026

## The short answer

Yes. We compared the Jeff Sackmann match data this project trains on against a second dataset and
against the official ATP Tour website. They agree on almost everything, the few differences are too
small to affect the model, and where the sources disagreed and we could tell who was right, it was
Sackmann. We are keeping the original data.

## Why we checked

The model (trained through 2024, tested on 2025 and 2026) under-predicts how often servers win
points, by 1 to 3 percentage points. Before blaming the model, we wanted to rule out the other
suspect: that the underlying data was wrong.

## What we compared

| Source | What it is | How we used it |
|---|---|---|
| **Sackmann archive** (the original) | `data/tennis_atp/atp_matches_YYYY.csv`, from an archival mirror of Jeff Sackmann's `tennis_atp`. Stops at tournaments starting 25 May 2026. | The data under test. |
| **TennisMyLife (TML)** | Yearly CSVs from stats.tennismylife.org, 1968 to 2026, same column layout. Runs to 13 September 2026. | Bulk comparison of every match, 1992 to 2026. |
| **ATP Tour website** (atptour.com) | The official match statistics pages. | Spot check of 12 randomly chosen matches, 3 per decade. |
| **tennisdata.app** | Season CSVs 2021 to 2026. | **Not used.** The download page sits behind a "prove you are not a bot" check, so the files could not be fetched automatically. |

A second, independent implementation of the 2026 comparison was run by Antigravity (Gemini). Its
counts matched ours (0 winner disagreements, the same 9 score differences, near-identical serve
totals), so the comparison itself is not the product of a bug in one script.

**A caveat on independence.** TML is not a fully separate source. It was originally built from
Sackmann's files and now collects new matches from atptour.com. So agreement between TML and
Sackmann for older seasons is weaker evidence than it looks. That is why the ATP website spot check
matters: it is the only truly independent check here, and it covers all four decades.

## What was the same, and how much

### Bulk comparison: Sackmann vs TML, 1992 to 2026

Matches were paired on the two players' names, the round and the tournament date.

| | Count | Share |
|---|---|---|
| Matches in Sackmann | 109,041 | |
| Found in both sources | 108,801 | **99.8%** of Sackmann |
| Same winner | 108,798 | **99.997%** |
| Same score | 108,423 | **99.65%** |
| Same surface | 108,528 | **99.75%** |
| Identical on all 16 serve statistics | 106,717 | **98.1%** |

The number that matters most for the model is the share of service points won, by surface and
season. The two sources agree to within 0.002 in every case:

| Season | Surface | Sackmann | TML |
|---|---|---|---|
| 2024 | Hard | 0.6445 | 0.6445 |
| 2025 | Hard | 0.6467 | 0.6461 |
| 2025 | Clay | 0.6211 | 0.6208 |
| 2026 | Hard | 0.6586 | 0.6565 |
| 2026 | Clay | 0.6271 | 0.6277 |

Both sources show the same upward drift in serve rate into 2025 and 2026. So the rise is real, not
a data error.

### Spot check: 12 random matches vs the ATP website

Three matches per decade, drawn with a fixed random seed before any website was opened.

| Decade | Matches |
|---|---|
| 1990s | US Open 1999 Bastl d. Squillari; Prague 1992 Krumrey d. Viver; Roland Garros 1997 Lapentti d. Fetterlein |
| 2000s | Stuttgart 2004 final Canas d. Gaudio; Basel 2003 Coria d. Ljubicic; Queen's Club 2003 Malisse d. Karlovic |
| 2010s | Nice 2016 Sousa d. Anderson; Geneva 2016 Bellucci d. Kukushkin; Barcelona 2014 Nadal d. Dodig |
| 2020s | Madrid 2024 Fonseca d. Michelsen; Wimbledon 2023 Thompson d. Nakashima; Shanghai 2023 Khachanov d. Zhukayev |

Result: **12 of 12** agree on winner, score and round, and **192 of 192** serve statistics are
identical (aces, double faults, first serves in, service points, first and second serve points won,
break points saved and faced, for both players). Three match durations differ by one minute; the
model does not use duration.

## What was different

About 2,700 of the 108,801 paired matches (2.5%) differ on at least one field. The differences are
concentrated, not scattered.

**Winner: 3 matches.** One is a join artefact (two different round-robin matches at Buenos Aires
2007 paired together). One is a walkover at the 2024 Olympics with no statistics. One is a genuine
conflict: a 2025 Davis Cup match tiebreak recorded as [8-10] in one source and [10-8] in the other.

**Serve statistics: 2,084 matches.**
- 997: Sackmann leaves the statistics blank and TML has numbers (mostly Davis Cup ties, plus a few
  late-round Grand Slam matches such as the 2026 Roland Garros semi-final and final).
- 236: the reverse, TML blank and Sackmann filled.
- 851 (0.8% of matches): both have numbers and they disagree. These cluster in events not run by
  the ATP: Roland Garros 2026 (124), Australian Open 2026 (114), US Open 2025 (100), the 2012 and
  1992 Olympics (63 each), Canada Masters 1995 (51), Madrid Masters 2003 (47) and the Düsseldorf
  team event in several years (about 26 each). In the recent Grand Slams the disagreement is in how
  points won are split between first and second serve; the total is the same or nearly so.

**Surface: 273 matches.** Mostly carpet versus hard for four 1990s indoor events (Philadelphia 1993;
Singapore, Basel and Shanghai 1998) and some Davis Cup ties. Also Santiago 2025: Sackmann says clay,
TML says hard.

**Score: 378 matches.** Nearly all are formatting (`7-5 0-0 RET` against `7-5 RET`, `[10-7]` against
`1-0(7)`), plus a few typos.

**Duration: about 3,400 matches**, typically 1 to 3 minutes apart. Not used by the model.

**Coverage.** Sackmann stops at 25 May 2026, so it has no 2026 grass season, US Open or summer hard
courts. TML has 855 more 2026 matches, through 13 September. This explains why the model evaluation
showed "no rows" for grass in 2026.

## Why we are still using the original data

1. **It passed the strongest test.** The only fully independent check, the official ATP website,
   matched Sackmann on every one of 192 statistics across four decades.
2. **Where the sources disagreed and we could judge, Sackmann was right.**
   - Santiago 2025 is a clay tournament, as Sackmann says.
   - Marbella 1996: TML records a set as `0-7`, which is impossible. Sackmann has `0-6`.
   - Australian Open 2026: the ATP website (which TML copies) shows Hijikata landing 87 of 92 first
     serves (95%) and "0 service games played". Sackmann has 55 of 89, which is believable. The ATP
     site's Grand Slam feed looks faulty, so "correcting" Sackmann towards it would make the data worse.
3. **The differences are far too small to explain the model's error.** The largest gap between
   sources in serve rate is 0.002. The model's bias is 0.015 to 0.027, roughly ten times larger.
   Like worrying about a 2 mm measuring error on a part that is 20 mm out of tolerance.
4. **Switching would add risk for no gain.** TML uses different player IDs (ATP's alphanumeric codes
   rather than Sackmann's numbers), so swapping sources would mean re-mapping every player by name,
   with its own chance of error, to fix a problem that does not exist.

**Conclusion: the data is sound, so the under-prediction of serve comes from the model.** It anchors
to the 1992 to 2024 average serve rate while the real rate has drifted upwards.

## Known limitations of the original data

- It ends on 25 May 2026. If a fuller 2026 test set is wanted, TML can top it up (855 matches,
  including 297 on grass), mapping new rows by player name and treating its Grand Slam serve splits
  with caution.
- About 200 of the 2026 matches have blank serve statistics. The pipeline already drops such rows,
  so this costs a little sample size and nothing else.
- Not checked: which source is right for the four 1990s carpet-or-hard events, and for the 2025
  Davis Cup tiebreak. The model only uses hard, clay and grass, so the carpet label decides whether
  those roughly 120 matches are included at all.
- tennisdata.app was never compared. If its 2021 to 2026 CSVs are downloaded by hand into
  `verification/external/tennisdata_app/`, that third comparison can be added.

## Where everything is

| File | Contents |
|---|---|
| `verification/cross_check_sources.py` | The comparison script. Run with `python verification/cross_check_sources.py`. |
| `verification/reports/cross_check_summary.md` | Season-by-season tables behind the numbers above. |
| `verification/out/cross_check_mismatches.csv` | Every mismatching match, both sources side by side. |
| `verification/reports/atp_spot_check.md` | The 12 ATP website checks with page addresses. |
| `verification/reports/atp_spot_check_sample.csv` | The 12 sampled rows and the random seed used. |
| `verification/antigravity/source_check/` | Antigravity's independent 2026 check. |
| `verification/external/SOURCES.md` | Download addresses, dates and file hashes for the TML files. |
