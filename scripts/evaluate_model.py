#!/usr/bin/env python3
"""Check a fitted model on the seasons it never saw (DESIGN.md §3.3).

Two constant baselines are printed. `pooled` always guesses the surface's training-era
rate (Run 0's straw man). `last` always guesses the last training season's rate, which is
the bar a model with mu anchored on that season has to beat.
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.dataset import load_rows, rows_after, rows_through, rows_to_tensors
from atp_sim.model import SurfaceBundle
from atp_sim.train import evaluate_holdout, evaluate_terms


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", default=os.path.join(ROOT, "runs", "rows.parquet"))
    p.add_argument("--model", default=os.path.join(ROOT, "runs", "model.pt"))
    args = p.parse_args()

    bundle = SurfaceBundle.load(args.model)
    if bundle.train_through is None:
        sys.exit("This model does not record its last training season, so no season can be "
                 "trusted as unseen. Retrain it with scripts/train_model.py.")

    df, _, _ = load_rows(args.rows)
    T = bundle.train_through
    train = rows_to_tensors(rows_through(df, T))
    held = rows_after(df, T)
    if held.empty:
        sys.exit(f"No rows after season {T}: nothing to check against.")
    seasons = sorted(int(s) for s in held["season"].unique())
    print(f"Model trained through {T}. Checking on seasons {seasons} ({len(held):,} rows).")
    print(f"'pooled' = always guessing the surface's training-era rate; "
          f"'last' = always guessing its {T} rate.\n")

    for surface, model in bundle.surfaces.items():
        if surface not in train:
            continue
        tb = train[surface]
        rate = float(tb["won"].sum() / tb["svpt"].sum())
        sel = tb["season"] == T
        last_rate = float(tb["won"][sel].sum() / tb["svpt"][sel].sum().clamp_min(1.0))
        print(f"=== {surface}  (pooled rate {rate:.4f}, {T} rate {last_rate:.4f}, "
              f"model mu → {float(model.mu.sigmoid()):.4f}) ===")
        for label, part in [(str(s), held[held["season"] == s]) for s in seasons] + [("all", held)]:
            batch = rows_to_tensors(part, [surface]).get(surface)
            if batch is None:
                print(f"  {label:>4}: no rows")
                continue
            r = evaluate_holdout(model, batch, rate, last_rate)
            t = evaluate_terms(model, batch["x_i"], batch["x_j"])
            print(f"  {label:>4}: rows={int(r['rows']):5d}  actual={r['actual']:.4f}  "
                  f"predicted={r['predicted']:.4f}  bias={r['predicted'] - r['actual']:+.4f}  "
                  f"drift since {T}={r['actual'] - last_rate:+.4f}")
            print(f"        nll={r['nll']:.5f} (pooled {r['nll_constant']:.5f}, last {r['nll_last']:.5f})  "
                  f"point-MAE={r['point_mae']:.4f} (pooled {r['point_mae_constant']:.4f}, "
                  f"last {r['point_mae_last']:.4f})")
            print(f"        terms: serve={t['mean_|serve|']:.3f}  return={t['mean_|return|']:.3f}  "
                  f"interaction={t['mean_|interaction|']:.3f}")
        print()


if __name__ == "__main__":
    main()
