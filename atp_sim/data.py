"""Load the Sackmann archive. Read-only — never mutated by training."""

from __future__ import annotations

import os
from typing import Iterable

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "tennis_atp")

LIVE_SURFACES = ("Hard", "Clay", "Grass")
SERVE_COLS = ["svpt", "1stIn", "1stWon", "2ndWon", "ace", "df", "bpSaved", "bpFaced"]
STAT_COLS = [f"{side}_{c}" for side in ("w", "l") for c in SERVE_COLS]


def load_matches(
    start_year: int = 1991,
    end_year: int = 2026,
    data_dir: str = DATA_DIR,
) -> pd.DataFrame:
    """Load tour-level singles match files in [start_year, end_year]."""
    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        path = os.path.join(data_dir, f"atp_matches_{year}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, low_memory=False)
        df["year"] = year
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No match files in {data_dir}. Run ./fetch_data.sh first."
        )
    return pd.concat(frames, ignore_index=True)


def load_players(data_dir: str = DATA_DIR) -> pd.DataFrame:
    path = os.path.join(data_dir, "atp_players.csv")
    players = pd.read_csv(path, low_memory=False)
    players["dob"] = pd.to_datetime(
        players["dob"].astype("Int64").astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
    return players.set_index("player_id")


def usable_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Keep matches with full serve stats on a live surface; drop W/O and DEF."""
    out = df.copy()
    out["tourney_date"] = pd.to_datetime(
        out["tourney_date"].astype(str), format="%Y%m%d", errors="coerce"
    )
    score = out["score"].astype(str)
    mask = (
        out["w_svpt"].notna()
        & out["l_svpt"].notna()
        & (out["w_svpt"] > 0)
        & (out["l_svpt"] > 0)
        & out["surface"].isin(LIVE_SURFACES)
        & out["tourney_date"].notna()
        & ~score.str.contains(r"W/O|DEF", na=False, regex=True)
    )
    out = out.loc[mask].sort_values(
        ["tourney_date", "tourney_id", "match_num"], kind="mergesort"
    )
    return out.reset_index(drop=True)


def parse_years(years: Iterable[int] | None) -> list[int] | None:
    if years is None:
        return None
    return list(years)
