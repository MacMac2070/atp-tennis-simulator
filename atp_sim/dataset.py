"""The training table: one row per server per match (design section 3, VERIFY_SPEC 10, 11).

Match outcomes are deliberately omitted. The two rows of a match are ordered by
server id, never winner first, so row order cannot leak the result either.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd
import torch

from .data import (
    DATA_DIR, EXCLUSION_RULES, ID_MERGES, LIVE_SURFACES,
    clean_players_dob, load_matches, load_players, prepare_matches,
)
from .form_cards import (
    ATTR_NAMES, EPOCH, KEY_SCALE, N_ATTRS, RATES, STD_ATTRS, WINDOW_DAYS,
    build_cards, build_log, standardise,
)

X_I = [f"x_i_{k}" for k in range(N_ATTRS)]
X_J = [f"x_j_{k}" for k in range(N_ATTRS)]
ROW_COLUMNS = (
    ["match_id", "tourney_id", "tourney_date", "season", "tourney_level", "surface", "round",
     "best_of", "server_id", "returner_id"]
    + X_I + X_J
    + ["svpt", "won", "retired", "defaulted", "i_n_52w", "i_n_10", "j_n_52w", "j_n_10",
       "i_dob_missing", "j_dob_missing"]
)
FORBIDDEN_RE = r"win|los|score|rank|minutes|name|seed"
ROW_DTYPES = {
    "season": "int16", "best_of": "int8", "server_id": "int32", "returner_id": "int32",
    "svpt": "int16", "won": "int16", "i_n_52w": "int16", "i_n_10": "int8",
    "j_n_52w": "int16", "j_n_10": "int8",
}


def build_rows(valid: pd.DataFrame, cards: pd.DataFrame, constants: pd.DataFrame) -> pd.DataFrame:
    """Two rows per valid live-surface match of every season that has constants."""
    seasons = set(constants["season"].astype(int))
    m = valid[valid["season"].isin(seasons) & valid["surface"].isin(LIVE_SURFACES)]
    base = ["match_id", "tourney_id", "tourney_date", "season", "tourney_level", "surface",
            "round", "best_of", "match_num", "retired", "defaulted"]

    def side(p: str, sid: str, rid: str) -> pd.DataFrame:
        r = m[base].copy()
        r["server_id"] = m[sid].to_numpy(np.int64)
        r["returner_id"] = m[rid].to_numpy(np.int64)
        r["svpt"] = m[f"{p}_svpt"].to_numpy(np.int64)
        r["won"] = (m[f"{p}_1stWon"] + m[f"{p}_2ndWon"]).to_numpy(np.int64)
        return r

    rows = pd.concat([side("w", "winner_id", "loser_id"), side("l", "loser_id", "winner_id")], ignore_index=True)
    xcols = [f"x_{k}" for k in range(N_ATTRS)]
    card_i = cards[["player_id", "tourney_date"] + xcols + ["n_52w", "n_10", "dob_missing"]].rename(
        columns={**{f"x_{k}": f"x_i_{k}" for k in range(N_ATTRS)},
                 "n_52w": "i_n_52w", "n_10": "i_n_10", "dob_missing": "i_dob_missing", "player_id": "server_id"}
    )
    card_j = cards[["player_id", "tourney_date"] + xcols + ["n_52w", "n_10", "dob_missing"]].rename(
        columns={**{f"x_{k}": f"x_j_{k}" for k in range(N_ATTRS)},
                 "n_52w": "j_n_52w", "n_10": "j_n_10", "dob_missing": "j_dob_missing", "player_id": "returner_id"}
    )
    rows = rows.merge(card_i, on=["server_id", "tourney_date"], how="left", validate="many_to_one")
    rows = rows.merge(card_j, on=["returner_id", "tourney_date"], how="left", validate="many_to_one")
    if rows[X_I + X_J].isna().any().any():
        raise AssertionError("a row is missing its card; every server must have a card at its date")
    rows = rows.sort_values(["tourney_date", "tourney_id", "match_num", "server_id"], kind="mergesort")
    rows = rows[ROW_COLUMNS].reset_index(drop=True)
    for c, dt in ROW_DTYPES.items():
        rows[c] = rows[c].astype(dt)
    for c in ("retired", "defaulted", "i_dob_missing", "j_dob_missing"):
        rows[c] = rows[c].astype(bool)
    return rows


@dataclass
class BuildResult:
    rows: pd.DataFrame
    cards: pd.DataFrame
    constants: pd.DataFrame
    exclusions: dict[str, int]
    invalid_dob: list[int]
    invalid_dob_names: dict[int, str]
    n_loaded: int
    boundary_hits: int
    seasons: pd.DataFrame
    elapsed: float = 0.0
    start_year: int = 1991
    end_year: int = 2026
    players_missing_dob: int = 0


def _boundary_hits(valid: pd.DataFrame, cards: pd.DataFrame) -> int:
    """Cards that have an appearance exactly WINDOW_DAYS before their date (the inclusive bound)."""
    log = build_log(valid)
    key_arr = log["player_id"].to_numpy(np.int64) * KEY_SCALE + log["day"].to_numpy(np.int64)
    pid = cards["player_id"].to_numpy(np.int64)
    day = (cards["tourney_date"] - EPOCH).dt.days.to_numpy(np.int64)
    probe = pid * KEY_SCALE + np.maximum(day - WINDOW_DAYS, 0)
    left = np.searchsorted(key_arr, probe, side="left")
    right = np.searchsorted(key_arr, probe, side="right")
    return int((right > left).sum())


def build_all(start_year: int = 1991, end_year: int = 2026, data_dir: str | None = None) -> BuildResult:
    t0 = time.time()
    kwargs = {"data_dir": data_dir} if data_dir is not None else {}
    raw = load_matches(start_year, end_year, **kwargs)
    valid, exclusions = prepare_matches(raw)
    players = clean_players_dob(load_players(**kwargs), valid)
    cards, constants = build_cards(valid, players)
    rows = build_rows(valid, cards, constants)

    inscope = valid[valid["surface"].isin(LIVE_SURFACES)]
    seasons = pd.DataFrame(
        {
            "matches_loaded": raw.groupby("season").size(),
            "valid": valid.groupby("season").size(),
            "valid_live_surface": inscope.groupby("season").size(),
            "rows": rows.groupby("season").size(),
            "cards": cards.groupby("season").size(),
        }
    ).fillna(0).astype(int)
    names = {}
    for pid in players.attrs.get("invalid_dob", []):
        if pid in players.index and "name_first" in players.columns:
            names[pid] = f"{players.loc[pid, 'name_first']} {players.loc[pid, 'name_last']}"
    seen = pd.concat([valid["winner_id"], valid["loser_id"]]).unique()
    missing_dob = int(players["dob"].reindex(seen).isna().sum())
    return BuildResult(
        rows=rows, cards=cards, constants=constants, exclusions=exclusions,
        invalid_dob=list(players.attrs.get("invalid_dob", [])), invalid_dob_names=names,
        n_loaded=len(raw), boundary_hits=_boundary_hits(valid, cards), seasons=seasons,
        elapsed=time.time() - t0, start_year=start_year, end_year=end_year,
        players_missing_dob=missing_dob,
    )


def final_constants(constants: pd.DataFrame, season: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """mu and sigma vectors (x order) of `season`, or of the latest season that has constants."""
    last = int(constants["season"].max()) if season is None else int(season)
    k = constants[constants["season"] == last].set_index("attr")
    if k.empty:
        raise ValueError(f"no standardising constants for season {last}")
    mean = np.array([k.loc[attr, "mu"] for attr, _ in STD_ATTRS], dtype=np.float64)
    std = np.array([k.loc[attr, "sigma"] for attr, _ in STD_ATTRS], dtype=np.float64)
    return mean, std


def build_training_table(
    start_year: int = 1991,
    end_year: int = 2026,
    data_dir: str | None = None,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Compatibility entry point: (rows, mean, std) with mean/std the latest season's constants."""
    result = build_all(start_year, end_year, data_dir)
    mean, std = final_constants(result.constants)
    return result.rows, mean, std


