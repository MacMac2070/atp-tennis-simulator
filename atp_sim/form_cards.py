"""Causal form cards: eight standardised attributes (design §4).

The one rule that cannot be broken: a card for match day D may only use
matches strictly before D.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

ATTR_NAMES = (
    "serve_strength",
    "ace_rate",
    "df_rate",
    "return_strength",
    "bp_saved",
    "bp_converted",
    "form",
    "age",
)
N_ATTRS = len(ATTR_NAMES)
WINDOW = timedelta(weeks=52)
FORM_MATCHES = 10


@dataclass
class Appearance:
    """One player's counting stats from a single past match."""

    date: pd.Timestamp
    svpt: float
    won: float
    ace: float
    df: float
    bp_saved: float
    bp_faced: float
    ret_pts: float
    ret_won: float
    bp_conv: float
    bp_opp: float


def _safe_rate(num: float, den: float) -> float | None:
    if den <= 0:
        return None
    return float(num) / float(den)


def _window_rates(apps: list[Appearance], end: pd.Timestamp) -> dict[str, float | None]:
    """Aggregate rates from appearances with date in [end - 52w, end)."""
    start = end - WINDOW
    w = [a for a in apps if start <= a.date < end]
    if not w:
        return {
            "serve_strength": None,
            "ace_rate": None,
            "df_rate": None,
            "return_strength": None,
            "bp_saved": None,
            "bp_converted": None,
        }

    svpt = sum(a.svpt for a in w)
    won = sum(a.won for a in w)
    ace = sum(a.ace for a in w)
    df = sum(a.df for a in w)
    bp_s = sum(a.bp_saved for a in w)
    bp_f = sum(a.bp_faced for a in w)
    ret_pts = sum(a.ret_pts for a in w)
    ret_won = sum(a.ret_won for a in w)
    bp_c = sum(a.bp_conv for a in w)
    bp_o = sum(a.bp_opp for a in w)

    return {
        "serve_strength": _safe_rate(won, svpt),
        "ace_rate": _safe_rate(ace, svpt),
        "df_rate": _safe_rate(df, svpt),
        "return_strength": _safe_rate(ret_won, ret_pts),
        "bp_saved": _safe_rate(bp_s, bp_f),
        "bp_converted": _safe_rate(bp_c, bp_o),
    }


def _form_delta(apps: list[Appearance], end: pd.Timestamp) -> float | None:
    """Last-10-match serve strength minus 52-week serve strength."""
    prior = [a for a in apps if a.date < end]
    if not prior:
        return None
    last10 = prior[-FORM_MATCHES:]
    short = _safe_rate(sum(a.won for a in last10), sum(a.svpt for a in last10))
    long = _window_rates(apps, end)["serve_strength"]
    if short is None or long is None:
        return None
    return short - long


def _age_years(dob: pd.Timestamp | None, on: pd.Timestamp) -> float | None:
    if dob is None or pd.isna(dob):
        return None
    return (on - dob).days / 365.25


def _side_stats(row: pd.Series, side: str) -> tuple[float, ...]:
    p = "w" if side == "winner" else "l"
    o = "l" if side == "winner" else "w"
    svpt = float(row[f"{p}_svpt"])
    won = float(row[f"{p}_1stWon"]) + float(row[f"{p}_2ndWon"])
    ace = float(row[f"{p}_ace"])
    df = float(row[f"{p}_df"])
    bp_saved = float(row[f"{p}_bpSaved"])
    bp_faced = float(row[f"{p}_bpFaced"])
    opp_svpt = float(row[f"{o}_svpt"])
    opp_won = float(row[f"{o}_1stWon"]) + float(row[f"{o}_2ndWon"])
    ret_won = opp_svpt - opp_won
    bp_conv = float(row[f"{o}_bpFaced"]) - float(row[f"{o}_bpSaved"])
    bp_opp = float(row[f"{o}_bpFaced"])
    return svpt, won, ace, df, bp_saved, bp_faced, opp_svpt, ret_won, bp_conv, bp_opp


def raw_card(
    history: list[Appearance],
    match_date: pd.Timestamp,
    dob: pd.Timestamp | None,
) -> np.ndarray:
    """Eight raw (unstandardised) attributes; NaN where unobserved."""
    rates = _window_rates(history, match_date)
    form = _form_delta(history, match_date)
    age = _age_years(dob, match_date)
    return np.array(
        [
            rates["serve_strength"],
            rates["ace_rate"],
            rates["df_rate"],
            rates["return_strength"],
            rates["bp_saved"],
            rates["bp_converted"],
            form,
            age,
        ],
        dtype=np.float64,
    )


class FormCardBuilder:
    """Stream matches in chronological order; emit cards, then append history.

    Emitting before appending is what enforces the no-leakage rule.
    """

    def __init__(self, players: pd.DataFrame):
        self.players = players
        self.history: dict[int, list[Appearance]] = defaultdict(list)

    def card_for(self, player_id: int, match_date: pd.Timestamp) -> np.ndarray:
        dob = None
        if player_id in self.players.index:
            dob = self.players.at[player_id, "dob"]
        return raw_card(self.history[int(player_id)], match_date, dob)

    def observe(self, row: pd.Series) -> None:
        date = row["tourney_date"]
        for side, pid in (("winner", int(row["winner_id"])), ("loser", int(row["loser_id"]))):
            svpt, won, ace, df, bp_s, bp_f, ret_pts, ret_won, bp_c, bp_o = _side_stats(
                row, side
            )
            self.history[pid].append(
                Appearance(
                    date=date,
                    svpt=svpt,
                    won=won,
                    ace=ace,
                    df=df,
                    bp_saved=bp_s,
                    bp_faced=bp_f,
                    ret_pts=ret_pts,
                    ret_won=ret_won,
                    bp_conv=bp_c,
                    bp_opp=bp_o,
                )
            )


def standardise(
    raw: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    """Map tour-average to 0 and one SD to 1. Missing → 0 (tour average)."""
    out = raw.copy()
    missing = np.isnan(out)
    filled = out.copy()
    filled[missing] = mean[missing]
    denom = np.where(std > 1e-8, std, 1.0)
    z = (filled - mean) / denom
    z[missing] = 0.0
    return z


def fit_standardiser(raw_cards: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    stacked = np.vstack(raw_cards)
    mean = np.nanmean(stacked, axis=0)
    std = np.nanstd(stacked, axis=0)
    mean = np.where(np.isnan(mean), 0.0, mean)
    std = np.where(np.isnan(std) | (std < 1e-8), 1.0, std)
    return mean, std
