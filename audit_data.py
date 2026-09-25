"""
audit_data.py
=============

Step zero of the ATP simulator project: find out what the data can actually
support before writing a single line of modelling code.

The project fits a point-level serve model of the form

    logit(p_serve, i against j) = mu + a.x_i - b.x_j + x_i^T W x_j

which needs, for every match, the number of service points each player played
and the number they won. Those columns exist in Jeff Sackmann's files, but not
for every year and not for every match, and the whole project's usable sample
size is decided by how far back the coverage actually goes.

This script answers that question and nothing else. It writes no features and
trains no model.

Usage
-----
    ./fetch_data.sh
    python3 audit_data.py

Data licence: Jeff Sackmann's tennis_atp data (now fetched from an archival mirror) is
CC BY-NC-SA 4.0. Non-commercial use only, attribution required, share-alike. The README
states this.
"""

import os
import sys

import pandas as pd

# Where fetch_data.sh puts the data, relative to this file.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tennis_atp")

# The serve statistics we need. Prefixed w_ for the match winner and l_ for the
# loser in Sackmann's schema. svpt is service points played, 1stWon and 2ndWon
# are points won on first and second serve, so (1stWon + 2ndWon) / svpt is the
# rate of service points won that the model predicts.
SERVE_COLS = ["svpt", "1stIn", "1stWon", "2ndWon", "ace", "df", "bpSaved", "bpFaced"]
STAT_COLS = [f"{side}_{c}" for side in ("w", "l") for c in SERVE_COLS]


def load_matches(start_year=1968, end_year=2026):
    """Load every atp_matches_YYYY.csv in range into one frame.

    We deliberately do NOT load the challenger, futures or qualifying files.
    Version 1 is tour level only: those events have different points, different
    fields, and much patchier statistics.
    """
    paths = []
    for year in range(start_year, end_year + 1):
        p = os.path.join(DATA_DIR, f"atp_matches_{year}.csv")
        if os.path.exists(p):
            paths.append((year, p))

    if not paths:
        sys.exit(
            f"No match files found in {DATA_DIR}\n"
            "Download the data first:\n"
            "  ./fetch_data.sh"
        )

    frames = []
    for year, p in paths:
        df = pd.read_csv(p, low_memory=False)
        df["year"] = year
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def coverage_by_year(df):
    """For each season, how complete are the serve statistics?

    This is the number that decides the project's sample size. A year where
    only 30% of matches carry serve counts is a year we mostly cannot use.
    """
    rows = []
    for year, g in df.groupby("year"):
        # A match is usable if BOTH players have service point counts, since the
        # model needs one training row per server and they come in pairs.
        usable = g["w_svpt"].notna() & g["l_svpt"].notna() & (g["w_svpt"] > 0) & (g["l_svpt"] > 0)
        rows.append(
            {
                "year": year,
                "matches": len(g),
                "with_serve_stats": int(usable.sum()),
                "coverage_%": round(100 * usable.mean(), 1),
                "players": pd.concat([g["winner_id"], g["loser_id"]]).nunique(),
                "tourneys": g["tourney_id"].nunique(),
            }
        )
    return pd.DataFrame(rows)


def surface_breakdown(df):
    """How many usable matches per surface? W is fitted per surface, so a
    surface with too few matches cannot support its own interaction matrix."""
    usable = df[df["w_svpt"].notna() & df["l_svpt"].notna()]
    out = usable.groupby("surface").agg(matches=("surface", "size"))
    out["share_%"] = (100 * out["matches"] / out["matches"].sum()).round(1)
    return out.sort_values("matches", ascending=False)


def match_volume_per_player(df, year_from):
    """Distribution of matches per player-season.

    Matters because a player's attribute vector is only meaningful if it is
    built from enough matches. This tells us how aggressive the shrinkage
    towards the tour mean needs to be, and how many player-seasons survive a
    minimum-match filter.
    """
    recent = df[(df["year"] >= year_from) & df["w_svpt"].notna() & df["l_svpt"].notna()]
    appearances = pd.concat(
        [
            recent[["year", "winner_id"]].rename(columns={"winner_id": "player_id"}),
            recent[["year", "loser_id"]].rename(columns={"loser_id": "player_id"}),
        ]
    )
    counts = appearances.groupby(["year", "player_id"]).size()
    return counts.describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(1), {
        "player_seasons_total": len(counts),
        "player_seasons_min_10_matches": int((counts >= 10).sum()),
        "player_seasons_min_20_matches": int((counts >= 20).sum()),
    }


