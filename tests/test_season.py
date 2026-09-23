"""Season loop: title odds, points, common random numbers, ATP Finals rules, the ledger."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from atp_sim.draws import ROUNDS, Event, build_knockout, build_round_robin, load_season_events
from atp_sim.season import (
    PreparedEvent, _break_tie, competition_ranks, entrant_cards, ledger_at, simulate_season,
)


def full_draw(n: int, byes: int = 0) -> pd.DataFrame:
    """Results of an n-draw where the lower id always wins.

    Players 1..byes skip round one and each meets a first-round winner in round two, as in
    a real ATP draw.
    """
    rounds = ROUNDS[-math.ceil(math.log2(n)):]
    alive = list(range(byes + 1, n + 1))
    out, num = [], 0
    for ri, rnd in enumerate(rounds):
        if ri == 1 and byes:
            alive = [p for pair in zip(range(1, byes + 1), alive[:byes]) for p in pair] + alive[byes:]
        nxt = []
        for a, b in zip(alive[0::2], alive[1::2]):
            num += 1
            out.append({"round": rnd, "match_num": num, "winner_id": min(a, b), "loser_id": max(a, b),
                        "score": "6-4 6-4"})
            nxt.append(min(a, b))
        alive = nxt
    return pd.DataFrame(out)


def knockout_event(rows: pd.DataFrame, index: int = 0, category: str = "250") -> Event:
    ko = build_knockout(rows)
    ev = Event(index=index, tourney_id=f"T{index}", name=f"Test {index}", level="A", surface="Hard",
               date=pd.Timestamp("2025-03-03"), season=2025, category=category, draw_size=ko.draw_size,
               best_of=3, final_tb=7, matches=rows, knockout=ko)
    ev.entry_rank = np.arange(1, len(ko.entrants) + 1)
    return ev


def prepared(ev: Event, pm: np.ndarray, pset: np.ndarray | None = None) -> PreparedEvent:
    e = len(ev.entrants)
    return PreparedEvent(event=ev, player_idx=np.arange(e), cards=np.zeros((e, 8)),
                         p_serve=np.full((e, e), 0.6), p_match=pm, p_set=pset)


def test_helper_draws_rebuild():
    assert knockout_event(full_draw(32)).draw_size == 32
    ev = knockout_event(full_draw(28, byes=4))
    assert ev.draw_size == 28 and ev.knockout.had_bye.sum() == 4


def test_title_odds_match_the_hand_calculation():
    """One player beats everyone 90% of the time, the rest are even: title chance 0.9^5."""
    ev = knockout_event(full_draw(32))
    pm = np.full((32, 32), 0.5)
    star = int(np.flatnonzero(ev.entrants == 17)[0])
    pm[star, :], pm[:, star] = 0.9, 0.1
    sims = simulate_season([prepared(ev, pm)], ev.entrants, 20_000, seed=1)
    assert (sims.champions[0] == star).mean() == pytest.approx(0.9**5, abs=0.015)


def test_points_per_round_in_a_32_draw():
    ev = knockout_event(full_draw(32))
    sims = simulate_season([prepared(ev, np.full((32, 32), 0.5))], ev.entrants, 500, seed=2)
    expected = sorted([250, 165] + [100] * 2 + [50] * 4 + [25] * 8 + [0] * 16)
    for row in sims.event_points[0]:
        assert sorted(row.tolist()) == expected


def test_bye_then_loss_scores_first_round_points():
    """28-draw 250: the four bye players always lose their first match and score 0, not 25."""
    ev = knockout_event(full_draw(28, byes=4))
    bye = ev.knockout.had_bye
    pm = np.full((28, 28), 0.5)
    pm[bye, :], pm[:, bye] = 0.0, 1.0
    sims = simulate_season([prepared(ev, pm)], ev.entrants, 300, seed=3)
    pts = sims.event_points[0]
    assert (pts[:, bye] == 0).all()
    assert (pts.max(axis=1) == 250).all()
    # the four R16 matches without a bye player pay their four losers the normal 25
    assert ((pts[:, ~bye] == 25).sum(axis=1) == 4).all()


def test_common_random_numbers():
    a = knockout_event(full_draw(32), index=0)
    b = knockout_event(full_draw(32), index=1)
    base = np.full((32, 32), 0.5)
    run1 = simulate_season([prepared(a, base), prepared(b, base)], a.entrants, 400, seed=9)
    again = simulate_season([prepared(a, base), prepared(b, base)], a.entrants, 400, seed=9)
    changed = base.copy()
    changed[0, :], changed[:, 0] = 0.8, 0.2
    run2 = simulate_season([prepared(a, changed), prepared(b, base)], a.entrants, 400, seed=9)
    other_seed = simulate_season([prepared(a, base), prepared(b, base)], a.entrants, 400, seed=10)
    assert np.array_equal(run1.totals, again.totals)
    # a different model at event 0 leaves event 1's coins, and so its results, untouched
    assert np.array_equal(run1.event_points[1], run2.event_points[1])
    assert not np.array_equal(run1.event_points[0], run2.event_points[0])
    assert not np.array_equal(run1.totals, other_seed.totals)


def finals_rows() -> pd.DataFrame:
    rr, num = [], 0
    for group in ((1, 2, 3, 4), (5, 6, 7, 8)):
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                num += 1
                rr.append({"round": "RR", "match_num": num, "winner_id": a, "loser_id": b, "score": "6-4 6-4"})
    rr += [{"round": "SF", "match_num": 13, "winner_id": 1, "loser_id": 6, "score": "6-4 6-4"},
           {"round": "SF", "match_num": 14, "winner_id": 5, "loser_id": 2, "score": "6-4 6-4"},
           {"round": "F", "match_num": 15, "winner_id": 1, "loser_id": 5, "score": "6-4 6-4"}]
    return pd.DataFrame(rr)


def finals_event() -> Event:
    rows = finals_rows()
    ev = Event(index=0, tourney_id="TF", name="Tour Finals", level="F", surface="Hard",
               date=pd.Timestamp("2025-11-09"), season=2025, category="F", draw_size=8, best_of=3,
               final_tb=7, matches=rows, finals=build_round_robin(rows))
    ev.entry_rank = np.arange(1, 9)
    return ev


def test_finals_points_add_up():
    ev = finals_event()
    half = np.full((8, 8), 0.5)
    sims = simulate_season([prepared(ev, half, half)], ev.entrants, 3000, seed=4)
    pts = sims.event_points[0].astype(int)
    assert (pts.sum(axis=1) == 12 * 200 + 2 * 400 + 500).all()
    # round-robin wins x 200, +400 for a semi-final win, +500 for the title (one or two
    # group wins can still take the title: 1,100 or 1,300)
    assert set(np.unique(pts)) <= {0, 200, 400, 600, 800, 1000, 1100, 1300, 1500}
    champ_share = np.bincount(sims.champions[0], minlength=8) / 3000
    assert np.allclose(champ_share, 1 / 8, atol=0.03)


def test_finals_dominant_player_goes_through_unbeaten():
    ev = finals_event()
    pset = np.full((8, 8), 0.5)
    pm = np.full((8, 8), 0.5)
    pset[0, :], pset[:, 0] = 1.0, 0.0
    pm[0, :], pm[:, 0] = 1.0, 0.0
    sims = simulate_season([prepared(ev, pm, pset)], ev.entrants, 200, seed=5)
    assert (sims.event_points[0][:, 0] == 1500).all()


def test_three_way_tie_follows_the_atp_order():
    """2025 Connors group: Fritz, De Minaur and Musetti all 1-2. Sets won: 3/7, 3/7, 2/7.
    Musetti drops out on sets, then De Minaur beats Fritz on head-to-head."""
    fritz, dm, musetti = 0, 1, 2
    pct = np.array([3 / 7, 3 / 7, 2 / 7])
    beat = np.zeros((3, 3), dtype=bool)
    beat[dm, fritz] = beat[fritz, musetti] = beat[musetti, dm] = True
    assert _break_tie([fritz, dm, musetti], pct, beat, np.array([6, 8, 9])) == [dm, fritz, musetti]
    level = np.full(3, 0.5)
    assert _break_tie([0, 1, 2], level, beat, np.array([9, 3, 5])) == [1, 2, 0]  # falls to ranking
    assert _break_tie([fritz, dm], level, beat, np.array([1, 2])) == [dm, fritz]  # head-to-head


def test_competition_ranks_share_ties():
    pts = np.array([[10, 20, 20, 5], [0, 0, 0, 0]])
    assert competition_ranks(pts).tolist() == [[3, 1, 1, 4], [1, 1, 1, 1]]


def test_ledger_keeps_points_for_52_weeks():
    entries = pd.DataFrame({"player": [0, 1], "points": [100, 30],
                            "entry": pd.to_datetime(["2025-01-06", "2025-01-13"])})
    at = lambda d: ledger_at(pd.Timestamp(d), entries, 2).tolist()
    assert at("2025-01-05") == [0, 0]
    assert at("2025-01-06") == [100, 0]
    assert at("2025-12-29") == [100, 30]
    assert at("2026-01-05") == [0, 30]  # 52 weeks on: the next edition's week
    assert at("2026-01-12") == [0, 0]


def test_entrant_cards_equal_the_training_cards(real):
    """Every 2025 entrant card is the card the training table would hold for that key."""
    from atp_sim.form_cards import build_cards

    valid, players, _ = real
    events, _ = load_season_events(2025)
    cards = entrant_cards(events, valid, players)
    full, _ = build_cards(valid, players)
    lookup = full.set_index(["player_id", "tourney_date"])[[f"x_{k}" for k in range(8)]]
    checked = 0
    for e in events:
        assert cards[e.index].shape == (len(e.entrants), 8)
        for pid, row in zip(e.entrants, cards[e.index]):
            key = (int(pid), e.date)
            if key in lookup.index:
                np.testing.assert_allclose(lookup.loc[key].to_numpy(np.float64), row, atol=1e-12)
                checked += 1
    assert checked > 2500
