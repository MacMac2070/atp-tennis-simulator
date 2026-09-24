#!/usr/bin/env python3
"""Simulate one season with one frozen serve model (DESIGN.md §10).

    python scripts/simulate_season.py --model artifacts/models/run0_baseline/model.pt \\
        --season 2025 --n-sims 10000 --seed 42 --out artifacts/simulations/run0_baseline/season_2025/

Run it once per model with the same --season, --n-sims and --seed. The events, draws, form
cards and random numbers are then identical, so any difference between the two output
folders comes from the model alone.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import platform
import subprocess
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.data import DATA_DIR, LAST_SEASON, clean_players_dob, load_matches, load_players, prepare_matches
from atp_sim.draws import load_season_events
from atp_sim.model import SurfaceBundle
from atp_sim.report import match_table, official_rankings, tournament_table, weekly_table, write_run, year_end_table
from atp_sim.season import entrant_cards, prepare_events, real_entries, simulate_season

CATEGORY_LABELS = {"G": "Grand Slams", "M": "Masters 1000", "500": "ATP 500", "250": "ATP 250", "F": "ATP Finals"}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state() -> dict:
    def run(*cmd: str) -> str:
        try:
            return subprocess.run(["git", *cmd], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""
    dirty = run("status", "--porcelain", "--", "atp_sim", "scripts")
    return {"commit": run("rev-parse", "HEAD") or "unknown", "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "code_uncommitted": bool(dirty)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="frozen weights, e.g. artifacts/models/run0_baseline/model.pt")
    p.add_argument("--season", type=int, default=2025)
    p.add_argument("--n-sims", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", required=True)
    p.add_argument("--data-dir", default=DATA_DIR)
    p.add_argument("--run", default=None, help="run name for the summary; default is the model's folder name")
    p.add_argument("--allow-working-copy", action="store_true", help="permit runs/model.pt")
    args = p.parse_args()

    model_path = os.path.abspath(args.model)
    if model_path == os.path.join(ROOT, "runs", "model.pt") and not args.allow_working_copy:
        sys.exit("runs/model.pt is a working copy. Simulate a frozen model under artifacts/models/ "
                 "or pass --allow-working-copy.")
    out = os.path.abspath(args.out)
    if out.startswith(os.path.join(ROOT, "artifacts", "models") + os.sep):
        sys.exit("Refusing to write into artifacts/models/: frozen model folders are read-only.")
    if args.n_sims < 1:
        sys.exit("--n-sims must be at least 1")
    bundle = SurfaceBundle.load(model_path)
    if bundle.train_through is None or bundle.train_through >= args.season:
        sys.exit(f"The model was trained through {bundle.train_through}; season {args.season} is not unseen.")
    model_hash_before = sha256(model_path)

    t0 = time.time()
    valid, _ = prepare_matches(load_matches(1991, LAST_SEASON, data_dir=args.data_dir))
    players = clean_players_dob(load_players(args.data_dir), valid)
    events, excluded = load_season_events(args.season, args.data_dir)
    base_events, _ = load_season_events(args.season - 1, args.data_dir)
    cards = entrant_cards(events, valid, players)

    # Season entrants first, then players who only hold points from the season before.
    ids = list(dict.fromkeys(int(pid) for e in events + base_events for pid in e.entrants))
    player_ids = np.array(ids, dtype=np.int64)
    pindex = {pid: i for i, pid in enumerate(ids)}
    names = {int(pid): " ".join(str(x) for x in (r.name_first, r.name_last) if pd.notna(x))
             for pid, r in players[["name_first", "name_last"]].iterrows()}

    prepared = prepare_events(events, bundle, cards, pindex)
    t1 = time.time()
    sims = simulate_season(prepared, player_ids, args.n_sims, args.seed)
    t2 = time.time()

    base_entries = real_entries(base_events, pindex)
    now_entries = real_entries(events, pindex)
    actual = np.bincount(now_entries["player"].to_numpy(np.int64),
                         weights=now_entries["points"].to_numpy(np.float64), minlength=len(ids)).astype(np.int64)
    official = official_rankings(args.data_dir, pd.Timestamp(f"{args.season}-01-01"),
                                 pd.Timestamp(f"{args.season}-12-31"))
    if official.empty:
        sys.exit(f"No official rankings dated {args.season} in {args.data_dir}.")
    year_end = official[official["ranking_date"] == official["ranking_date"].max()]

    mt = match_table(prepared, names)
    tt = tournament_table(prepared, sims, names)
    ye = year_end_table(sims, actual, year_end, names)
    wk = weekly_table(prepared, sims, base_entries, now_entries, official, names)

    cats = Counter(e.category for e in events)
    n_team = int((excluded["reason"] == "team event").sum()) if not excluded.empty else 0
    others = excluded[excluded["reason"] != "team event"]["name"].tolist() if not excluded.empty else []
    excluded_summary = ", ".join(([f"{n_team} Davis Cup ties"] if n_team else []) + others) or "nothing"
    run_name = args.run or os.path.basename(os.path.dirname(model_path))
    config = {
        "run": run_name,
        "season": args.season,
        "n_sims": args.n_sims,
        "seed": args.seed,
        "rng": "numpy default_rng(SeedSequence(seed, spawn_key=(event_index,))), one uniform row per match slot",
        "model": os.path.relpath(model_path, ROOT),
        "model_sha256": model_hash_before,
        "train_through": bundle.train_through,
        "code": git_state(),
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "first_event": str(events[0].date.date()),
        "last_event": str(events[-1].date.date()),
        "events": len(events),
        "events_by_category": {CATEGORY_LABELS[k]: cats[k] for k in CATEGORY_LABELS if cats[k]},
        "excluded_events": excluded.astype(str).to_dict(orient="records"),
        "excluded_summary": excluded_summary,
        "entrants": int(sum(len(e.entrants) for e in events)),
        "players_2025": int(len({int(p) for e in events for p in e.entrants})),
        "players_in_ledger": len(ids),
        "matches_scored": int(len(mt)),
        "year_end_ranking_date": str(official["ranking_date"].max().date()),
        "official_ranking_duplicate_rows_dropped": official.attrs.get("duplicates_dropped", 0),
        "seconds": {"prepare": round(t1 - t0, 1), "simulate": round(t2 - t1, 1)},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    metrics = write_run(out, config, mt, tt, ye, wk)
    if sha256(model_path) != model_hash_before:
        sys.exit("The model file changed during the run. Frozen weights must never be written.")

    mm, tm, sm = metrics["match"], metrics["tournament"], metrics["season"]
    print(f"{run_name}: {args.n_sims:,} seasons in {t2 - t1:.1f}s -> {os.path.relpath(out, ROOT)}")
    print(f"  match: n={mm['n']:,} acc={mm['accuracy']:.3f} log_loss={mm['log_loss']:.4f} "
          f"brier={mm['brier']:.4f} (higher rank {mm['higher_rank_accuracy']:.3f})")
    print(f"  titles: real champion favourite in {tm['actual_champion_is_modal']}/{tm['events']}, "
          f"top 3 in {tm['actual_champion_in_top3']}")
    print(f"  year end: most likely #1 {sm['modal_no1']} ({sm['modal_no1_p']:.1%}); "
          f"real #1 {sm['actual_no1_same_table']} at {sm['p_actual_no1']:.1%}")


if __name__ == "__main__":
    main()
