"""From two serve-point probabilities to a match winner (design §10, step 2).

Everything here is exact arithmetic on the standard assumption that every point is an
independent coin with the server's probability. Functions take numpy arrays and work
element by element, so a whole pairing matrix is one call.

    p_hold       point  -> game        closed form with the deuce geometric series
    p_tiebreak   point  -> tiebreak    first to 7 (or 10) by two, serve 1 then 2-2-2
    p_set        game   -> set         first to 6 by two, tiebreak at 6-6
    p_match      set    -> match       best of 3 or 5, own format for the deciding set

`pa` is always the chance that player A wins a point on his own serve, `pb` the same
for B. A result is the probability that A wins. Who serves first does not change a
tiebreak, set or match probability under this assumption (Newton and Keller, 2005),
which the tests check numerically, so no function needs to know it.

`simulate_match` plays the same rules point by point with a random generator. It is the
independent check on the recursions, not what the season simulator uses.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "SLAM_FINAL_TB", "TOUR_TB", "best_of_for_level", "final_tb_for_level",
    "p_hold", "p_tiebreak", "p_set", "p_match", "simulate_match",
]

TOUR_TB = 7         # every set on tour, and every non-deciding set at a Slam
SLAM_FINAL_TB = 10  # deciding set at the four Slams since 2022: first to 10 by two at 6-6
SET_GAMES = 6

ArrayLike = float | np.ndarray  # a probability, or an array of them element by element


def best_of_for_level(level: str) -> int:
    """Slams are best of five, everything else on tour (ATP Finals included) best of three.

    Taken from the level, not from the csv's `best_of`, which is 3 on some Slam
    walkover and retirement rows.
    """
    return 5 if level == "G" else 3


def final_tb_for_level(level: str) -> int:
    """Deciding-set tiebreak target: 10 at a Slam, 7 everywhere else."""
    return SLAM_FINAL_TB if level == "G" else TOUR_TB


def _arrays(pa: ArrayLike, pb: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    a, b = np.broadcast_arrays(np.asarray(pa, dtype=np.float64), np.asarray(pb, dtype=np.float64))
    # Written as "inside the range" so that NaN, which fails every comparison, is rejected too.
    if not (((a >= 0) & (a <= 1)).all() and ((b >= 0) & (b <= 1)).all()):
        raise ValueError("serve-point probabilities must lie in [0, 1] (NaN included)")
    return a, b


def _race_from_tie(win_a: np.ndarray, win_b: np.ndarray) -> np.ndarray:
    """P(A takes two in a row first) when each two-step round goes A, B or back to level."""
    den = win_a + win_b
    return np.divide(win_a, den, out=np.full_like(win_a, 0.5), where=den > 0)


def p_hold(p: ArrayLike) -> np.ndarray:
    """Probability the server wins a game from 0-0.

    Win to 0, 15 or 30: p^4 (1 + 4q + 10q^2). Reach deuce (3-3): 20 p^3 q^3, then win
    two points in a row before losing two: p^2 / (p^2 + q^2).
    """
    p = np.asarray(p, dtype=np.float64)
    q = 1.0 - p
    from_deuce = _race_from_tie(p * p, q * q)
    return p**4 * (1 + 4 * q + 10 * q * q) + 20 * p**3 * q**3 * from_deuce


def _tb_a_serves(k: int) -> bool:
    """A serves point k (0-based) of a tiebreak that A opens: A, B B, A A, B B, ..."""
    return k == 0 or ((k - 1) // 2) % 2 == 1


def p_tiebreak(pa: ArrayLike, pb: ArrayLike, target: int = TOUR_TB) -> np.ndarray:
    """Probability A wins a tiebreak to `target` (win by two) that A serves first.

    Dynamic programme over the score. From target-1 all, every two points contain one
    serve each, so the rest is a race: A wins a pair with pa(1 - pb), B with (1 - pa)pb.
    """
    a, b = _arrays(pa, pb)
    n = target - 1
    reach = np.zeros((n + 1, n + 1) + a.shape)
    reach[0, 0] = 1.0
    win = np.zeros_like(a)
    for k in range(2 * n):
        on_serve = a if _tb_a_serves(k) else 1.0 - b  # P(A wins point k)
        for i in range(max(0, k - n), min(k, n) + 1):
            j = k - i
            r = reach[i, j]
            if i == n:
                win += r * on_serve  # A reaches target with B at most target-2
            else:
                reach[i + 1, j] += r * on_serve
            if j < n:
                reach[i, j + 1] += r * (1.0 - on_serve)
    return win + reach[n, n] * _race_from_tie(a * (1.0 - b), (1.0 - a) * b)


def p_set(pa: ArrayLike, pb: ArrayLike, tb_target: int = TOUR_TB) -> np.ndarray:
    """Probability A wins a set that A serves first: first to 6 by two, tiebreak at 6-6.

    Serve alternates by game, so A serves game k when k is even; after twelve games A
    also serves first in the tiebreak.
    """
    a, b = _arrays(pa, pb)
    ha, hb = p_hold(a), p_hold(b)
    reach = np.zeros((SET_GAMES + 2, SET_GAMES + 2) + a.shape)
    reach[0, 0] = 1.0
    win = np.zeros_like(a)

    def a_won(i: int, j: int) -> bool:
        return (i == SET_GAMES and j <= SET_GAMES - 2) or i == SET_GAMES + 1

    for k in range(2 * SET_GAMES):
        take = ha if k % 2 == 0 else 1.0 - hb  # P(A wins game k)
        for i in range(0, k + 1):
            j = k - i
            if i > SET_GAMES + 1 or j > SET_GAMES + 1:
                continue
            if a_won(i, j) or a_won(j, i):
                continue  # already decided, carries no mass forward
            r = reach[i, j]
            if a_won(i + 1, j):
                win += r * take
            else:
                reach[i + 1, j] += r * take
            if not a_won(j + 1, i):
                reach[i, j + 1] += r * (1.0 - take)
    tb = p_tiebreak(a, b, tb_target)
    return win + reach[SET_GAMES, SET_GAMES] * tb


def p_match(pa: ArrayLike, pb: ArrayLike, best_of: int = 3, final_tb: int = TOUR_TB) -> np.ndarray:
    """Probability A wins a best-of-3 or best-of-5 match.

    Sets are independent with the same probability, except the deciding set, which uses
    its own tiebreak target (10 at a Slam).
    """
    if best_of not in (3, 5):
        raise ValueError(f"best_of must be 3 or 5, got {best_of}")
    a, b = _arrays(pa, pb)
    s = p_set(a, b, TOUR_TB)
    s_final = s if final_tb == TOUR_TB else p_set(a, b, final_tb)
    need = (best_of + 1) // 2
    reach = np.zeros((need, need) + a.shape)
    reach[0, 0] = 1.0
    win = np.zeros_like(a)
    for k in range(2 * need - 1):
        for i in range(max(0, k - need + 1), min(k, need - 1) + 1):
            j = k - i
            r = reach[i, j]
            take = s_final if i == j == need - 1 else s
            if i + 1 == need:
                win += r * take
            else:
                reach[i + 1, j] += r * take
            if j + 1 < need:
                reach[i, j + 1] += r * (1.0 - take)
    return win


def simulate_match(
    pa: float,
    pb: float,
    rng: np.random.Generator,
    best_of: int = 3,
    final_tb: int = TOUR_TB,
    a_serves_first: bool = True,
) -> bool:
    """Play one match point by point with the real serve order; True when A wins.

    Serve alternates every game across the whole match, and a tiebreak counts as one
    game opened by whoever's turn it was. Used by the tests only.
    """
    need = (best_of + 1) // 2
    sets_a = sets_b = 0
    a_serving = a_serves_first
    while sets_a < need and sets_b < need:
        deciding = sets_a == sets_b == need - 1
        target = final_tb if deciding else TOUR_TB
        ga = gb = 0
        while True:
            if ga == gb == SET_GAMES:
                pts_a = pts_b = 0
                k = 0
                while True:
                    a_on_serve = a_serving if k == 0 or ((k - 1) // 2) % 2 == 1 else not a_serving
                    a_point = rng.random() < (pa if a_on_serve else 1.0 - pb)
                    pts_a += a_point
                    pts_b += not a_point
                    k += 1
                    if max(pts_a, pts_b) >= target and abs(pts_a - pts_b) >= 2:
                        break
                a_game = pts_a > pts_b
            else:
                p_server = pa if a_serving else pb
                ps = po = 0
                while not (max(ps, po) >= 4 and abs(ps - po) >= 2):
                    if rng.random() < p_server:
                        ps += 1
                    else:
                        po += 1
                a_game = (ps > po) == a_serving
            ga += a_game
            gb += not a_game
            a_serving = not a_serving
            if (max(ga, gb) >= SET_GAMES and abs(ga - gb) >= 2) or ga + gb == 2 * SET_GAMES + 1:
                break
        if ga > gb:
            sets_a += 1
        else:
            sets_b += 1
    return sets_a > sets_b
