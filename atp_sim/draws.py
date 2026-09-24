"""The real draws of a season, rebuilt from its results (DESIGN.md §10, step 3).

Sackmann publishes results, not draw sheets, but a single-elimination draw can be read
back from its results: every player in a round either won a match in the round before or
entered there with a bye. Linking each match to the matches that fed it gives the exact
tree, without trusting `match_num` order or the csv's `draw_size` (which is wrong for most
2024 events). Every step is checked and anything that does not fit raises `DrawError`.

The ATP Finals are a round robin of two groups of four, then semi-finals and a final.
Team events (Davis Cup, United Cup, Laver Cup), the Olympics and the Next Gen Finals
(exhibition scoring) are left out, and listed as such.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import DATA_DIR, LIVE_SURFACES, apply_id_merges
from .match import best_of_for_level, final_tb_for_level
from .points import (
    FINALS_F_WIN, FINALS_RR_WIN, FINALS_SF_WIN,
    category_for, loss_points, table_for, winner_points,
)

__all__ = [
    "EXCLUDED_LEVELS", "EXCLUDED_NAMES_RE", "ROUNDS", "DrawError", "Event", "Knockout",
    "RoundRobin", "build_knockout", "build_round_robin", "load_season_events", "real_points",
]

ROUNDS = ("R128", "R64", "R32", "R16", "QF", "SF", "F")
EXCLUDED_LEVELS = ("D", "O")  # Davis Cup (team), Olympics (no ranking points)
EXCLUDED_NAMES_RE = r"United Cup|Laver Cup|Next ?Gen"
WALKOVER_RE = r"W/O|Walkover"
NO_RANK = 10_000  # entry rank for an unranked player


class DrawError(ValueError):
    """A draw that cannot be rebuilt exactly from its results."""


@dataclass
class Knockout:
    """A single-elimination draw as a list of match slots ("nodes") in playing order.

    Each node has two sides. A side is either an entrant (first round, or a bye into the
    second) or the winner of an earlier node. Nodes are ordered round by round, so every
    feeder comes before the node it feeds.
    """

    entrants: np.ndarray       # (E,) player_id per entrant index
    rounds: tuple[str, ...]    # rounds of this draw, first round to "F"
    node_round: np.ndarray     # (N,) index into `rounds`
    side: np.ndarray           # (N, 2) entrant index when side_is_entry, else node index
    side_is_entry: np.ndarray  # (N, 2) bool
    had_bye: np.ndarray        # (E,) bool
    real_winner: np.ndarray    # (N,) entrant index of the real winner of each node
    real_loser: np.ndarray     # (N,)
    real_walkover: np.ndarray  # (N,) bool

    @property
    def draw_size(self) -> int:
        return int(2 * (self.node_round == 0).sum() + self.had_bye.sum())


@dataclass
class RoundRobin:
    """ATP Finals: two groups of four, top two cross into the semi-finals."""

    entrants: np.ndarray        # (8,) player_id
    group: np.ndarray           # (8,) 0 or 1
    rr_pairs: np.ndarray        # (12, 2) entrant indices, lower index first
    real_rr_winner: np.ndarray  # (12,) entrant index
    real_sf_winners: np.ndarray  # (2,) entrant index
    real_champion: int


@dataclass
class Event:
    index: int
    tourney_id: str
    name: str
    level: str
    surface: str
    date: pd.Timestamp
    season: int
    category: str
    draw_size: int
    best_of: int
    final_tb: int
    matches: pd.DataFrame = field(repr=False)
    knockout: Knockout | None = field(default=None, repr=False)
    finals: RoundRobin | None = field(default=None, repr=False)
    entry_rank: np.ndarray | None = field(default=None, repr=False)  # (E,) rank at entry, NO_RANK if none

    @property
    def entrants(self) -> np.ndarray:
        return self.knockout.entrants if self.knockout is not None else self.finals.entrants

    @property
    def points_entry_date(self) -> pd.Timestamp:
        """Monday on which the event's points enter the ranking (estimated from its length)."""
        span = 13 if self.level == "G" else 11 if (self.level == "M" and self.draw_size == 96) else 6
        last_day = self.date + pd.Timedelta(days=span)
        return last_day + pd.Timedelta(days=7 - last_day.dayofweek)


