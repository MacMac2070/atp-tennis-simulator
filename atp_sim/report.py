"""Score a simulated season against the real one and write the output files.

Three levels, the same for every run:

- Match: every real match of the simulated events (walkovers dropped) gets the model's
  probability for the real winner, from the cards on the morning of the event. No
  simulation is involved, so this is the cleanest test of the serve model.
- Tournament: how much of the simulated title distribution sat on the real champion.
- Season: the year-end points distribution against the real 2025 results scored with the
  same points table ("same-table actual") and against the official ranking. The first
  gap is simulator error; the rest is the ranking rules this simulator does not model.

Every file comes from the same code and template, so two run folders differ only in numbers.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from .draws import NO_RANK, WALKOVER_RE
from .season import PreparedEvent, SeasonSims, competition_ranks, ledger_at

__all__ = [
    "CATEGORY_NAMES", "DISPLAY_NAMES", "LIMITATIONS", "display_name", "match_metrics", "match_table", "official_rankings", "season_metrics",
    "tournament_table", "weekly_table", "write_run", "year_end_table",
]

# Raw archive names that read wrongly in a report. The CSV files keep the raw names.
DISPLAY_NAMES = {"Us Open": "US Open", "Tour Finals": "ATP Finals"}
CATEGORY_NAMES = {"G": "Grand Slam", "M": "Masters 1000", "500": "ATP 500", "250": "ATP 250", "F": "ATP Finals"}


def display_name(name: str) -> str:
    return DISPLAY_NAMES.get(name, name)


LIMITATIONS = [
    "Form cards are frozen at each event's real start date and built from real results only; "
    "simulated results never change later cards. Tournaments are linked through ranking points "
    "alone, so this is an A/B test of the serve model, not a closed fantasy season.",
    "Every real entrant plays and nobody else does: injuries, withdrawals and retirements are not "
    "simulated, and every match is played to a finish. Real walkovers are simulated as matches.",
    "Ranking rules are simplified: every simulated event counts in full. No best-19 rule, "
    "mandatory-event zero-pointers or protected rankings, and no points from Challengers, "
    "qualifying or the United Cup. Year-end figures are therefore compared with the "
    "same-table actual race first and the official ranking second.",
    "ATP Finals: the real 2025 groups are fixed (qualification is not simulated). Groups are "
    "ordered by wins, head-to-head and percentage of sets won; percentage of games won is not simulated, so an unbroken "
    "three-way tie falls to the ranking at entry.",
    "Points enter the ledger on the Monday after the event's estimated last day and drop 52 weeks "
    "later. The 2024 part of the ledger is the real 2024 results scored with the same table.",
    "Team events (Davis Cup, United Cup, Laver Cup) and the Next Gen Finals are not simulated and "
    "are left out of the actual side too.",
]


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def official_rankings(data_dir: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Official ATP rankings between two dates: ranking_date, rank, player_id, points.

    The file lists a few players twice on one date (e.g. 208147 at 860 and 1658 on
    29 December 2025). The better rank is kept; the number dropped is in attrs["duplicates_dropped"].
    """
    path = os.path.join(data_dir, "atp_rankings_20s.csv")
    r = pd.read_csv(path)
    r["ranking_date"] = pd.to_datetime(r["ranking_date"].astype(str), format="%Y%m%d")
    r = r[(r["ranking_date"] >= start) & (r["ranking_date"] <= end)]
    r = r.rename(columns={"player": "player_id"})[["ranking_date", "rank", "player_id", "points"]]
    r = r.sort_values(["ranking_date", "rank"], kind="mergesort")
    dup = r.duplicated(["ranking_date", "player_id"], keep="first")
    out = r[~dup].reset_index(drop=True)
    out.attrs["duplicates_dropped"] = int(dup.sum())
    return out


# ---------------------------------------------------------------------------------- match

