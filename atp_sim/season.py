"""The season loop (DESIGN.md §10, steps 3 to 5): real draws, simulated winners, points, repeated.

The two runs share everything except the serve model: the same events, draws, form cards
and random numbers. Each event has its own generator seeded from (seed, event index) and
each match slot its own row of uniforms, so a slot's coin is identical in both runs and a
different outcome can only come from a different model (common random numbers).

Form cards are frozen at each event's real start date and computed from real results
only. Simulated results never feed back into later cards; tournaments are linked through
ranking points alone. This is an A/B test of the serve model, not a closed fantasy season.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch

from .draws import Event, real_points
from .form_cards import N_ATTRS, build_cards
from .match import TOUR_TB, p_match, p_set
from .model import SurfaceBundle
from .points import FINALS_F_WIN, FINALS_RR_WIN, FINALS_SF_WIN, loss_points, table_for, winner_points

__all__ = [
    "PreparedEvent", "SeasonSims", "competition_ranks", "entrant_cards", "ledger_at",
    "prepare_events", "real_entries", "simulate_season",
]

RR_SETS = 3  # uniforms reserved per round-robin match: up to three sets


@dataclass
class PreparedEvent:
    event: Event
    player_idx: np.ndarray     # (E,) index into the season's player list
    cards: np.ndarray          # (E, 8) standardised form cards at the event's start date
    p_serve: np.ndarray        # (E, E) P(i wins a point serving to j)
    p_match: np.ndarray        # (E, E) P(i beats j) in this event's format
    p_set: np.ndarray | None   # (8, 8) P(i wins a set against j), ATP Finals only


@dataclass
class SeasonSims:
    player_ids: np.ndarray           # (N,) the season's player list
    event_points: list[np.ndarray]   # per event, (S, E) points earned in each simulation
    champions: np.ndarray            # (n_events, S) season player index of the champion
    totals: np.ndarray               # (S, N) points over the simulated events
    n_sims: int
    seed: int


def entrant_cards(events: list[Event], valid: pd.DataFrame, players: pd.DataFrame) -> dict[int, np.ndarray]:
    """{event index: (E, 8) cards}, every entrant's card at the event's real start date.

    One `build_cards` call over all keys, so walkover and missing-statistics entrants get
    the same causal card as anyone else: only matches dated before the event count.
    """
    wanted = [pd.DataFrame({"event": e.index, "player_id": e.entrants, "tourney_date": e.date,
                            "season": e.season}) for e in events]
    wanted = pd.concat(wanted, ignore_index=True)
    keys = wanted.drop_duplicates(["player_id", "tourney_date"])
    cards, _ = build_cards(valid, players, keys=keys[["player_id", "tourney_date", "season"]])
    xcols = [f"x_{k}" for k in range(N_ATTRS)]
    got = wanted.merge(cards[["player_id", "tourney_date"] + xcols], on=["player_id", "tourney_date"],
                       how="left", validate="many_to_one")
    if got[xcols].isna().any().any():
        missing = got.loc[got[xcols].isna().any(axis=1), ["event", "player_id"]].head().to_dict("records")
        raise ValueError(f"entrants without a card (season constants missing?): {missing}")
    return {int(k): g[xcols].to_numpy(np.float64) for k, g in got.groupby("event", sort=False)}


def _pairwise_serve(bundle: SurfaceBundle, surface: str, x: np.ndarray) -> np.ndarray:
    """(E, E) serve-point probabilities, row player serving to column player."""
    e = len(x)
    t = torch.tensor(x, dtype=torch.float32)
    with torch.no_grad():
        p = bundle.predict(surface, t[:, None, :].expand(e, e, N_ATTRS), t[None, :, :].expand(e, e, N_ATTRS))
    return p.double().numpy()


def prepare_events(
    events: list[Event],
    bundle: SurfaceBundle,
    cards: dict[int, np.ndarray],
    player_index: dict[int, int],
) -> list[PreparedEvent]:
    """Everything deterministic about each event. Only `p_serve` onward depends on the model."""
    out = []
    for e in events:
        x = cards[e.index]
        ps = _pairwise_serve(bundle, e.surface, x)
        pm = p_match(ps, ps.T, e.best_of, e.final_tb)
        pset = p_set(ps, ps.T, TOUR_TB) if e.finals is not None else None
        out.append(PreparedEvent(
            event=e, player_idx=np.array([player_index[int(p)] for p in e.entrants], dtype=np.int64),
            cards=x, p_serve=ps, p_match=pm, p_set=pset,
        ))
    return out


def _event_rng(seed: int, event_index: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(event_index,)))


def _play_knockout(pe: PreparedEvent, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(points (S, E), champion entrant (S,)) for one draw, one uniform row per node."""
    ko = pe.event.knockout
    table = table_for(pe.event.category, pe.event.draw_size)
    n_nodes, sims = u.shape
    rows = np.arange(sims)
    winners = np.empty((n_nodes, sims), dtype=np.int64)
    pts = np.zeros((sims, len(ko.entrants)), dtype=np.int16)
    for n in range(n_nodes):
        rnd = ko.rounds[ko.node_round[n]]
        side, loss = [], []
        for k in (0, 1):
            s = int(ko.side[n, k])
            if ko.side_is_entry[n, k]:
                side.append(np.full(sims, s))
                loss.append(loss_points(table, ko.rounds, rnd, bool(ko.had_bye[s])))
            else:
                side.append(winners[s])
                loss.append(loss_points(table, ko.rounds, rnd, False))
        a, b = side
        a_wins = u[n] < pe.p_match[a, b]
        winners[n] = np.where(a_wins, a, b)
        pts[rows, np.where(a_wins, b, a)] = np.where(a_wins, loss[1], loss[0])
    champion = winners[-1]
    pts[rows, champion] = winner_points(table)
    return pts, champion


