"""Leakage tests: the first tests this project must pass (DESIGN.md §4).

A card for date D may only use matches strictly before D. Deleting every match dated
D or later from the archive must leave the card, its shrunk rates and its x values
byte-identical.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from atp_sim.data import LIVE_SURFACES, clean_players_dob, parse_players, prepare_matches
from atp_sim.form_cards import build_cards
from tests.conftest import CORE_MATCHES, RAW_PLAYERS, mk, raw_frame

CARD_VALUE_COLS = [
    "n_52w", "n_10", "svpt_52", "svwon_52", "ace_52", "df_52", "bpf_52", "bps_52",
    "rpt_52", "rwon_52", "obpf_52", "obps_52", "svpt_10", "svwon_10",
    "shr_serve", "shr_ace", "shr_df", "shr_ret", "shr_bps", "shr_bpc", "form", "age",
] + [f"x_{k}" for k in range(8)]


def _card(cards, pid, date):
    sel = cards[(cards["player_id"] == pid) & (cards["tourney_date"] == pd.Timestamp(date))]
    assert len(sel) == 1
    return sel.iloc[0]


def test_leakage_delete_future_synthetic(synthetic):
    valid, players = synthetic
    D = pd.Timestamp("2019-06-03")
    keys = pd.DataFrame({"player_id": [1], "tourney_date": [D], "season": [2019]})

    full, _ = build_cards(valid, players, keys=keys)
    trunc, _ = build_cards(valid[valid["tourney_date"] < D], players, keys=keys)

    pd.testing.assert_frame_equal(
        full[CARD_VALUE_COLS].reset_index(drop=True),
        trunc[CARD_VALUE_COLS].reset_index(drop=True),
    )
    # window [2018-06-04, 2019-06-03): M2 on 2018-06-04 (inclusive bound), M3 and M4 on 2019-03-04
    assert full.iloc[0]["n_52w"] == 3


def test_future_match_added_changes_nothing(synthetic):
    valid, players = synthetic
    D = pd.Timestamp("2019-03-04")
    keys = pd.DataFrame({"player_id": [1], "tourney_date": [D], "season": [2019]})
    before, _ = build_cards(valid, players, keys=keys)

    extra = mk("T19Z", "Zeta", "Hard", "A", "2019-12-02", 1, 1, 2,
               (99, 70, 69, 29, 40, 0, 9, 9), (30, 20, 5, 2, 0, 9, 0, 9))
    valid2, excl = prepare_matches(raw_frame(CORE_MATCHES + [extra]))
    assert sum(excl.values()) == 0
    after, _ = build_cards(valid2, players, keys=keys)

    pd.testing.assert_frame_equal(
        before[CARD_VALUE_COLS].reset_index(drop=True),
        after[CARD_VALUE_COLS].reset_index(drop=True),
    )


def test_same_day_never_contributes(synthetic):
    """Player 1 plays twice on 2019-03-04; neither match may feed that day's card."""
    valid, players = synthetic
    cards, _ = build_cards(valid, players)
    c = _card(cards, 1, "2019-03-04")
    assert c["n_52w"] == 2  # only the two 2018 matches
    assert c["svpt_52"] == 80 + 64


def test_two_events_same_date_no_history():
    """A player whose first ever matches are two events on one date has an empty card."""
    rows = [
        mk("E1", "One", "Hard", "A", "2019-03-04", 1, 7, 8, (60, 40, 30, 10, 3, 1, 2, 4), (60, 40, 30, 10, 3, 1, 2, 4)),
        mk("E2", "Two", "Clay", "D", "2019-03-04", 1, 7, 9, (60, 40, 30, 10, 3, 1, 2, 4), (60, 40, 30, 10, 3, 1, 2, 4)),
    ]
    valid, _ = prepare_matches(raw_frame(rows))
    players = parse_players(pd.DataFrame({"player_id": [7, 8, 9], "dob": [np.nan] * 3}))
    cards, _ = build_cards(valid, players)
    c = _card(cards, 7, "2019-03-04")
    assert c["n_52w"] == 0 and c["n_10"] == 0 and c["svpt_52"] == 0
    assert len(cards[cards["player_id"] == 7]) == 1  # one card per player-date, shared by both events


def test_window_boundary():
    """D-364 is in, D-365 is out, D-1 is in, D and D+1 are out."""
    stats = (60, 40, 30, 10, 3, 1, 2, 4)
    rows = [
        mk("B0", "B", "Hard", "A", "2018-03-04", 1, 5, 6, (100, 60, 50, 20, 1, 1, 1, 1), stats),  # D-365
        mk("B1", "B", "Hard", "A", "2018-03-05", 1, 5, 6, (200, 120, 100, 40, 2, 2, 2, 2), stats),  # D-364
        mk("B2", "B", "Hard", "A", "2019-03-03", 1, 5, 6, (300, 180, 150, 60, 3, 3, 3, 3), stats),  # D-1
        mk("B3", "B", "Hard", "A", "2019-03-04", 1, 5, 6, (400, 240, 200, 80, 4, 4, 4, 4), stats),  # D
        mk("B4", "B", "Hard", "A", "2019-03-05", 1, 5, 6, (500, 300, 250, 100, 5, 5, 5, 5), stats),  # D+1
    ]
    valid, _ = prepare_matches(raw_frame(rows))
    players = parse_players(pd.DataFrame({"player_id": [5, 6], "dob": [np.nan, np.nan]}))
    keys = pd.DataFrame({"player_id": [5], "tourney_date": [pd.Timestamp("2019-03-04")], "season": [2019]})
    cards, _ = build_cards(valid, players, keys=keys)
    c = cards.iloc[0]
    assert c["n_52w"] == 2
    assert c["svpt_52"] == 200 + 300
    assert c["ace_52"] == 2 + 3


def test_leakage_delete_future_real(real):
    valid, players, _ = real
    inscope = valid[(valid["season"] >= 1992) & valid["surface"].isin(LIVE_SURFACES)]
    rng = np.random.default_rng(20260917)
    picks = rng.choice(len(inscope), size=20, replace=False)
    keys = pd.DataFrame(
        {
            "player_id": [int(inscope.iloc[i]["winner_id"] if k % 2 else inscope.iloc[i]["loser_id"]) for k, i in enumerate(picks)],
            "tourney_date": [inscope.iloc[i]["tourney_date"] for i in picks],
            "season": [int(inscope.iloc[i]["season"]) for i in picks],
        }
    )
    full, _ = build_cards(valid, players, keys=keys)
    full = full.set_index(["player_id", "tourney_date"])
    assert full[[f"x_{k}" for k in range(8)]].notna().all().all()
    for _, key in keys.iterrows():
        D = key["tourney_date"]
        one = key.to_frame().T.astype({"player_id": int, "season": int})
        trunc, _ = build_cards(valid[valid["tourney_date"] < D], players, keys=one)
        got = trunc.set_index(["player_id", "tourney_date"]).loc[(int(key["player_id"]), D), CARD_VALUE_COLS]
        exp = full.loc[(int(key["player_id"]), D), CARD_VALUE_COLS]
        pd.testing.assert_series_equal(got, exp, check_names=False)
