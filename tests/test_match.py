"""Match engine: the recursions against hand values, symmetry and a point-by-point replay."""

from __future__ import annotations

import numpy as np
import pytest

from atp_sim.match import (
    SLAM_FINAL_TB, TOUR_TB, best_of_for_level, final_tb_for_level,
    p_hold, p_match, p_set, p_tiebreak, simulate_match,
)

GRID = np.linspace(0.30, 0.85, 12)
PA, PB = np.meshgrid(GRID, GRID, indexing="ij")


def test_hold_closed_form():
    assert float(p_hold(0.5)) == pytest.approx(0.5, abs=1e-12)
    p, q = 0.6, 0.4
    expected = p**4 * (1 + 4 * q + 10 * q**2) + 20 * p**3 * q**3 * p**2 / (p**2 + q**2)
    assert float(p_hold(0.6)) == pytest.approx(expected, abs=1e-12)
    assert float(p_hold(0.6)) == pytest.approx(0.735729, abs=1e-6)  # textbook value
    assert float(p_hold(0.0)) == 0.0 and float(p_hold(1.0)) == 1.0


def test_hold_is_increasing():
    h = p_hold(np.linspace(0.01, 0.99, 99))
    assert (np.diff(h) > 0).all()


def test_equal_players_are_even():
    for p in (0.55, 0.62, 0.70):
        assert float(p_tiebreak(p, p)) == pytest.approx(0.5, abs=1e-12)
        assert float(p_tiebreak(p, p, SLAM_FINAL_TB)) == pytest.approx(0.5, abs=1e-12)
        assert float(p_set(p, p)) == pytest.approx(0.5, abs=1e-12)
        assert float(p_match(p, p, 3)) == pytest.approx(0.5, abs=1e-12)
        assert float(p_match(p, p, 5, SLAM_FINAL_TB)) == pytest.approx(0.5, abs=1e-12)


@pytest.mark.parametrize("fn", [
    lambda a, b: p_tiebreak(a, b),
    lambda a, b: p_tiebreak(a, b, SLAM_FINAL_TB),
    lambda a, b: p_set(a, b),
    lambda a, b: p_match(a, b, 3),
    lambda a, b: p_match(a, b, 5, SLAM_FINAL_TB),
])
def test_order_of_serve_does_not_matter(fn):
    """fn(a, b) has A serving first; 1 - fn(b, a) is A's chance when B serves first."""
    np.testing.assert_allclose(fn(PA, PB), 1.0 - fn(PB, PA), atol=1e-12)


def test_probabilities_are_proper_and_monotone():
    for m in (p_set(PA, PB), p_match(PA, PB, 3), p_match(PA, PB, 5, SLAM_FINAL_TB)):
        assert ((m >= 0) & (m <= 1)).all()
        assert (np.diff(m, axis=0) > 0).all()  # better server, better chance
        assert (np.diff(m, axis=1) < 0).all()  # better opponent, worse chance


def test_best_of_five_amplifies_the_favourite():
    b3 = p_match(PA, PB, 3)
    b5 = p_match(PA, PB, 5, SLAM_FINAL_TB)
    assert (b5[PA > PB] > b3[PA > PB]).all()
    assert (b5[PA < PB] < b3[PA < PB]).all()


def test_sanity_figures():
    # The two reference matchups used in the docs.
    assert float(p_match(0.62, 0.62, 3)) == pytest.approx(0.5, abs=1e-12)
    assert float(p_match(0.65, 0.58, 3)) == pytest.approx(0.8141, abs=1e-4)


def test_ten_point_tiebreak_favours_the_better_player_more():
    assert float(p_tiebreak(0.70, 0.60, SLAM_FINAL_TB)) > float(p_tiebreak(0.70, 0.60))


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        p_match(1.2, 0.5)
    with pytest.raises(ValueError):  # NaN fails every comparison, so it needs its own check
        p_match(np.array([0.6, np.nan]), 0.5)
    with pytest.raises(ValueError):
        p_match(0.6, 0.5, best_of=4)


def test_level_formats():
    assert best_of_for_level("G") == 5 and final_tb_for_level("G") == SLAM_FINAL_TB
    for level in ("M", "A", "F"):
        assert best_of_for_level(level) == 3 and final_tb_for_level(level) == TOUR_TB


@pytest.mark.parametrize("pa,pb,best_of,final_tb,a_first", [
    (0.66, 0.61, 3, TOUR_TB, True),
    (0.66, 0.61, 3, TOUR_TB, False),
    (0.64, 0.66, 5, SLAM_FINAL_TB, True),
])
def test_point_by_point_replay_agrees(pa, pb, best_of, final_tb, a_first):
    """20,000 matches played point by point land within 1.1 pp (3 sigma) of the recursion."""
    rng = np.random.default_rng(7)
    n = 20_000
    wins = sum(simulate_match(pa, pb, rng, best_of, final_tb, a_first) for _ in range(n))
    assert wins / n == pytest.approx(float(p_match(pa, pb, best_of, final_tb)), abs=0.011)