def _order(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def build_knockout(m: pd.DataFrame) -> Knockout:
    """Rebuild one single-elimination draw from its result rows (walkovers included)."""
    unknown = sorted(set(m["round"]) - set(ROUNDS))
    if unknown:
        raise DrawError(f"rounds {unknown} do not belong in a knockout draw")
    present = [r for r in ROUNDS if (m["round"] == r).any()]
    if not present or present[-1] != "F" or tuple(present) != ROUNDS[ROUNDS.index(present[0]):]:
        raise DrawError(f"rounds {present} are not a contiguous run ending in the final")

    index: dict[int, int] = {}
    entrants: list[int] = []
    byes: set[int] = set()

    def enter(pid: int) -> int:
        if pid in index:
            raise DrawError(f"player {pid} enters the draw twice")
        index[pid] = len(entrants)
        entrants.append(pid)
        return index[pid]

    node_round, side, is_entry, win, lose, wo = [], [], [], [], [], []
    won_prev: dict[int, int] = {}
    for ri, rnd in enumerate(present):
        rows = m[m["round"] == rnd].sort_values("match_num", kind="mergesort")
        won_now: dict[int, int] = {}
        fed: set[int] = set()
        played_now: set[int] = set()
        for w, l, score in zip(rows["winner_id"], rows["loser_id"], rows["score"].astype(str)):
            w, l = int(w), int(l)
            # One match per player per round, so every feeder node is used exactly once.
            if w in played_now or l in played_now:
                raise DrawError(f"a player plays two {rnd} matches")
            played_now.update((w, l))
            sides = []
            for pid in sorted((w, l)):
                if ri > 0 and pid in won_prev:
                    sides.append((won_prev[pid], False))
                    fed.add(won_prev[pid])
                elif (ri == 0 or (ri == 1 and rnd != "F")) and pid not in index:
                    sides.append((enter(pid), True))
                    if ri == 1:
                        byes.add(pid)
                else:
                    raise DrawError(f"player {pid} plays {rnd} without winning a {present[ri - 1]} match")
            if ri == 1 and all(e for _, e in sides):
                raise DrawError(f"two byes meet in {rnd}: a first-round result is probably missing")
            node = len(node_round)
            node_round.append(ri)
            side.append([s for s, _ in sides])
            is_entry.append([e for _, e in sides])
            win.append(w)
            lose.append(l)
            wo.append(bool(re.search(WALKOVER_RE, score, flags=re.IGNORECASE)))
            won_now[w] = node
        if ri > 0 and fed != set(won_prev.values()):
            raise DrawError(f"{len(set(won_prev.values()) - fed)} {present[ri - 1]} winners never play {rnd}")
        won_prev = won_now
    if len(won_prev) != 1:
        raise DrawError("the draw does not end in a single final")

    ko = Knockout(
        entrants=np.array(entrants, dtype=np.int64),
        rounds=tuple(present),
        node_round=np.array(node_round, dtype=np.int64),
        side=np.array(side, dtype=np.int64),
        side_is_entry=np.array(is_entry, dtype=bool),
        had_bye=np.array([pid in byes for pid in entrants], dtype=bool),
        real_winner=np.array([index[p] for p in win], dtype=np.int64),
        real_loser=np.array([index[p] for p in lose], dtype=np.int64),
        real_walkover=np.array(wo, dtype=bool),
    )
    expected = 2 ** len(present)
    if not (expected // 2 < ko.draw_size <= expected):
        raise DrawError(f"a {ko.draw_size} draw does not fit {len(present)} rounds")
    # Every ATP format has an even draw and at most as many byes as first-round matches
    # (96: 32 and 32, 28: 4 and 12). Anything else means a first-round result is missing
    # and its winner was taken for a bye.
    if ko.draw_size % 2:
        raise DrawError(f"odd draw size {ko.draw_size}: a first-round result is probably missing")
    if ko.had_bye.sum() > (ko.node_round == 0).sum():
        raise DrawError(f"{int(ko.had_bye.sum())} byes but only {int((ko.node_round == 0).sum())} "
                        "first-round matches: a first-round result is probably missing")
    return ko


def build_round_robin(m: pd.DataFrame) -> RoundRobin:
    """Rebuild the ATP Finals: two complete groups of four, two semi-finals, one final."""
    if set(m["round"]) != {"RR", "SF", "F"}:
        raise DrawError(f"ATP Finals rounds {sorted(set(m['round']))} are not RR, SF and F")
    rr = m[m["round"] == "RR"]
    players = sorted({int(p) for p in pd.concat([rr["winner_id"], rr["loser_id"]])})
    if len(players) != 8 or len(rr) != 12:
        raise DrawError(f"round robin has {len(players)} players and {len(rr)} matches, not 8 and 12")
    idx = {p: i for i, p in enumerate(players)}
    parent = list(range(8))

    def root(i: int) -> int:
        while parent[i] != i:
            i = parent[i]
        return i

    pairs, winners = [], []
    for w, l in zip(rr["winner_id"].astype(int), rr["loser_id"].astype(int)):
        a, b = idx[w], idx[l]
        parent[root(a)] = root(b)
        pairs.append(_order(a, b))
        winners.append(a)
    roots = sorted({root(i) for i in range(8)})
    if len(roots) != 2 or len(set(pairs)) != 12:
        raise DrawError("round robin is not two groups where everyone meets once")
    group = np.array([roots.index(root(i)) for i in range(8)], dtype=np.int64)
    if sorted(np.bincount(group).tolist()) != [4, 4]:
        raise DrawError("round robin groups are not four and four")

    sf = m[m["round"] == "SF"]
    fin = m[m["round"] == "F"]
    if len(sf) != 2 or len(fin) != 1:
        raise DrawError("ATP Finals need two semi-finals and one final")
    for w, l in zip(sf["winner_id"].astype(int), sf["loser_id"].astype(int)):
        if w not in idx or l not in idx or group[idx[w]] == group[idx[l]]:
            raise DrawError("a semi-final is not one player from each group")
    champ = idx[int(fin["winner_id"].iloc[0])]
    return RoundRobin(
        entrants=np.array(players, dtype=np.int64),
        group=group,
        rr_pairs=np.array(pairs, dtype=np.int64),
        real_rr_winner=np.array(winners, dtype=np.int64),
        real_sf_winners=np.array([idx[int(w)] for w in sf["winner_id"]], dtype=np.int64),
        real_champion=champ,
    )


def _entry_rank(m: pd.DataFrame, entrants: np.ndarray) -> np.ndarray:
    w = m[["winner_id", "winner_rank"]].set_axis(["pid", "rank"], axis=1)
    l = m[["loser_id", "loser_rank"]].set_axis(["pid", "rank"], axis=1)
    ranks = pd.concat([w, l]).groupby("pid")["rank"].min()
    return ranks.reindex(entrants).fillna(NO_RANK).to_numpy(np.int64)


def load_season_events(
    season: int,
    data_dir: str = DATA_DIR,
) -> tuple[list[Event], pd.DataFrame]:
    """(events in playing order, the excluded events with a reason) for one file year."""
    path = os.path.join(data_dir, f"atp_matches_{season}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run ./fetch_data.sh first.")
    raw = pd.read_csv(path, low_memory=False)
    for col in ("winner_id", "loser_id", "tourney_date", "match_num"):
        raw[col] = pd.to_numeric(raw[col], errors="raise").astype("int64")
    raw = apply_id_merges(raw)
    raw["tourney_date"] = pd.to_datetime(raw["tourney_date"].astype(str), format="%Y%m%d")

    heads = (raw.groupby("tourney_id", sort=False)
             .agg(name=("tourney_name", "first"), level=("tourney_level", "first"),
                  surface=("surface", "first"), date=("tourney_date", "min"),
                  n=("tourney_id", "size"))
             .reset_index().sort_values(["date", "tourney_id"], kind="mergesort"))
    excluded, events = [], []
    for h in heads.itertuples(index=False):
        reason = None
        if h.level in EXCLUDED_LEVELS:
            reason = "team event" if h.level == "D" else "no ranking points"
        elif re.search(EXCLUDED_NAMES_RE, str(h.name), flags=re.IGNORECASE):
            reason = "team or exhibition format"
        elif h.surface not in LIVE_SURFACES:
            reason = f"surface {h.surface}"
        if reason:
            excluded.append({"tourney_id": h.tourney_id, "name": h.name, "level": h.level,
                             "date": h.date.date(), "matches": int(h.n), "reason": reason})
            continue
        m = raw[raw["tourney_id"] == h.tourney_id]
        knockout = finals = None
        if h.level == "F":
            finals = build_round_robin(m)
            draw_size = 8
        else:
            try:
                knockout = build_knockout(m)
            except DrawError as e:
                raise DrawError(f"{h.name} ({h.tourney_id}): {e}") from None
            draw_size = knockout.draw_size
        category = category_for(h.level, str(h.name), season)
        if category != "F":
            table_for(category, draw_size)  # fail now, not mid-season, on a missing row
        ev = Event(
            index=len(events), tourney_id=str(h.tourney_id), name=str(h.name), level=h.level,
            surface=h.surface, date=h.date, season=season, category=category, draw_size=draw_size,
            best_of=best_of_for_level(h.level), final_tb=final_tb_for_level(h.level),
            matches=m.reset_index(drop=True), knockout=knockout, finals=finals,
        )
        ev.entry_rank = _entry_rank(m, ev.entrants)
        events.append(ev)
    return events, pd.DataFrame(excluded)


def real_points(ev: Event) -> dict[int, int]:
    """Ranking points each entrant actually earned, scored with the simulator's table.

    A walkover counts as a normal loss in that round, the same as in the simulation.
    """
    out: dict[int, int] = {}
    if ev.finals is not None:
        f = ev.finals
        pts = np.bincount(f.real_rr_winner, minlength=8) * FINALS_RR_WIN
        pts[f.real_sf_winners] += FINALS_SF_WIN
        pts[f.real_champion] += FINALS_F_WIN
        return {int(p): int(v) for p, v in zip(f.entrants, pts)}
    ko = ev.knockout
    table = table_for(ev.category, ev.draw_size)
    for n in range(len(ko.node_round)):
        loser = int(ko.real_loser[n])
        rnd = ko.rounds[ko.node_round[n]]
        out[int(ko.entrants[loser])] = loss_points(table, ko.rounds, rnd, bool(ko.had_bye[loser]))
    out[int(ko.entrants[ko.real_winner[-1]])] = winner_points(table)
    return out
