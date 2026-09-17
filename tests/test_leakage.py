"""Leakage test — the first test this project must pass (design §4).

A form card for match day D may only use matches strictly before D.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from atp_sim.form_cards import Appearance, FormCardBuilder, raw_card


def _players() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dob": [
                pd.Timestamp("1990-01-01"),
                pd.Timestamp("1992-06-15"),
            ]
        },
        index=[101, 102],
    )


def _match(
    date: str,
    wid: int,
    lid: int,
    w_svpt=80,
    w_won=50,
    l_svpt=80,
    l_won=48,
) -> pd.Series:
    return pd.Series(
        {
            "tourney_date": pd.Timestamp(date),
            "winner_id": wid,
            "loser_id": lid,
            "w_svpt": w_svpt,
            "w_1stWon": w_won,
            "w_2ndWon": 0,
            "w_ace": 5,
            "w_df": 2,
            "w_bpSaved": 3,
            "w_bpFaced": 5,
            "l_svpt": l_svpt,
            "l_1stWon": l_won,
            "l_2ndWon": 0,
            "l_ace": 4,
            "l_df": 3,
            "l_bpSaved": 2,
            "l_bpFaced": 6,
        }
    )


def test_card_ignores_same_day_and_future_matches():
    builder = FormCardBuilder(_players())
    builder.observe(_match("2019-05-01", 101, 102, w_won=60, w_svpt=80))

    card_before = builder.card_for(101, pd.Timestamp("2019-06-05"))
    assert not np.isnan(card_before[0]), "should see the May match"

    builder.observe(_match("2019-07-01", 101, 102, w_won=79, w_svpt=80))
    card_after = builder.card_for(101, pd.Timestamp("2019-06-05"))
    np.testing.assert_array_equal(card_before, card_after)


def test_emit_before_observe_excludes_current_match():
    builder = FormCardBuilder(_players())
    row = _match("2019-06-05", 101, 102, w_won=70, w_svpt=80)

    card = builder.card_for(101, row["tourney_date"])
    assert np.isnan(card[0])

    builder.observe(row)
    card_next = builder.card_for(101, pd.Timestamp("2019-06-06"))
    assert not np.isnan(card_next[0])
    assert abs(card_next[0] - 70 / 80) < 1e-9


def test_raw_card_window_excludes_end_date():
    apps = [
        Appearance(
            date=pd.Timestamp("2019-06-05"),
            svpt=100,
            won=90,
            ace=10,
            df=1,
            bp_saved=1,
            bp_faced=2,
            ret_pts=100,
            ret_won=40,
            bp_conv=1,
            bp_opp=2,
        )
    ]
    card = raw_card(apps, pd.Timestamp("2019-06-05"), pd.Timestamp("1990-01-01"))
    assert np.isnan(card[0])
