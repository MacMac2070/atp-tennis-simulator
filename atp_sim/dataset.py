"""Build the training table: one row per server per match (design §3).

Match outcomes are deliberately omitted — the model only sees service points.
"""

from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import pandas as pd
import torch

from .data import LIVE_SURFACES, load_matches, load_players, usable_matches
from .form_cards import (
    N_ATTRS,
    FormCardBuilder,
    fit_standardiser,
    standardise,
)


def _serve_row(
    server_id: int,
    returner_id: int,
    server_card: np.ndarray,
    returner_card: np.ndarray,
    surface: str,
    date: pd.Timestamp,
    svpt: float,
    won: float,
) -> dict:
    return {
        "server_id": server_id,
        "returner_id": returner_id,
        "surface": surface,
        "tourney_date": date,
        "svpt": svpt,
        "won": won,
        **{f"x_i_{k}": float(server_card[k]) for k in range(N_ATTRS)},
        **{f"x_j_{k}": float(returner_card[k]) for k in range(N_ATTRS)},
    }


def build_raw_rows(
    matches: pd.DataFrame,
    players: pd.DataFrame,
) -> tuple[pd.DataFrame, list[np.ndarray]]:
    """Chronological pass: emit two rows per match, then update histories."""
    builder = FormCardBuilder(players)
    rows: list[dict] = []
    raw_cards: list[np.ndarray] = []

    for _, row in matches.iterrows():
        date = row["tourney_date"]
        surface = row["surface"]
        wid, lid = int(row["winner_id"]), int(row["loser_id"])

        w_raw = builder.card_for(wid, date)
        l_raw = builder.card_for(lid, date)
        raw_cards.append(w_raw)
        raw_cards.append(l_raw)

        w_svpt = float(row["w_svpt"])
        w_won = float(row["w_1stWon"]) + float(row["w_2ndWon"])
        l_svpt = float(row["l_svpt"])
        l_won = float(row["l_1stWon"]) + float(row["l_2ndWon"])

        rows.append(_serve_row(wid, lid, w_raw, l_raw, surface, date, w_svpt, w_won))
        rows.append(_serve_row(lid, wid, l_raw, w_raw, surface, date, l_svpt, l_won))

        builder.observe(row)

    return pd.DataFrame(rows), raw_cards


def standardise_rows(
    raw_df: pd.DataFrame,
    raw_cards: list[np.ndarray],
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    mean, std = fit_standardiser(raw_cards)
    out = raw_df.copy()
    xi_cols = [f"x_i_{k}" for k in range(N_ATTRS)]
    xj_cols = [f"x_j_{k}" for k in range(N_ATTRS)]

    xi = out[xi_cols].to_numpy(dtype=np.float64, copy=True)
    xj = out[xj_cols].to_numpy(dtype=np.float64, copy=True)
    for i in range(len(out)):
        xi[i] = standardise(xi[i], mean, std)
        xj[i] = standardise(xj[i], mean, std)
    out[xi_cols] = xi
    out[xj_cols] = xj
    return out, mean, std


def build_training_table(
    start_year: int = 1991,
    end_year: int = 2026,
    data_dir: str | None = None,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    kwargs = {"data_dir": data_dir} if data_dir is not None else {}
    matches = usable_matches(load_matches(start_year, end_year, **kwargs))
    players = load_players(**kwargs)
    raw_df, raw_cards = build_raw_rows(matches, players)
    return standardise_rows(raw_df, raw_cards)


def save_rows(
    df: pd.DataFrame,
    mean: np.ndarray,
    std: np.ndarray,
    path: str,
) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    df.to_parquet(path, index=False)
    meta = path.replace(".parquet", "_meta.pt")
    torch.save({"card_mean": torch.tensor(mean), "card_std": torch.tensor(std)}, meta)


def load_rows(path: str) -> tuple[pd.DataFrame, torch.Tensor, torch.Tensor]:
    df = pd.read_parquet(path)
    meta = torch.load(
        path.replace(".parquet", "_meta.pt"),
        weights_only=False,
    )
    return df, meta["card_mean"], meta["card_std"]


def rows_to_tensors(
    df: pd.DataFrame,
    surfaces: Iterable[str] = LIVE_SURFACES,
) -> dict[str, dict[str, torch.Tensor]]:
    """Split the table into per-surface tensor batches."""
    out: dict[str, dict[str, torch.Tensor]] = {}
    xi_cols = [f"x_i_{k}" for k in range(N_ATTRS)]
    xj_cols = [f"x_j_{k}" for k in range(N_ATTRS)]
    for surface in surfaces:
        part = df[df["surface"] == surface]
        if part.empty:
            continue
        out[surface] = {
            "x_i": torch.tensor(part[xi_cols].to_numpy(dtype=np.float32)),
            "x_j": torch.tensor(part[xj_cols].to_numpy(dtype=np.float32)),
            "won": torch.tensor(part["won"].to_numpy(dtype=np.float32)),
            "svpt": torch.tensor(part["svpt"].to_numpy(dtype=np.float32)),
        }
    return out