def match_table(prepared: list[PreparedEvent], names: dict[int, str]) -> pd.DataFrame:
    rows = []
    for pe in prepared:
        e = pe.event
        idx = {int(p): i for i, p in enumerate(e.entrants)}
        m = e.matches[~e.matches["score"].astype(str).str.contains(WALKOVER_RE, case=False, regex=True)]
        for r in m.itertuples(index=False):
            w, l = idx[int(r.winner_id)], idx[int(r.loser_id)]
            p = float(pe.p_match[w, l])
            wr = int(r.winner_rank) if pd.notna(r.winner_rank) else NO_RANK
            lr = int(r.loser_rank) if pd.notna(r.loser_rank) else NO_RANK
            rows.append({
                "match_id": f"{e.tourney_id}#{int(r.match_num)}", "date": e.date.date().isoformat(),
                "tourney": e.name, "category": e.category, "round": r.round, "surface": e.surface,
                "best_of": e.best_of, "winner_id": int(r.winner_id), "winner_name": names.get(int(r.winner_id), ""),
                "loser_id": int(r.loser_id), "loser_name": names.get(int(r.loser_id), ""),
                "winner_rank": wr if wr != NO_RANK else None, "loser_rank": lr if lr != NO_RANK else None,
                "p_serve_winner": float(pe.p_serve[w, l]), "p_serve_loser": float(pe.p_serve[l, w]),
                "p_winner": p, "correct": 1.0 if p > 0.5 else 0.5 if p == 0.5 else 0.0,
                "log_loss": -np.log(max(p, 1e-12)), "brier": (1.0 - p) ** 2,
                "higher_rank_won": 1.0 if wr < lr else 0.5 if wr == lr else 0.0,
                "retired": "RET" in str(r.score).upper(),
            })
    return pd.DataFrame(rows)


def match_metrics(mt: pd.DataFrame) -> dict:
    return {
        "n": int(len(mt)),
        "accuracy": float(mt["correct"].mean()),
        "log_loss": float(mt["log_loss"].mean()),
        "brier": float(mt["brier"].mean()),
        "higher_rank_accuracy": float(mt["higher_rank_won"].mean()),
    }


def _calibration(mt: pd.DataFrame) -> pd.DataFrame:
    """Favourite's predicted chance against how often the favourite won, in 5 bins."""
    fav = np.maximum(mt["p_winner"], 1 - mt["p_winner"])
    fav_won = (mt["p_winner"] >= 0.5).astype(float)
    bins = pd.cut(fav, [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], include_lowest=True)
    g = pd.DataFrame({"bin": bins, "fav": fav, "won": fav_won}).groupby("bin", observed=False)
    return g.agg(n=("won", "size"), predicted=("fav", "mean"), actual=("won", "mean")).reset_index()


# ----------------------------------------------------------------------------- tournament

