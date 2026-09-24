"""Draw rebuild and ranking points: a hand-made draw, the failure modes, and the real 2025 season."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from atp_sim.draws import DrawError, build_knockout, load_season_events, real_points
from atp_sim.points import PointsRuleError, category_for, loss_points, table_for


def rows(matches):
    """(round, match_num, winner_id, loser_id[, score]) tuples to raw result rows."""
    out = []
    for m in matches:
        rnd, num, w, l = m[:4]
        out.append({"round": rnd, "match_num": num, "winner_id": w, "loser_id": l,
                    "score": m[4] if len(m) > 4 else "6-4 6-4"})
    return pd.DataFrame(out)


# Six players: 1 and 2 have byes into the semi-finals.
SIX = [("QF", 1, 3, 4), ("QF", 2, 5, 6, "W/O"), ("SF", 3, 1, 3), ("SF", 4, 5, 2), ("F", 5, 1, 5)]


def test_small_draw_with_byes():
    ko = build_knockout(rows(SIX))
    pid = {int(p): i for i, p in enumerate(ko.entrants)}
    assert ko.rounds == ("QF", "SF", "F") and ko.draw_size == 6
    assert sorted(ko.entrants.tolist()) == [1, 2, 3, 4, 5, 6]
    assert {int(p) for p in ko.entrants[ko.had_bye]} == {1, 2}
    assert ko.node_round.tolist() == [0, 0, 1, 1, 2]
    # SF 1 vs 3: player 1 enters by bye, player 3 is the winner of node 0
    assert set(zip(ko.side[2].tolist(), ko.side_is_entry[2].tolist())) == {(pid[1], True), (0, False)}
    # the final is fed by the two semi-final nodes
    assert sorted(ko.side[4].tolist()) == [2, 3] and not ko.side_is_entry[4].any()
    assert ko.real_walkover.tolist() == [False, True, False, False, False]
    assert int(ko.entrants[ko.real_winner[-1]]) == 1


@pytest.mark.parametrize("bad,msg", [
    (SIX[:-1], "rounds"),                                  # no final
    ([m for m in SIX if m[:2] != ("QF", 1)], "byes"),       # a lost first-round row looks like a bye
    (SIX[:4] + [("F", 5, 1, 4)], "without winning"),         # 4 lost in the QF but plays the final
    ([("R32", 1, 1, 2)] + SIX, "rounds"),                   # a gap: R32 then QF
])
def test_broken_draws_raise(bad, msg):
    with pytest.raises(DrawError, match=msg):
        build_knockout(rows(bad))


def test_player_cannot_enter_twice():
    bad = [("QF", 1, 1, 2), ("QF", 2, 3, 1), ("SF", 3, 1, 3), ("SF", 4, 5, 6), ("F", 5, 1, 5)]
    with pytest.raises(DrawError):
        build_knockout(rows(bad))


@pytest.mark.parametrize("bad,msg", [
    # player 1 wins one semi-final and loses the other: one QF node would feed two SFs
    ([("QF", 1, 1, 2), ("QF", 2, 3, 4), ("SF", 3, 1, 3), ("SF", 4, 5, 1), ("F", 5, 5, 1)], "two SF"),
    # a "bye" straight into the final of a two-round draw
    ([("SF", 1, 1, 2), ("F", 2, 1, 3)], "without winning"),
    # two bye players meeting in their first match
    ([("QF", 1, 1, 2), ("QF", 2, 3, 4), ("SF", 3, 1, 3), ("SF", 4, 5, 6), ("F", 5, 1, 5)], "two byes"),
])
def test_impossible_draw_shapes_raise(bad, msg):
    with pytest.raises(DrawError, match=msg):
        build_knockout(rows(bad))


def test_one_missing_first_round_result_is_caught():
    """28-draw with one R32 row lost: its winner would pass for a fifth bye, size 27."""
    from test_season import full_draw  # the same generator the season tests use

    full = full_draw(28, byes=4)
    lost = full[(full["round"] == "R32") & (full["winner_id"] == 13)].index
    with pytest.raises(DrawError, match="odd draw size"):
        build_knockout(full.drop(lost))


def test_points_rules():
    m96 = table_for("M", 96)
    r96 = ("R128", "R64", "R32", "R16", "QF", "SF", "F")
    assert loss_points(m96, r96, "R64", had_bye=False) == 30
    assert loss_points(m96, r96, "R64", had_bye=True) == 10  # bye then loss = first-round points
    assert loss_points(m96, r96, "R32", had_bye=True) == 50  # a bye only matters in round two
    r28 = ("R32", "R16", "QF", "SF", "F")
    assert loss_points(table_for("250", 28), r28, "R16", had_bye=True) == 0
    assert loss_points(table_for("250", 28), r28, "R16", had_bye=False) == 25
    assert category_for("A", "Dallas", 2025) == "500"
    assert category_for("A", "Dallas", 2024) == "250"
    assert category_for("A", "Rio De Janeiro", 2024) == "500"  # name case differs by year
    with pytest.raises(PointsRuleError):
        category_for("D", "Davis Cup", 2025)
    with pytest.raises(PointsRuleError):
        table_for("500", 64)
    with pytest.raises(PointsRuleError):
        category_for("A", "Anywhere", 2019)


@pytest.fixture(scope="module")
def season_2025():
    from atp_sim.data import DATA_DIR

    if not os.path.exists(os.path.join(DATA_DIR, "atp_matches_2025.csv")):
        pytest.skip("raw archive not present; run ./fetch_data.sh")
    return load_season_events(2025)


def test_every_2025_draw_rebuilds(season_2025):
    events, excluded = season_2025
    assert len(events) == 60
    counts = pd.Series([e.category for e in events]).value_counts().to_dict()
    assert counts == {"250": 30, "500": 16, "M": 9, "G": 4, "F": 1}
    for e in events:
        if e.knockout is None:
            continue
        # in 2025 the csv's draw size is right, so it cross-checks the rebuild
        assert e.draw_size == int(e.matches["draw_size"].iloc[0]), e.name
        assert len(e.knockout.node_round) == len(e.matches), e.name  # every result is a node
    assert set(excluded["reason"]) == {"team event", "team or exhibition format"}
    assert {"United Cup", "Laver Cup", "Next Gen Finals"} <= set(excluded["name"])


def test_finals_groups(season_2025):
    fin = [e for e in season_2025[0] if e.finals is not None]
    assert len(fin) == 1
    f = fin[0].finals
    assert np.bincount(f.group).tolist() == [4, 4]
    assert all(f.group[a] == f.group[b] for a, b in f.rr_pairs)


def test_real_2025_totals_match_the_official_top_two(season_2025):
    """Same table, real results: Alcaraz and Sinner land on their official year-end points."""
    total: dict[int, int] = {}
    for e in season_2025[0]:
        for p, v in real_points(e).items():
            total[p] = total.get(p, 0) + v
    assert total[207989] == 12050  # Alcaraz, official 2025-12-29
    assert total[206173] == 11500  # Sinner


def test_points_enter_on_the_monday_after(season_2025):
    by_name = {e.name: e for e in season_2025[0]}
    assert by_name["Australian Open"].points_entry_date == pd.Timestamp("2025-01-27")
    assert by_name["Indian Wells Masters"].points_entry_date == pd.Timestamp("2025-03-17")
    assert by_name["Rotterdam"].points_entry_date == pd.Timestamp("2025-02-10")
    assert by_name["Tour Finals"].points_entry_date == pd.Timestamp("2025-11-17")
