"""Every exclusion rule, the identity merges and the DOB cleaning."""

from __future__ import annotations

import numpy as np
import pandas as pd

from atp_sim.data import ID_MERGES, clean_players_dob, parse_players, prepare_matches
from tests.conftest import CORE_MATCHES, INVALID_MATCHES, RAW_PLAYERS, mk, raw_frame


def test_each_rule_excludes_exactly_one_row():
    valid, excl = prepare_matches(raw_frame(CORE_MATCHES + INVALID_MATCHES))
    assert excl == {
        "stats_missing": 1, "svpt_zero": 1, "walkover": 1, "exhibition_format": 1,
        "same_player": 1, "negative_stat": 1, "impossible_stat": 1, "duplicate": 1,
    }
    assert len(valid) == len(CORE_MATCHES)
    assert list(excl) == ["stats_missing", "svpt_zero", "walkover", "exhibition_format",
                          "same_player", "negative_stat", "impossible_stat", "duplicate"]


def test_valid_frame_shape_and_flags():
    valid, _ = prepare_matches(raw_frame(CORE_MATCHES))
    assert str(valid["tourney_date"].dtype).startswith("datetime64")
    assert valid["match_id"].tolist()[:2] == ["T18A#1", "T18B#1"]
    ret = valid[valid["tourney_id"] == "T20A"].iloc[0]
    assert bool(ret["retired"]) and not bool(ret["defaulted"])
    assert valid["retired"].sum() == 1
    # sorted by date, event, match number
    assert valid["tourney_date"].is_monotonic_increasing
    assert valid["season"].tolist() == [2018, 2018, 2019, 2019, 2019, 2019, 2020]


def test_id_merges_applied():
    rows = [mk("Q1", "Q", "Hard", "A", "2023-01-02", 1, 211776, 2, (60, 40, 30, 10, 3, 1, 2, 4), (60, 40, 30, 10, 3, 1, 2, 4)),
            mk("Q1", "Q", "Hard", "A", "2023-01-02", 2, 3, 209870, (60, 40, 30, 10, 3, 1, 2, 4), (60, 40, 30, 10, 3, 1, 2, 4))]
    valid, _ = prepare_matches(raw_frame(rows))
    assert valid["winner_id"].tolist() == [ID_MERGES[211776], 3]
    assert valid["loser_id"].tolist() == [2, ID_MERGES[209870]]


def test_dob_parsing_and_invalid_dob_nulled():
    players = parse_players(pd.DataFrame({
        "player_id": [1, 2, 3, 4],
        "dob": [19900101.0, 19920000.0, np.nan, 19850707.0],
    }))
    assert players.loc[1, "dob"] == pd.Timestamp("1990-01-01")
    assert pd.isna(players.loc[2, "dob"])  # year-only value does not parse
    assert pd.isna(players.loc[3, "dob"])

    # player 4: Sackmann's age says 20.5 at 2019-03-04 but the DOB gives about 33.7 -> invalid
    rows = [mk("R1", "R", "Hard", "A", "2019-03-04", 1, 4, 1, (60, 40, 30, 10, 3, 1, 2, 4), (60, 40, 30, 10, 3, 1, 2, 4),
               w_age=20.5, l_age=29.2)]
    valid, _ = prepare_matches(raw_frame(rows))
    cleaned = clean_players_dob(players, valid)
    assert pd.isna(cleaned.loc[4, "dob"])
    assert cleaned.loc[1, "dob"] == pd.Timestamp("1990-01-01")  # 29.17 years: within 1 year
    assert cleaned.attrs["invalid_dob"] == [4]