def tournament_table(prepared: list[PreparedEvent], sims: SeasonSims, names: dict[int, str]) -> pd.DataFrame:
    pos = {int(p): i for i, p in enumerate(sims.player_ids)}
    rows = []
    for k, pe in enumerate(prepared):
        e = pe.event
        counts = np.bincount(sims.champions[k], minlength=len(sims.player_ids)) / sims.n_sims
        champ = e.finals.real_champion if e.finals is not None else e.knockout.real_winner[-1]
        actual_pid = int(e.entrants[champ])
        modal = int(np.argmax(counts))
        p_actual = float(counts[pos[actual_pid]])
        rows.append({
            "tourney_id": e.tourney_id, "name": e.name, "date": e.date.date().isoformat(),
            "category": e.category, "surface": e.surface, "draw_size": e.draw_size,
            "actual_champion_id": actual_pid, "actual_champion": names.get(actual_pid, ""),
            "p_actual_champion": p_actual,
            "actual_champion_position": int((counts > p_actual).sum()) + 1,
            "modal_champion": names.get(int(sims.player_ids[modal]), ""),
            "p_modal_champion": float(counts[modal]),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------- season

def year_end_table(
    sims: SeasonSims,
    actual_points: np.ndarray,
    official: pd.DataFrame,
    names: dict[int, str],
) -> pd.DataFrame:
    """One row per player who scored in the simulation or in reality, by mean points.

    `official` is the official ranking of one date (the year-end Monday).
    """
    ranks = competition_ranks(sims.totals)
    actual_rank = competition_ranks(actual_points[None, :])[0]
    off = official.set_index("player_id")
    tot = sims.totals
    df = pd.DataFrame({
        "player_id": sims.player_ids,
        "name": [names.get(int(p), "") for p in sims.player_ids],
        "mean_points": tot.mean(axis=0),
        "sd_points": tot.std(axis=0),
        "p05_points": np.percentile(tot, 5, axis=0),
        "p95_points": np.percentile(tot, 95, axis=0),
        "mean_rank": ranks.mean(axis=0),
        "median_rank": np.median(ranks, axis=0),
        "p_top1": (ranks == 1).mean(axis=0),
        "p_top4": (ranks <= 4).mean(axis=0),
        "p_top8": (ranks <= 8).mean(axis=0),
        "p_top10": (ranks <= 10).mean(axis=0),
        "actual_points_same_table": actual_points,
        "actual_rank_same_table": actual_rank,
        "official_rank": off["rank"].reindex(sims.player_ids).to_numpy(),
        "official_points": off["points"].reindex(sims.player_ids).to_numpy(),
    })
    df = df[(df["mean_points"] > 0) | (df["actual_points_same_table"] > 0)]
    return df.sort_values(["mean_points", "actual_points_same_table"], ascending=False).reset_index(drop=True)


def _spearman(a: pd.Series, b: pd.Series) -> float:
    return float(np.corrcoef(a.rank(), b.rank())[0, 1])


def season_metrics(ye: pd.DataFrame) -> dict:
    by_same = ye.sort_values("actual_points_same_table", ascending=False)
    off_top = ye[ye["official_rank"].notna()].sort_values("official_rank")
    sim_top10 = set(ye["player_id"].head(10))
    top50 = off_top[off_top["official_rank"] <= 50]
    top20 = off_top[off_top["official_rank"] <= 20]
    modal = ye.loc[ye["p_top1"].idxmax()]
    actual1 = by_same.iloc[0]
    return {
        "modal_no1": modal["name"], "modal_no1_p": float(modal["p_top1"]),
        "mean_points_no1": ye.iloc[0]["name"],
        "actual_no1_same_table": actual1["name"], "p_actual_no1": float(actual1["p_top1"]),
        "top10_overlap_same_table": len(sim_top10 & set(by_same["player_id"].head(10))),
        "top10_overlap_official": len(sim_top10 & set(off_top["player_id"].head(10))),
        "spearman_official_top50": _spearman(top50["mean_points"], top50["actual_points_same_table"]),
        "rank_mae_official_top20": float((top20["mean_rank"] - top20["official_rank"]).abs().mean()),
        "rank_mae_same_table_top20": float((top20["mean_rank"] - top20["actual_rank_same_table"]).abs().mean()),
        "points_mae_same_table_top20": float((top20["mean_points"] - top20["actual_points_same_table"]).abs().mean()),
    }


def weekly_table(
    prepared: list[PreparedEvent],
    sims: SeasonSims,
    base_entries: pd.DataFrame,
    real_entries_now: pd.DataFrame,
    official: pd.DataFrame,
    names: dict[int, str],
    track_top: int = 30,
) -> pd.DataFrame:
    """Simulated 52-week ranking on every official ranking Monday of the season.

    `base_entries` are the previous season's real points, `real_entries_now` this season's
    real points (both on the simulator's table), used for the same-table actual ranking.
    """
    n = len(sims.player_ids)
    pos = {int(p): i for i, p in enumerate(sims.player_ids)}
    by_entry = sorted(range(len(prepared)), key=lambda k: prepared[k].event.points_entry_date)
    running = np.zeros((sims.n_sims, n), dtype=np.int32)
    k = 0
    rows = []
    # The pointer walk over `by_entry` needs the dates in ascending order: sort explicitly.
    for date, off in official.sort_values("ranking_date").groupby("ranking_date", sort=False):
        while k < len(by_entry) and prepared[by_entry[k]].event.points_entry_date <= date:
            running[:, prepared[by_entry[k]].player_idx] += sims.event_points[by_entry[k]]
            k += 1
        base = ledger_at(date, base_entries, n)
        ranks = competition_ranks(running + base[None, :])
        same = base + ledger_at(date, real_entries_now, n)
        same_rank = competition_ranks(same[None, :])[0]
        for r in off.sort_values("rank").head(track_top).itertuples(index=False):
            i = pos.get(int(r.player_id))
            row = {"ranking_date": date.date().isoformat(), "player_id": int(r.player_id),
                   "name": names.get(int(r.player_id), ""), "official_rank": int(r.rank),
                   "official_points": int(r.points)}
            if i is None:  # official top 30 but no tour-level main-draw entry in either season
                row.update({"same_table_rank": np.nan, "same_table_points": 0, "mean_rank": np.nan,
                            "median_rank": np.nan, "mean_points": 0.0, "p_top10": 0.0})
            else:
                row.update({"same_table_rank": int(same_rank[i]), "same_table_points": int(same[i]),
                            "mean_rank": float(ranks[:, i].mean()), "median_rank": float(np.median(ranks[:, i])),
                            "mean_points": float((running[:, i] + base[i]).mean()),
                            "p_top10": float((ranks[:, i] <= 10).mean())})
            rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------- writing

def _fmt(df: pd.DataFrame, dp4_cols: list[str], int_cols: list[str]) -> pd.DataFrame:
    """Fixed number formats: probabilities and scores to 4 dp, points and ranks as integers."""
    out = df.copy()
    for c in dp4_cols:
        if c in out:
            out[c] = pd.to_numeric(out[c]).round(4)
    for c in int_cols:
        if c in out:
            out[c] = pd.to_numeric(out[c]).round().astype("Int64")
    return out


def _md_table(header: list[str], rows: list[list]) -> list[str]:
    align = ["---" if i == 0 else "---:" for i in range(len(header))]
    return ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"] + [
        "| " + " | ".join(str(v) for v in r) + " |" for r in rows
    ]


def write_run(
    out_dir: str,
    config: dict,
    mt: pd.DataFrame,
    tt: pd.DataFrame,
    ye: pd.DataFrame,
    wk: pd.DataFrame,
) -> dict:
    """Write config.json, metrics.json, summary.md and the four csv files. Returns metrics."""
    os.makedirs(out_dir, exist_ok=True)
    mm = match_metrics(mt)
    sm = season_metrics(ye)
    top20 = wk[wk["official_rank"] <= 20]
    weekly_mae = pd.DataFrame({
        "ranking_date": top20["ranking_date"],
        "sim_vs_official": (top20["mean_rank"] - top20["official_rank"]).abs(),
        "same_table_vs_official": (top20["same_table_rank"] - top20["official_rank"]).abs(),
    }).groupby("ranking_date").mean()
    tm = {
        "events": int(len(tt)),
        "actual_champion_is_modal": int((tt["actual_champion_position"] == 1).sum()),
        "actual_champion_in_top3": int((tt["actual_champion_position"] <= 3).sum()),
        "mean_p_actual_champion": float(tt["p_actual_champion"].mean()),
        "title_log_loss": float(-np.log(tt["p_actual_champion"].clip(lower=1.0 / config["n_sims"])).mean()),
    }
    metrics = {"match": mm, "match_by_surface": {s: match_metrics(g) for s, g in mt.groupby("surface")},
               "match_by_category": {c: match_metrics(g) for c, g in mt.groupby("category")},
               "tournament": tm, "season": sm,
               "weekly_rank_mae_top20_mean": float(weekly_mae["sim_vs_official"].mean())}

    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2, default=str)
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    _fmt(mt, ["p_serve_winner", "p_serve_loser", "p_winner", "brier", "log_loss"],
         ["winner_rank", "loser_rank"]).to_csv(os.path.join(out_dir, "matches.csv"), index=False)
    _fmt(tt, ["p_actual_champion", "p_modal_champion"], []).to_csv(
        os.path.join(out_dir, "tournaments.csv"), index=False)
    _fmt(ye, ["p_top1", "p_top4", "p_top8", "p_top10", "mean_rank", "median_rank"],
         ["mean_points", "sd_points", "p05_points", "p95_points", "official_rank", "official_points"]).to_csv(
        os.path.join(out_dir, "rankings_year_end.csv"), index=False)
    _fmt(wk, ["p_top10", "mean_rank", "median_rank"], ["mean_points", "same_table_rank"]).to_csv(
        os.path.join(out_dir, "rankings_weekly.csv"), index=False)

    with open(os.path.join(out_dir, "summary.md"), "w") as f:
        f.write(_summary(config, metrics, mt, tt, ye, weekly_mae))
    return metrics


