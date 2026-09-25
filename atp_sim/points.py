"""ATP singles ranking points by category, draw size and round reached (docs/season_simulation.md, step 4).

One table, used for everything the simulator scores: the simulated 2025 season, the real
2025 season on the same events (the "same-table actual" race) and the real 2024 results
that seed the 52-week ledger. Scoring real and simulated seasons with one table is what
lets the comparison separate simulator error from points-rule error.

Sources are recorded in verification/antigravity/simulation_review/points_table_check.md.
Sackmann codes ATP 500 and ATP 250 events both as level "A", so the split is by name.
"""

from __future__ import annotations

__all__ = [
    "FINALS_F_WIN", "FINALS_RR_WIN", "FINALS_SF_WIN", "PointsRuleError",
    "atp500_names", "category_for", "loss_points", "table_for", "winner_points",
]


class PointsRuleError(ValueError):
    """An event whose category or draw size has no row in the table."""


# Points for the round a player lost in; "W" is the champion.
_SLAM = {"W": 2000, "F": 1300, "SF": 800, "QF": 400, "R16": 200, "R32": 100, "R64": 50, "R128": 10}
_M1000_96 = {"W": 1000, "F": 650, "SF": 400, "QF": 200, "R16": 100, "R32": 50, "R64": 30, "R128": 10}
_M1000_56 = {"W": 1000, "F": 650, "SF": 400, "QF": 200, "R16": 100, "R32": 50, "R64": 10}
_A500_32 = {"W": 500, "F": 330, "SF": 200, "QF": 100, "R16": 50, "R32": 0}
_A500_48 = {"W": 500, "F": 330, "SF": 200, "QF": 100, "R16": 50, "R32": 25, "R64": 0}
_A250_32 = {"W": 250, "F": 165, "SF": 100, "QF": 50, "R16": 25, "R32": 0}
_A250_48 = {"W": 250, "F": 165, "SF": 100, "QF": 50, "R16": 25, "R32": 13, "R64": 0}

TABLES: dict[tuple[str, int], dict[str, int]] = {
    ("G", 128): _SLAM,
    ("M", 96): _M1000_96,
    ("M", 56): _M1000_56,
    ("500", 32): _A500_32,
    ("500", 48): _A500_48,
    ("250", 28): _A250_32,
    ("250", 32): _A250_32,
    ("250", 48): _A250_48,
}

# ATP Finals: points are earned per match won, not per round reached.
FINALS_RR_WIN = 200
FINALS_SF_WIN = 400
FINALS_F_WIN = 500

# A player with a first-round bye who loses his first match scores as a first-round loser.
BYE_LOSS_SCORES_FIRST_ROUND = True

_ATP500 = {
    2024: ("Rotterdam", "Rio de Janeiro", "Acapulco", "Dubai", "Barcelona", "Halle",
           "Queen's Club", "Hamburg", "Washington", "Tokyo", "Beijing", "Vienna", "Basel"),
    # 2025: Doha, Dallas and Munich promoted from 250.
    2025: ("Rotterdam", "Dallas", "Doha", "Rio de Janeiro", "Acapulco", "Dubai", "Barcelona",
           "Munich", "Hamburg", "Queen's Club", "Halle", "Washington", "Tokyo", "Beijing",
           "Vienna", "Basel"),
}


def atp500_names(season: int) -> frozenset[str]:
    if season not in _ATP500:
        raise PointsRuleError(f"no ATP 500 list for season {season}")
    return frozenset(n.casefold() for n in _ATP500[season])


def category_for(level: str, name: str, season: int) -> str:
    """'G', 'M', '500', '250' or 'F' (ATP Finals)."""
    if level in ("G", "M", "F"):
        return level
    if level == "A":
        return "500" if name.casefold() in atp500_names(season) else "250"
    raise PointsRuleError(f"level {level!r} ({name}) earns no ranking points in this table")


def table_for(category: str, draw_size: int) -> dict[str, int]:
    try:
        return TABLES[(category, int(draw_size))]
    except KeyError:
        raise PointsRuleError(f"no points row for a {category} event with a {draw_size} draw") from None


def loss_points(table: dict[str, int], rounds: tuple[str, ...], round_lost: str, had_bye: bool) -> int:
    """Points for losing in `round_lost` of an event whose rounds run `rounds[0]` to 'F'."""
    if round_lost not in table:
        raise PointsRuleError(f"round {round_lost!r} is not in this event's table")
    if had_bye and BYE_LOSS_SCORES_FIRST_ROUND and len(rounds) > 1 and round_lost == rounds[1]:
        return table[rounds[0]]
    return table[round_lost]


def winner_points(table: dict[str, int]) -> int:
    return table["W"]