def write_report(result: BuildResult, path: str) -> None:
    c = result.constants
    lines = [
        "# Training table build report", "",
        f"Seasons loaded: {result.start_year} to {result.end_year}. Elapsed {result.elapsed:.1f} s.", "",
        f"Matches loaded: {result.n_loaded:,}. Valid: {int(result.seasons['valid'].sum()):,}. "
        f"Rows: {len(result.rows):,}. Cards: {len(result.cards):,}.", "",
        "## Exclusions (first failing rule wins, VERIFY_SPEC section 3)", "",
        "| rule | matches |", "|---|---:|",
    ]
    lines += [f"| {rule} | {result.exclusions[rule]:,} |" for rule in EXCLUSION_RULES]
    lines += ["", "## Identity merges", "", "| old id | kept id |", "|---|---|"]
    lines += [f"| {o} | {n} |" for o, n in ID_MERGES.items()]
    lines += ["", "## Dates of birth", "",
              f"Players in valid matches without a usable DOB: {result.players_missing_dob}.",
              f"DOBs nulled because they contradict Sackmann's age column by more than a year: {result.invalid_dob}"
              + (f" ({', '.join(f'{k}: {v}' for k, v in result.invalid_dob_names.items())})" if result.invalid_dob_names else ""),
              "", f"Cards with an appearance exactly {WINDOW_DAYS} days before their date (inclusive bound): {result.boundary_hits:,}.",
              "", "## Per season", "", "| season | loaded | valid | valid live surface | rows | cards |", "|---|---:|---:|---:|---:|---:|"]
    for s, r in result.seasons.iterrows():
        lines.append(f"| {s} | {r['matches_loaded']:,} | {r['valid']:,} | {r['valid_live_surface']:,} | {r['rows']:,} | {r['cards']:,} |")
    lines += ["", "## Constants (from the previous season's row population)", "",
              "| season | n_pop | serve m_prior | serve mu | serve sigma | ret mu | ret sigma | form sigma | age mu | age sigma | no-history x_serve |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in sorted(c["season"].unique()):
        k = c[c["season"] == s].set_index("attr")
        nohist = (k.loc["serve", "m_prior"] - k.loc["serve", "mu"]) / k.loc["serve", "sigma"] if k.loc["serve", "sigma"] > 0 else 0.0
        lines.append(
            f"| {s} | {int(k.loc['serve', 'n_pop']):,} | {k.loc['serve', 'm_prior']:.4f} | {k.loc['serve', 'mu']:.4f} | "
            f"{k.loc['serve', 'sigma']:.4f} | {k.loc['ret', 'mu']:.4f} | {k.loc['ret', 'sigma']:.4f} | {k.loc['form', 'sigma']:.4f} | "
            f"{k.loc['age', 'mu']:.2f} | {k.loc['age', 'sigma']:.2f} | {nohist:+.3f} |"
        )
    lines += ["", "The full table is in constants.csv. The x vector order is: " + ", ".join(ATTR_NAMES) + ".", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def save_build(result: BuildResult, out_dir: str) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "rows": os.path.join(out_dir, "rows.parquet"),
        "cards": os.path.join(out_dir, "cards.parquet"),
        "constants": os.path.join(out_dir, "constants.csv"),
        "report": os.path.join(out_dir, "build_report.md"),
    }
    mean, std = final_constants(result.constants)
    save_rows(result.rows, mean, std, paths["rows"], constants=result.constants)
    cards = result.cards.copy()
    cards["player_id"] = cards["player_id"].astype("int32")
    cards["season"] = cards["season"].astype("int16")
    cards.to_parquet(paths["cards"], index=False)
    result.constants.to_csv(paths["constants"], index=False)
    write_report(result, paths["report"])
    return paths


def save_rows(
    df: pd.DataFrame,
    mean: np.ndarray,
    std: np.ndarray,
    path: str,
    constants: pd.DataFrame | None = None,
) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    df.to_parquet(path, index=False)
    meta = {
        "card_mean": torch.tensor(np.asarray(mean, dtype=np.float64)),
        "card_std": torch.tensor(np.asarray(std, dtype=np.float64)),
        "attr_names": list(ATTR_NAMES),
        "note": "card_mean/card_std are the latest season's mu/sigma; constants holds every season",
    }
    if constants is not None:
        meta["constants"] = constants.to_dict(orient="list")
    torch.save(meta, path.replace(".parquet", "_meta.pt"))


def load_rows(path: str) -> tuple[pd.DataFrame, torch.Tensor, torch.Tensor]:
    df = pd.read_parquet(path)
    meta = torch.load(path.replace(".parquet", "_meta.pt"), weights_only=False)
    return df, meta["card_mean"], meta["card_std"]


def load_constants(path: str, season: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Card mu and sigma for `season`. Season Y's constants come from the population of Y-1,
    so a model fitted through T must carry season T+1's, never a later season's."""
    meta = torch.load(path.replace(".parquet", "_meta.pt"), weights_only=False)
    if "constants" not in meta:
        raise ValueError("rows meta has no per-season constants; rebuild the table")
    mean, std = final_constants(pd.DataFrame(meta["constants"]), season)
    return torch.tensor(mean), torch.tensor(std)


def rows_after(df: pd.DataFrame, last_season: int) -> pd.DataFrame:
    """Held-out rows: seasons strictly after last_season. May be empty."""
    if "season" not in df.columns:
        raise ValueError("rows have no season column, cannot split chronologically")
    return df[df["season"] > last_season]


def rows_through(df: pd.DataFrame, last_season: int) -> pd.DataFrame:
    """Rows of seasons up to and including last_season (design section 9: splits are chronological)."""
    if "season" not in df.columns:
        raise ValueError("rows have no season column, cannot split chronologically")
    part = df[df["season"] <= last_season]
    if part.empty:
        raise ValueError(f"no rows at or before season {last_season}")
    return part


def rows_to_tensors(
    df: pd.DataFrame,
    surfaces: Iterable[str] = LIVE_SURFACES,
) -> dict[str, dict[str, torch.Tensor]]:
    """Split the table into per-surface tensor batches."""
    out: dict[str, dict[str, torch.Tensor]] = {}
    for surface in surfaces:
        part = df[df["surface"] == surface]
        if part.empty:
            continue
        out[surface] = {
            "x_i": torch.tensor(part[X_I].to_numpy(dtype=np.float32)),
            "x_j": torch.tensor(part[X_J].to_numpy(dtype=np.float32)),
            "won": torch.tensor(part["won"].to_numpy(dtype=np.float32)),
            "svpt": torch.tensor(part["svpt"].to_numpy(dtype=np.float32)),
            "season": torch.tensor(part["season"].to_numpy(dtype=np.int64)),
        }
    return out
