"""Load the Sackmann archive and decide which matches count.

Implements VERIFY_SPEC sections 1 to 3 (files, seasons, identity merges, the
exclusion rules) and section 8 (date-of-birth cleaning). Nothing here ever writes
to data/: the raw archive is read-only.
"""

from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "tennis_atp")

LIVE_SURFACES = ("Hard", "Clay", "Grass")
SERVE_COLS = ["svpt", "1stIn", "1stWon", "2ndWon", "ace", "df", "bpSaved", "bpFaced"]
STAT_COLS = [f"{side}_{c}" for side in ("w", "l") for c in SERVE_COLS]

FIRST_SEASON = 1991  # first season file with serve statistics
LAST_SEASON = 2026

# Split identities in the tour-level files (same player, two ids). Old id -> kept id.
ID_MERGES = {211776: 212021, 209870: 211326}

WALKOVER_RE = r"W/O|Walkover"
EXHIBITION_RE = r"Next ?Gen|Laver Cup"  # four-game sets / match tiebreaks: not tour scoring
DUPLICATE_KEY = ["tourney_id", "winner_id", "loser_id", "round", "score", "w_svpt", "l_svpt"]
EXCLUSION_RULES = (
    "stats_missing", "svpt_zero", "walkover", "exhibition_format",
    "same_player", "negative_stat", "impossible_stat", "duplicate",
)


def load_matches(
    start_year: int = FIRST_SEASON,
    end_year: int = LAST_SEASON,
    data_dir: str = DATA_DIR,
) -> pd.DataFrame:
    """Load tour-level singles files in [start_year, end_year]; `season` is the file year."""
    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        path = os.path.join(data_dir, f"atp_matches_{year}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, low_memory=False)
        df["season"] = year
        df["year"] = year  # kept for audit_data.py compatibility
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No match files in {data_dir}. Run ./fetch_data.sh first.")
    return pd.concat(frames, ignore_index=True)


def parse_players(players: pd.DataFrame) -> pd.DataFrame:
    """Index by player_id and parse `dob` strictly as YYYYMMDD; anything else is missing."""
    out = players.copy()
    dob = pd.to_numeric(out["dob"], errors="coerce").round().astype("Int64").astype("string")
    out["dob"] = pd.to_datetime(dob, format="%Y%m%d", errors="coerce")
    return out.set_index("player_id")


def load_players(data_dir: str = DATA_DIR) -> pd.DataFrame:
    return parse_players(pd.read_csv(os.path.join(data_dir, "atp_players.csv"), low_memory=False))


def apply_id_merges(df: pd.DataFrame, merges: dict[int, int] = ID_MERGES) -> pd.DataFrame:
    out = df.copy()
    for old, new in merges.items():
        out.loc[out["winner_id"] == old, "winner_id"] = new
        out.loc[out["loser_id"] == old, "loser_id"] = new
    return out


def prepare_matches(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the merges and the eight exclusion rules in order (first failing rule wins).

    Returns the valid matches (sorted by date, event, match number, with datetime
    `tourney_date`, `match_id`, `retired`, `defaulted`) and the exclusion counts.
    """
    if "season" not in raw.columns:
        raise ValueError("matches need a `season` column (the file year); use load_matches")
    df = apply_id_merges(raw)
    df["winner_id"] = df["winner_id"].astype("int64")
    df["loser_id"] = df["loser_id"].astype("int64")

    stats = df[STAT_COLS].apply(pd.to_numeric, errors="coerce")
    score = df["score"].astype("string").fillna("")
    name = df["tourney_name"].astype("string").fillna("")
    reason = pd.Series(np.full(len(df), None, dtype=object), index=df.index)

    def mark(mask: pd.Series, label: str) -> None:
        mask = mask.fillna(False).astype(bool)
        reason[mask & reason.isna()] = label

    mark(stats.isna().any(axis=1), "stats_missing")
    mark((stats["w_svpt"] <= 0) | (stats["l_svpt"] <= 0), "svpt_zero")
    mark(score.str.contains(WALKOVER_RE, case=False, regex=True), "walkover")
    mark(name.str.contains(EXHIBITION_RE, case=False, regex=True), "exhibition_format")
    mark(df["winner_id"] == df["loser_id"], "same_player")
    mark((stats < 0).any(axis=1), "negative_stat")
    impossible = pd.Series(False, index=df.index)
    for s in ("w", "l"):
        svpt, first_in, first_won, second_won, ace, dfault, bp_saved, bp_faced = (
            stats[f"{s}_{c}"] for c in SERVE_COLS
        )
        impossible |= (
            (first_in > svpt) | (first_won > first_in) | (second_won > svpt - first_in)
            | (dfault > svpt - first_in) | (ace + dfault > svpt) | (bp_saved > bp_faced)
        )
    mark(impossible, "impossible_stat")
    passed = reason.isna()
    dup = pd.Series(False, index=df.index)
    dup[passed] = df.loc[passed].duplicated(DUPLICATE_KEY, keep="first")
    mark(dup, "duplicate")

    exclusions = {rule: int((reason == rule).sum()) for rule in EXCLUSION_RULES}
    valid = df[reason.isna()].copy()
    valid[STAT_COLS] = stats.loc[valid.index].astype("int64")
    valid["season"] = valid["season"].astype("int64")
    valid["tourney_date"] = pd.to_datetime(valid["tourney_date"].astype("int64").astype(str), format="%Y%m%d")
    valid["match_num"] = valid["match_num"].astype("int64")
    valid["match_id"] = valid["tourney_id"].astype(str) + "#" + valid["match_num"].astype(str)
    valid["retired"] = score.loc[valid.index].str.contains("RET", regex=False).astype(bool).to_numpy()
    valid["defaulted"] = score.loc[valid.index].str.contains("DEF", regex=False).astype(bool).to_numpy()
    valid = valid.sort_values(["tourney_date", "tourney_id", "match_num"], kind="mergesort")
    return valid.reset_index(drop=True), exclusions


def clean_players_dob(players: pd.DataFrame, valid: pd.DataFrame) -> pd.DataFrame:
    """Null any DOB that contradicts Sackmann's age column by more than a year in any match."""
    out = players.copy()
    w = valid[["winner_id", "tourney_date", "winner_age"]].rename(columns={"winner_id": "player_id", "winner_age": "csv_age"})
    l = valid[["loser_id", "tourney_date", "loser_age"]].rename(columns={"loser_id": "player_id", "loser_age": "csv_age"})
    app = pd.concat([w, l], ignore_index=True)
    app = app[app["csv_age"].notna()].join(out["dob"], on="player_id")
    app = app[app["dob"].notna()]
    age = (app["tourney_date"] - app["dob"]).dt.days / 365.25
    bad = sorted({int(p) for p in app.loc[(age - app["csv_age"]).abs() > 1.0, "player_id"]})
    out.loc[out.index.isin(bad), "dob"] = pd.NaT
    out.attrs["invalid_dob"] = bad
    return out


def usable_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibility wrapper: valid matches on the three live surfaces."""
    valid, _ = prepare_matches(df)
    return valid[valid["surface"].isin(LIVE_SURFACES)].reset_index(drop=True)


def parse_years(years: Iterable[int] | None) -> list[int] | None:
    if years is None:
        return None
    return list(years)
