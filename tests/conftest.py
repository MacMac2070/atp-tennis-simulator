"""Shared fixtures.

`synthetic` is a hand-sized archive in the raw Sackmann schema whose card values are
worked out by hand in tests/test_cards.py. `real` is the full 1991 to 2026 archive
(session-scoped) and is skipped when the data folder is absent.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

STAT = ("svpt", "1stIn", "1stWon", "2ndWon", "ace", "df", "bpSaved", "bpFaced")


def mk(
    tid, name, surface, level, date, num, wid, lid, w, l,
    score="6-4 6-4", best_of=3, rnd="R32", season=None, w_age=np.nan, l_age=np.nan,
):
    """One raw match row. `w` and `l` are 8-tuples in STAT order."""
    row = {
        "tourney_id": tid, "tourney_name": name, "surface": surface,
        "tourney_level": level, "tourney_date": int(date.replace("-", "")),
        "match_num": num, "winner_id": wid, "loser_id": lid,
        "winner_age": w_age, "loser_age": l_age, "score": score,
        "best_of": best_of, "round": rnd,
        "season": season if season is not None else int(date[:4]),
    }
    for k, v in zip(STAT, w):
        row[f"w_{k}"] = v
    for k, v in zip(STAT, l):
        row[f"l_{k}"] = v
    return row


# Stats are (svpt, 1stIn, 1stWon, 2ndWon, ace, df, bpSaved, bpFaced).
CORE_MATCHES = [
    mk("T18A", "Alpha", "Hard", "A", "2018-03-05", 1, 1, 2,
       (80, 50, 40, 15, 8, 2, 3, 5), (70, 45, 30, 12, 4, 3, 4, 8)),
    mk("T18B", "Beta", "Clay", "A", "2018-06-04", 1, 2, 1,
       (60, 40, 30, 10, 3, 1, 2, 4), (64, 40, 28, 10, 5, 4, 1, 6)),
    mk("T19A", "Alpha", "Hard", "A", "2019-03-04", 1, 1, 3,
       (90, 60, 45, 15, 10, 1, 2, 2), (85, 50, 30, 15, 2, 5, 3, 9)),
    mk("T19A", "Alpha", "Hard", "A", "2019-03-04", 2, 1, 2,
       (70, 45, 35, 12, 6, 2, 1, 3), (66, 40, 25, 13, 3, 2, 2, 7), rnd="R16"),
    mk("T19B", "Beta", "Clay", "A", "2019-06-03", 1, 3, 1,
       (75, 50, 38, 13, 4, 2, 3, 4), (72, 48, 33, 11, 6, 3, 2, 5)),
    mk("T19C", "Gamma", "Carpet", "A", "2019-09-02", 1, 2, 3,
       (50, 30, 25, 8, 2, 1, 1, 2), (55, 35, 24, 9, 3, 2, 0, 3)),
    mk("T20A", "Alpha", "Hard", "A", "2020-02-03", 1, 1, 2,
       (40, 25, 20, 7, 3, 1, 1, 1), (38, 24, 15, 6, 1, 2, 2, 4), score="6-3 2-1 RET"),
]

GOOD = (60, 40, 30, 10, 3, 1, 2, 4)

# One row per exclusion rule, all in season 2020 so they never touch the 2018/2019 cards.
INVALID_MATCHES = [
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 1, 1, 2, GOOD, GOOD, score="W/O"),
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 2, 1, 2,
       (np.nan, 40, 30, 10, 3, 1, 2, 4), GOOD),
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 3, 1, 2, (0, 0, 0, 0, 0, 0, 0, 0), GOOD),
    mk("T20N", "Next Gen Finals", "Hard", "F", "2020-11-09", 1, 1, 2, GOOD, GOOD),
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 4, 1, 1, GOOD, GOOD),
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 5, 1, 2, (60, 40, 30, 10, -1, 1, 2, 4), GOOD),
    mk("T20X", "Xi", "Hard", "A", "2020-03-02", 6, 1, 2, (60, 40, 41, 10, 3, 1, 2, 4), GOOD),
    # exact duplicate of the T20A retirement match under a new match_num
    mk("T20A", "Alpha", "Hard", "A", "2020-02-03", 9, 1, 2,
       (40, 25, 20, 7, 3, 1, 1, 1), (38, 24, 15, 6, 1, 2, 2, 4), score="6-3 2-1 RET"),
]

RAW_PLAYERS = pd.DataFrame(
    {
        "player_id": [1, 2, 3],
        "name_first": ["Ann", "Ben", "Cy"],
        "name_last": ["One", "Two", "Three"],
        "hand": ["R", "L", "R"],
        "dob": [19900101.0, 19920615.0, np.nan],
        "ioc": ["GBR", "ESP", "USA"],
        "height": [185.0, 180.0, np.nan],
        "wikidata_id": [np.nan, np.nan, np.nan],
    }
)


def raw_frame(rows):
    return pd.DataFrame(rows)


@pytest.fixture
def synthetic():
    """(valid matches, players) for the seven core matches."""
    from atp_sim.data import clean_players_dob, parse_players, prepare_matches

    valid, exclusions = prepare_matches(raw_frame(CORE_MATCHES))
    assert sum(exclusions.values()) == 0
    players = clean_players_dob(parse_players(RAW_PLAYERS.copy()), valid)
    return valid, players


@pytest.fixture(scope="session")
def real():
    """(valid, players, exclusions) for the real 1991 to 2026 archive."""
    from atp_sim.data import DATA_DIR, clean_players_dob, load_matches, load_players, prepare_matches

    if not os.path.exists(os.path.join(DATA_DIR, "atp_matches_2019.csv")):
        pytest.skip("raw archive not present; run ./fetch_data.sh")
    valid, exclusions = prepare_matches(load_matches(1991, 2026))
    players = clean_players_dob(load_players(), valid)
    return valid, players, exclusions
