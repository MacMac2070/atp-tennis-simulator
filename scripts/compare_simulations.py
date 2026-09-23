#!/usr/bin/env python3
"""Compare season simulations run with different models, and write the run READMEs.

    python scripts/compare_simulations.py --season 2025 \\
        artifacts/simulations/run0_baseline artifacts/simulations/run1_season_delta

Refuses to compare runs that differ in anything but the model (season, seed, simulation
count, code commit), because then a difference in the numbers would not be the model's.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.report import LIMITATIONS


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _table(header: list[str], rows: list[list]) -> list[str]:
    align = ["---" if i == 0 else "---:" for i in range(len(header))]
    return ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"] + [
        "| " + " | ".join(str(v) for v in r) + " |" for r in rows
    ]


def load_run(run_dir: str, season: int) -> dict:
    d = os.path.join(run_dir, f"season_{season}")
    with open(os.path.join(d, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(d, "metrics.json")) as f:
        metrics = json.load(f)
    return {
        "dir": run_dir, "name": os.path.basename(os.path.normpath(run_dir)), "config": config, "metrics": metrics,
        "tournaments": pd.read_csv(os.path.join(d, "tournaments.csv")),
        "year_end": pd.read_csv(os.path.join(d, "rankings_year_end.csv")),
        "weekly": pd.read_csv(os.path.join(d, "rankings_weekly.csv")),
    }


def check_comparable(runs: list[dict]) -> None:
    keys = ("season", "n_sims", "seed", "events", "entrants", "matches_scored")
    for k in keys:
        vals = {r["config"][k] for r in runs}
        if len(vals) > 1:
            sys.exit(f"Runs differ in {k} ({vals}); only the model may differ.")
    commits = {r["config"]["code"]["commit"] for r in runs}
    if len(commits) > 1:
        sys.exit(f"Runs were made from different code commits {commits}.")
    if len({r["config"]["model_sha256"] for r in runs}) != len(runs):
        sys.exit("Two runs used the same model file.")


def compare_note(runs: list[dict], season: int) -> str:
    c0 = runs[0]["config"]
    names = [r["name"] for r in runs]
    L = [f"# {season} season simulations: " + " vs ".join(names) + " vs actual", "",
         f"Same {c0['events']} events, real draws, form cards, seed {c0['seed']} and {c0['n_sims']:,} simulated "
         f"seasons for every run; only the serve model differs (common random numbers: each match slot "
         f"draws the same random number in every run). Code commit `{c0['code']['commit'][:10]}`"
         + (" plus uncommitted changes" if c0["code"]["code_uncommitted"] else "") + ".", ""]
    L += _table(["Run", "Model", "Trained through", "sha256"],
                [[r["name"], f"`{r['config']['model']}`", r["config"]["train_through"],
                  f"`{r['config']['model_sha256'][:12]}`"] for r in runs])

    L += ["", "## Match level", "",
          f"{c0['matches_scored']:,} real matches of the simulated events (walkovers dropped), each scored with "
          "the model's pre-event probability for the real winner. No simulation involved: the cleanest "
          "test of the serve model. A coin flip scores log loss 0.6931.", ""]
    rows = []
    for r in runs:
        m = r["metrics"]["match"]
        rows.append([r["name"], _pct(m["accuracy"]), f"{m['log_loss']:.4f}", f"{m['brier']:.4f}"])
    hr = runs[0]["metrics"]["match"]["higher_rank_accuracy"]
    rows.append(["Higher-ranked player wins", _pct(hr), "", ""])
    L += _table(["", "Accuracy", "Log loss", "Brier"], rows)
    L += ["", "Log loss by surface and category:", ""]
    groups = [("match_by_surface", s) for s in runs[0]["metrics"]["match_by_surface"]] + \
             [("match_by_category", c) for c in runs[0]["metrics"]["match_by_category"]]
    L += _table(["Group", "Matches"] + names,
                [[g, f"{runs[0]['metrics'][kind][g]['n']:,}"] +
                 [f"{r['metrics'][kind][g]['log_loss']:.4f}" for r in runs] for kind, g in groups])

    L += ["", "## Tournament level", ""]
    L += _table(["", "Real champion was the favourite", "Real champion in top 3", "Mean P(real champion)",
                 "Title log loss"],
                [[r["name"], f"{r['metrics']['tournament']['actual_champion_is_modal']} of {r['metrics']['tournament']['events']}",
                  f"{r['metrics']['tournament']['actual_champion_in_top3']}",
                  _pct(r["metrics"]["tournament"]["mean_p_actual_champion"]),
                  f"{r['metrics']['tournament']['title_log_loss']:.3f}"] for r in runs])
    big = runs[0]["tournaments"]
    big = big[big["category"].isin(["G", "M", "F"])]
    rows = []
    for t in big.itertuples(index=False):
        row = [t.name, t.actual_champion]
        for r in runs:
            x = r["tournaments"].set_index("tourney_id").loc[t.tourney_id]
            row += [_pct(x["p_actual_champion"]), f"{x['modal_champion']} ({_pct(x['p_modal_champion'])})"]
        rows.append(row)
    L += ["", "Slams, Masters and the ATP Finals: simulated chance of the real champion, and each run's favourite.", ""]
    L += _table(["Event", "Real champion"] + [h for n in names for h in (f"{n} chance", f"{n} favourite")], rows)

    L += ["", "## Year end", "",
          "Same-table actual = the real 2025 results of the same events scored with the simulator's points "
          "table; official = ATP ranking of " + c0["year_end_ranking_date"] + ". Real top 10 by same-table points.", ""]
    ye0 = runs[0]["year_end"].sort_values("actual_points_same_table", ascending=False).head(10)
    rows = []
    for p in ye0.itertuples(index=False):
        row = [p.name, f"{int(p.actual_points_same_table):,}",
               f"#{int(p.official_rank)}" if pd.notna(p.official_rank) else ""]
        for r in runs:
            x = r["year_end"].set_index("player_id").loc[p.player_id]
            row += [f"{x['mean_points']:,.0f}", f"{x['mean_rank']:.1f}", _pct(x["p_top1"])]
        rows.append(row)
    L += _table(["Player", "Same-table actual", "Official"] +
                [h for n in names for h in (f"{n} mean pts", f"{n} mean rank", f"{n} P(#1)")], rows)
    L += [""]
    L += _table(["", "Most likely #1", "P(real #1)", "Top-10 overlap (same-table)", "Top-10 overlap (official)",
                 "Spearman, official top 50", "Rank error, official top 20"],
                [[r["name"], f"{r['metrics']['season']['modal_no1']} ({_pct(r['metrics']['season']['modal_no1_p'])})",
                  _pct(r["metrics"]["season"]["p_actual_no1"]),
                  f"{r['metrics']['season']['top10_overlap_same_table']} of 10",
                  f"{r['metrics']['season']['top10_overlap_official']} of 10",
                  f"{r['metrics']['season']['spearman_official_top50']:.3f}",
                  f"{r['metrics']['season']['rank_mae_same_table_top20']:.1f}"] for r in runs])

    L += ["", "## Rankings through the season", "",
          "Mean absolute gap between simulated mean rank and official rank, official top 20, last ranking "
          "of each month. The same-table column is the floor set by the simplified ranking rules alone.", ""]
    monthly = []
    for r in runs:
        w = r["weekly"][r["weekly"]["official_rank"] <= 20].copy()
        w["ranking_date"] = pd.to_datetime(w["ranking_date"])
        w["sim"] = (w["mean_rank"] - w["official_rank"]).abs()
        w["same"] = (w["same_table_rank"] - w["official_rank"]).abs()
        g = w.groupby("ranking_date")[["sim", "same"]].mean().resample("MS").last()
        monthly.append(g)
    rows = [[d.strftime("%b %Y")] + [f"{m.loc[d, 'sim']:.1f}" for m in monthly] + [f"{monthly[0].loc[d, 'same']:.1f}"]
            for d in monthly[0].index]
    L += _table(["Month"] + names + ["Same-table"], rows)
    L += ["", "## Limitations (all runs)", ""] + [f"- {x}" for x in LIMITATIONS]
    L += ["", "## Reproduce", "", "```bash"]
    for r in runs:
        L.append(f"python scripts/simulate_season.py --model {r['config']['model']} --season {season} "
                 f"--n-sims {c0['n_sims']} --seed {c0['seed']} --out {os.path.relpath(r['dir'], ROOT)}/season_{season}/")
    L += [f"python scripts/compare_simulations.py --season {season} "
          + " ".join(os.path.relpath(r["dir"], ROOT) for r in runs), "```", ""]
    return "\n".join(L)


def run_readme(r: dict, season: int, note_path: str) -> str:
    c, m = r["config"], r["metrics"]
    mm, tm, sm = m["match"], m["tournament"], m["season"]
    return "\n".join([
        f"# Simulations: {r['name']}", "",
        f"Weights: `{c['model']}` (trained through {c['train_through']}, sha256 `{c['model_sha256'][:12]}`).", "",
        "| Folder | Season | Seasons simulated | Seed | Status |", "|---|---|---:|---:|---|",
        f"| `season_{season}/` | {season} file year | {c['n_sims']:,} | {c['seed']} | Done |", "",
        "## Headline", "",
        f"- Match level: accuracy {_pct(mm['accuracy'])}, log loss {mm['log_loss']:.4f}, Brier {mm['brier']:.4f} "
        f"on {mm['n']:,} real matches (higher-ranked player wins {_pct(mm['higher_rank_accuracy'])}).",
        f"- Titles: real champion was the favourite in {tm['actual_champion_is_modal']} of {tm['events']} events, "
        f"in the top three in {tm['actual_champion_in_top3']}.",
        f"- Year end: most likely #1 {sm['modal_no1']} ({_pct(sm['modal_no1_p'])}); the real #1 "
        f"{sm['actual_no1_same_table']} finished #1 in {_pct(sm['p_actual_no1'])} of simulated seasons.", "",
        f"Full write-up: `season_{season}/summary.md`. Comparison with the other runs: `{note_path}`.", "",
        "## Reproduce", "", "```bash",
        f"python scripts/simulate_season.py --model {c['model']} --season {season} --n-sims {c['n_sims']} "
        f"--seed {c['seed']} --out {os.path.relpath(r['dir'], ROOT)}/season_{season}/",
        "```", "",
        "Other runs use the same season, seed and simulation count, so only the model differs.", ""])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+", help="run folders under artifacts/simulations/")
    p.add_argument("--season", type=int, default=2025)
    p.add_argument("--out", default=None, help="default verification/reports/simulations_<season>.md")
    args = p.parse_args()
    if len(args.runs) < 2:
        sys.exit("Give at least two run folders to compare.")
    runs = [load_run(os.path.abspath(d), args.season) for d in args.runs]
    check_comparable(runs)
    out = args.out or os.path.join(ROOT, "verification", "reports", f"simulations_{args.season}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(compare_note(runs, args.season))
    note_rel = os.path.relpath(out, ROOT)
    for r in runs:
        with open(os.path.join(r["dir"], "README.md"), "w") as f:
            f.write(run_readme(r, args.season, note_rel))
    print(f"Wrote {note_rel} and {len(runs)} run READMEs.")


if __name__ == "__main__":
    main()