def _summary(config, metrics, mt, tt, ye, weekly_mae) -> str:
    mm, tm, sm = metrics["match"], metrics["tournament"], metrics["season"]
    L = [f"# Season {config['season']} simulation: `{config['run']}`", "",
         f"Model `{config['model']}` (trained through {config['train_through']}). "
         f"{config['n_sims']:,} simulated seasons, seed {config['seed']}. "
         f"Season = the {config['season']} file year, events dated {config['first_event']} to {config['last_event']}.", "",
         "## What was simulated", "",
         f"{config['events']} events with their real draws: " + ", ".join(
             f"{v} {k}" for k, v in config["events_by_category"].items()) + ". "
         f"{config['entrants']:,} entries by {config['players_2025']} players. "
         f"Left out: {config['excluded_summary']}.", "",
         "## Match level", "",
         "Every real match of the simulated events, walkovers dropped, scored with the model's pre-event "
         "probability for the real winner. No simulation involved.", ""]

    def mrow(label, v):
        return [label, f"{v['n']:,}", _pct(v["accuracy"]), f"{v['log_loss']:.4f}", f"{v['brier']:.4f}",
                _pct(v["higher_rank_accuracy"])]

    L += _md_table(["", "Matches", "Accuracy", "Log loss", "Brier", "Higher-ranked player wins"],
                   [mrow("All", mm)]
                   + [mrow(k, v) for k, v in metrics["match_by_surface"].items()]
                   + [mrow(CATEGORY_NAMES.get(k, k), v) for k, v in metrics["match_by_category"].items()])
    L += ["", "A coin flip scores a log loss of 0.6931. Calibration, the favourite's predicted chance against "
          "how often the favourite won:", ""]
    L += _md_table(["Favourite's chance", "Matches", "Predicted", "Won"],
                   [[f"{max(r.bin.left, 0.5):.0%} to {r.bin.right:.0%}", f"{r.n:,}", _pct(r.predicted) if r.n else "", _pct(r.actual) if r.n else ""]
                    for r in _calibration(mt).itertuples(index=False)])
    L += ["", "## Tournament level", "",
          f"The real champion was the simulation's favourite in {tm['actual_champion_is_modal']} of {tm['events']} events "
          f"and in its top three in {tm['actual_champion_in_top3']}. The mean simulated chance of the real champion was "
          f"{_pct(tm['mean_p_actual_champion'])}.", ""]
    big = tt[tt["category"].isin(["G", "M", "F"])]
    L += _md_table(["Event", "Real champion", "Sim. chance", "Position", "Sim. favourite", "Chance"],
                   [[display_name(r.name), r.actual_champion, _pct(r.p_actual_champion), r.actual_champion_position,
                     r.modal_champion, _pct(r.p_modal_champion)] for r in big.itertuples(index=False)])
    L += ["", "Grand Slams, Masters 1000 and the ATP Finals are shown; every event is in `tournaments.csv`.", "",
          "## Year-end top 10", "",
          "Sorted by mean simulated points. Same-table actual = the real 2025 results of the same events, "
          "scored with the simulator's points table. Official = ATP ranking of 2025-12-29.", ""]
    L += _md_table(["Player", "Mean pts", "90% range", "Mean rank", "P(#1)", "P(top 10)",
                    "Same-table actual", "Official"],
                   [[r.name, f"{r.mean_points:,.0f}", f"{r.p05_points:,.0f} to {r.p95_points:,.0f}",
                     f"{r.mean_rank:.1f}", _pct(r.p_top1), _pct(r.p_top10),
                     f"{int(r.actual_points_same_table):,} (#{int(r.actual_rank_same_table)})",
                     f"{int(r.official_points):,} (#{int(r.official_rank)})" if pd.notna(r.official_rank) else ""]
                    for r in ye.head(10).itertuples(index=False)])
    L += ["", f"- Most likely #1: **{sm['modal_no1']}** ({_pct(sm['modal_no1_p'])}). "
          f"Real same-table #1: **{sm['actual_no1_same_table']}**, simulated P(#1) {_pct(sm['p_actual_no1'])}.",
          f"- Top-10 overlap with same-table actual: {sm['top10_overlap_same_table']} of 10; "
          f"with the official top 10: {sm['top10_overlap_official']} of 10.",
          f"- Official top 50: Spearman between mean simulated points and same-table points "
          f"{sm['spearman_official_top50']:.3f}.",
          f"- Official top 20: mean |simulated rank - same-table rank| {sm['rank_mae_same_table_top20']:.1f}; "
          f"against the official rank {sm['rank_mae_official_top20']:.1f}; "
          f"mean |points gap| {sm['points_mae_same_table_top20']:,.0f}.", "",
          "## Rankings through the season", "",
          "52-week ledger on each official ranking Monday (2024 real results, then simulated 2025 results). "
          "Mean absolute rank error for the official top 20, taken at the last ranking of each month: "
          "simulated mean rank against the official rank, and, for scale, the same-table actual rank "
          "against the official rank (the part the simplified rules alone explain).", ""]
    months = weekly_mae.copy()
    months.index = pd.to_datetime(months.index)
    monthly = months.resample("MS").last()
    L += _md_table(["Month", "Simulated vs official", "Same-table vs official"],
                   [[d.strftime("%b %Y"), f"{r.sim_vs_official:.1f}", f"{r.same_table_vs_official:.1f}"]
                    for d, r in monthly.iterrows()])
    top20 = ye[ye["official_rank"] <= 20].copy()
    top20["gap"] = top20["mean_points"] - top20["actual_points_same_table"]
    over = top20.sort_values("gap", ascending=False).head(4)
    under = top20.sort_values("gap").head(4)
    L += ["", "## Where it misses", "",
          "Official top 20, largest gaps between mean simulated points and same-table actual points.", ""]
    L += _md_table(["Player", "Mean simulated", "Same-table actual", "Gap"],
                   [[r.name, f"{r.mean_points:,.0f}", f"{int(r.actual_points_same_table):,}", f"{r.gap:+,.0f}"]
                    for r in pd.concat([over, under]).drop_duplicates("player_id").itertuples(index=False)])
    L += ["", "## Limitations", ""] + [f"- {x}" for x in LIMITATIONS]
    L += ["", "## Files", "",
          "| File | Contents |", "|---|---|",
          "| `config.json` | Season, seed, simulation count, model path and hash, code commit, event counts |",
          "| `metrics.json` | Every headline number on this page, machine-readable |",
          "| `matches.csv` | One row per real match: both serve probabilities, P(real winner), log loss and Brier score |",
          "| `tournaments.csv` | One row per event: real champion, simulated chance, simulated favourite |",
          "| `rankings_year_end.csv` | One row per player: simulated points and rank distribution, same-table and official |",
          "| `rankings_weekly.csv` | Official top 30 on each ranking Monday: simulated, same-table and official rank |",
          ""]
    return "\n".join(L)
