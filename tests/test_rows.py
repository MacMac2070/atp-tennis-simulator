"""The training table itself: schema, ordering, symmetry, no leaked result."""

from __future__ import annotations

import re


from atp_sim.data import LIVE_SURFACES
from atp_sim.dataset import FORBIDDEN_RE, ROW_COLUMNS, build_rows, rows_to_tensors
from atp_sim.form_cards import build_cards


def _rows(synthetic):
    valid, players = synthetic
    cards, constants = build_cards(valid, players)
    return build_rows(valid, cards, constants), valid


def test_row_schema_and_no_result_columns(synthetic):
    rows, _ = _rows(synthetic)
    assert list(rows.columns) == ROW_COLUMNS
    assert not any(re.search(FORBIDDEN_RE, c) for c in rows.columns)
    assert rows[[f"x_i_{k}" for k in range(8)] + [f"x_j_{k}" for k in range(8)]].notna().all().all()
    assert str(rows["tourney_date"].dtype).startswith("datetime64")


def test_rows_two_per_match_swapped_and_ordered(synthetic):
    rows, valid = _rows(synthetic)
    # seasons with constants: 2019, 2020; live surfaces only -> M3, M4, M5, M7 (not the carpet M6)
    assert len(rows) == 8
    assert rows["match_id"].tolist() == ["T19A#1", "T19A#1", "T19A#2", "T19A#2", "T19B#1", "T19B#1", "T20A#1", "T20A#1"]
    assert rows["server_id"].tolist() == [1, 3, 1, 2, 1, 3, 1, 2]  # by server_id, never winner-first
    assert rows["returner_id"].tolist() == [3, 1, 2, 1, 3, 1, 2, 1]
    for mid, g in rows.groupby("match_id"):
        assert set(g["server_id"]) == set(g["returner_id"])
    m5 = rows[rows["match_id"] == "T19B#1"].set_index("server_id")
    assert (m5.loc[3, "svpt"], m5.loc[3, "won"]) == (75, 38 + 13)
    assert (m5.loc[1, "svpt"], m5.loc[1, "won"]) == (72, 33 + 11)
    assert rows[rows["match_id"] == "T20A#1"]["retired"].all()
    assert not rows["defaulted"].any()
    assert rows["season"].tolist() == [2019] * 6 + [2020] * 2


def test_row_cards_match_card_table(synthetic):
    valid, players = synthetic
    cards, constants = build_cards(valid, players)
    rows = build_rows(valid, cards, constants)
    c = cards.set_index(["player_id", "tourney_date"])
    for _, r in rows.iterrows():
        for k in range(8):
            assert r[f"x_i_{k}"] == c.loc[(r["server_id"], r["tourney_date"]), f"x_{k}"]
            assert r[f"x_j_{k}"] == c.loc[(r["returner_id"], r["tourney_date"]), f"x_{k}"]
        assert r["i_n_52w"] == c.loc[(r["server_id"], r["tourney_date"]), "n_52w"]


def test_rows_to_tensors_contract(synthetic):
    rows, _ = _rows(synthetic)
    batches = rows_to_tensors(rows)
    assert set(batches) == {"Hard", "Clay"}
    assert batches["Hard"]["x_i"].shape == (6, 8)
    assert float(batches["Clay"]["svpt"].sum()) == 75 + 72


def test_row_count_equals_2x_valid_in_scope_real(real):
    valid, players, _ = real
    cards, constants = build_cards(valid, players)
    rows = build_rows(valid, cards, constants)
    inscope = valid[(valid["season"] >= 1992) & valid["surface"].isin(LIVE_SURFACES)]
    assert len(rows) == 2 * len(inscope)
    assert rows["season"].min() == 1992
    assert set(rows["surface"]) == set(LIVE_SURFACES)
    assert rows[[f"x_i_{k}" for k in range(8)]].notna().all().all()
    assert (rows["won"] <= rows["svpt"]).all()
    assert rows.groupby("match_id").size().eq(2).all()