def _break_tie(tied: list[int], pct: np.ndarray, beat: np.ndarray, rank: np.ndarray) -> list[int]:
    """ATP Finals group tie-break for one simulation.

    Two tied: head-to-head. Three tied: sets won %, and as soon as that splits them the
    remaining tie goes back through this function (two left means head-to-head). Games
    won % comes next in the real rules but games are not simulated, so an unbroken
    three-way tie falls through to the ranking at entry.
    """
    if len(tied) == 1:
        return tied
    if len(tied) == 2:
        a, b = tied
        return [a, b] if beat[a, b] else [b, a]
    levels = sorted({round(float(pct[p]), 12) for p in tied}, reverse=True)
    if len(levels) == 1:
        return sorted(tied, key=lambda p: rank[p])
    out = []
    for level in levels:
        out += _break_tie([p for p in tied if round(float(pct[p]), 12) == level], pct, beat, rank)
    return out


def _play_finals(pe: PreparedEvent, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Round robin set by set, then semi-finals (winner vs other group's runner-up) and final."""
    f = pe.event.finals
    sims = u.shape[1]
    wins = np.zeros((sims, 8), dtype=np.int64)
    sets_won = np.zeros((sims, 8), dtype=np.int64)
    sets_played = np.zeros((sims, 8), dtype=np.int64)
    beat = np.zeros((sims, 8, 8), dtype=bool)
    rows = np.arange(sims)
    for i, (a, b) in enumerate(f.rr_pairs):
        s = u[RR_SETS * i: RR_SETS * (i + 1)] < pe.p_set[a, b]  # (3, S): A takes set k
        decided = s[0] == s[1]
        a_sets = np.where(decided, 2 * s[0], 1 + s[2]).astype(np.int64)
        b_sets = np.where(decided, 2 * ~s[0], 1 + ~s[2]).astype(np.int64)
        a_won = a_sets == 2
        wins[:, a] += a_won
        wins[:, b] += ~a_won
        sets_won[:, a] += a_sets
        sets_won[:, b] += b_sets
        sets_played[:, a] += a_sets + b_sets
        sets_played[:, b] += a_sets + b_sets
        beat[rows, a, b] = a_won
        beat[rows, b, a] = ~a_won
    pct = sets_won / sets_played
    members = [np.flatnonzero(f.group == g).tolist() for g in (0, 1)]
    first = np.empty((2, sims), dtype=np.int64)
    second = np.empty((2, sims), dtype=np.int64)
    for s_i in range(sims):
        for g in (0, 1):
            order = []
            for w in sorted({int(wins[s_i, p]) for p in members[g]}, reverse=True):
                tied = [p for p in members[g] if wins[s_i, p] == w]
                order += _break_tie(tied, pct[s_i], beat[s_i], pe.event.entry_rank)
            first[g, s_i], second[g, s_i] = order[0], order[1]
    base = RR_SETS * len(f.rr_pairs)
    pts = (wins * FINALS_RR_WIN).astype(np.int16)
    finalists = []
    for k, (a, b) in enumerate(((first[0], second[1]), (first[1], second[0]))):
        w = np.where(u[base + k] < pe.p_match[a, b], a, b)
        pts[rows, w] += FINALS_SF_WIN
        finalists.append(w)
    a, b = finalists
    champion = np.where(u[base + 2] < pe.p_match[a, b], a, b)
    pts[rows, champion] += FINALS_F_WIN
    return pts, champion


def simulate_season(prepared: list[PreparedEvent], player_ids: np.ndarray, n_sims: int, seed: int) -> SeasonSims:
    """Play every event `n_sims` times. `player_ids` is the season list the indices refer to."""
    event_points, champions = [], []
    totals = np.zeros((n_sims, len(player_ids)), dtype=np.int32)
    for pe in prepared:
        rng = _event_rng(seed, pe.event.index)
        if pe.event.finals is not None:
            u = rng.random((RR_SETS * len(pe.event.finals.rr_pairs) + 3, n_sims))
            pts, champ = _play_finals(pe, u)
        else:
            u = rng.random((len(pe.event.knockout.node_round), n_sims))
            pts, champ = _play_knockout(pe, u)
        totals[:, pe.player_idx] += pts  # entrants are distinct within an event
        event_points.append(pts)
        champions.append(pe.player_idx[champ])
    return SeasonSims(player_ids=np.asarray(player_ids), event_points=event_points,
                      champions=np.array(champions), totals=totals, n_sims=n_sims, seed=seed)


def competition_ranks(points: np.ndarray) -> np.ndarray:
    """Row-wise rank, 1 = most points; ties share the best rank (1, 2, 2, 4)."""
    order = np.argsort(-points, axis=1, kind="stable")
    ordered = np.take_along_axis(points, order, axis=1)
    pos = np.broadcast_to(np.arange(points.shape[1]), points.shape)
    new = np.ones(points.shape, dtype=bool)
    new[:, 1:] = ordered[:, 1:] != ordered[:, :-1]
    start = np.maximum.accumulate(np.where(new, pos, 0), axis=1)
    ranks = np.empty(points.shape, dtype=np.int64)
    np.put_along_axis(ranks, order, start + 1, axis=1)
    return ranks


def real_entries(events: list[Event], player_index: dict[int, int]) -> pd.DataFrame:
    """One row per (event, player): real points on the simulator's table and when they enter."""
    rows = []
    for e in events:
        entry = e.points_entry_date
        for pid, pts in real_points(e).items():
            rows.append({"event": e.index, "season": e.season, "player_id": pid,
                         "player": player_index.get(pid, -1), "points": pts, "entry": entry})
    return pd.DataFrame(rows)


def ledger_at(date: pd.Timestamp, entries: pd.DataFrame, n_players: int) -> np.ndarray:
    """(N,) points counting on `date`: entered on or before it and less than 52 weeks ago."""
    live = entries[(entries["entry"] <= date) & (entries["entry"] > date - pd.Timedelta(days=364))]
    live = live[live["player"] >= 0]
    return np.bincount(live["player"].to_numpy(np.int64), weights=live["points"].to_numpy(np.float64),
                       minlength=n_players).astype(np.int64)