def data_hazards(df):
    """Things that will quietly corrupt the model if not handled.

    Retirements and walkovers produce partial or empty statistics that look
    like real observations. Best-of-five matches have different point counts.
    Missing dob breaks the age feature.
    """
    usable = df[df["w_svpt"].notna() & df["l_svpt"].notna()].copy()
    score = usable["score"].astype(str)
    return {
        "usable_matches": len(usable),
        "retirements (RET in score)": int(score.str.contains("RET", na=False).sum()),
        "walkovers (W/O in score)": int(score.str.contains("W/O", na=False).sum()),
        "defaults (DEF in score)": int(score.str.contains("DEF", na=False).sum()),
        "best_of_5": int((usable["best_of"] == 5).sum()),
        "best_of_3": int((usable["best_of"] == 3).sum()),
        "missing winner dob": int(usable["winner_age"].isna().sum()),
        "missing surface": int(usable["surface"].isna().sum()),
        "svpt == 0 anomalies": int(((usable["w_svpt"] == 0) | (usable["l_svpt"] == 0)).sum()),
        "service points won > svpt (impossible)": int(
            ((usable["w_1stWon"] + usable["w_2ndWon"]) > usable["w_svpt"]).sum()
        ),
    }


def tour_baseline(df, year_from):
    """The mu in the model: tour-average service points won, per surface.

    Computed here so we have the real number rather than a remembered one, and
    so that the first sanity check on the fitted model has something to hit.
    """
    usable = df[(df["year"] >= year_from) & df["w_svpt"].notna() & df["l_svpt"].notna()]
    won = (usable["w_1stWon"] + usable["w_2ndWon"] + usable["l_1stWon"] + usable["l_2ndWon"])
    played = usable["w_svpt"] + usable["l_svpt"]
    by_surface = usable.assign(_won=won, _played=played).groupby("surface")[["_won", "_played"]].sum()
    by_surface["serve_pts_won_%"] = (100 * by_surface["_won"] / by_surface["_played"]).round(2)
    return by_surface[["serve_pts_won_%"]]


if __name__ == "__main__":
    df = load_matches()
    print(f"\nLoaded {len(df):,} matches from {df['year'].min()} to {df['year'].max()}\n")

    cov = coverage_by_year(df)
    print("=" * 78)
    print("SERVE STATISTIC COVERAGE BY YEAR")
    print("=" * 78)
    print(cov.to_string(index=False))

    # The first season where coverage is high enough to trust. Everything before
    # this is effectively unusable for a point-level model.
    good = cov[cov["coverage_%"] >= 90]
    first_good = int(good["year"].min()) if len(good) else None
    print(f"\nFirst season with >=90% serve-stat coverage: {first_good}")
    if first_good:
        usable_total = int(cov[cov["year"] >= first_good]["with_serve_stats"].sum())
        print(f"Usable matches from {first_good} onwards: {usable_total:,}")
        print(f"Training rows (two servers per match):   {usable_total * 2:,}")

    print("\n" + "=" * 78)
    print("SURFACE BREAKDOWN (usable matches, all years)")
    print("=" * 78)
    print(surface_breakdown(df).to_string())

    if first_good:
        print("\n" + "=" * 78)
        print(f"MATCHES PER PLAYER-SEASON (from {first_good})")
        print("=" * 78)
        desc, counts = match_volume_per_player(df, first_good)
        print(desc.to_string())
        for k, v in counts.items():
            print(f"  {k}: {v:,}")

        print("\n" + "=" * 78)
        print(f"TOUR BASELINE SERVICE POINTS WON (from {first_good}): this is mu")
        print("=" * 78)
        print(tour_baseline(df, first_good).to_string())

    print("\n" + "=" * 78)
    print("DATA HAZARDS")
    print("=" * 78)
    for k, v in data_hazards(df).items():
        print(f"  {k:<38} {v:>10,}")
    print()
