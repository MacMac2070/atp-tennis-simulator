#!/usr/bin/env python3
"""Train the bilinear serve model on rows.parquet → model.pt."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.dataset import load_constants, load_rows, rows_through, rows_to_tensors
from atp_sim.train import evaluate_terms, train_all_surfaces


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", default=os.path.join(ROOT, "runs", "rows.parquet"))
    p.add_argument("--out", default=os.path.join(ROOT, "runs", "model.pt"))
    p.add_argument("--train-through", type=int, default=2024, dest="train_through",
                   help="last season used for fitting; later seasons are held out (e.g. test 2025+)")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=2048)
    p.add_argument("--lr", type=float, default=0.05)
    p.add_argument("--l2-W", type=float, default=1e-2, dest="l2_W")
    p.add_argument("--l2-ab", type=float, default=1e-4, dest="l2_ab")
    p.add_argument("--lr-decay", action=argparse.BooleanOptionalAction, default=True, dest="lr_decay",
                   help="cool the learning rate to 5%% over the run so mu settles on the anchor "
                        "season instead of jittering by about --lr in log-odds (default: on)")
    args = p.parse_args()

    df, _, _ = load_rows(args.rows)
    train = rows_through(df, args.train_through)
    held_out = len(df) - len(train)
    print(f"Training on seasons {int(train['season'].min())} to {int(train['season'].max())}: "
          f"{len(train):,} rows. Held out after {args.train_through}: {held_out:,} rows.")
    if held_out == 0:
        print("WARNING: nothing is held out, so this model cannot be checked on unseen seasons.",
              file=sys.stderr)
    # the first season this model may be asked about; its constants use only seasons it has seen
    mean, std = load_constants(args.rows, args.train_through + 1)
    batches = rows_to_tensors(train)
    print("Serve rate mu is anchored on the last training season (pooled rate shown for reference):")
    for surface, b in batches.items():
        last = b["season"] == args.train_through
        pooled = float(b["won"].sum() / b["svpt"].sum())
        recent = float(b["won"][last].sum() / b["svpt"][last].sum().clamp_min(1.0))
        print(f"  {surface}: {args.train_through} rate {recent:.4f}   pooled {pooled:.4f}")
    bundle = train_all_surfaces(
        batches,
        mean,
        std,
        train_through=args.train_through,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        l2_W=args.l2_W,
        l2_ab=args.l2_ab,
        lr_decay=args.lr_decay,
    )
    parent = os.path.dirname(args.out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    bundle.save(args.out)
    print(f"\nSaved {bundle.total_parameters()} parameters → {args.out} (season offsets are not saved)")

    print("\nFitted season offsets delta (log-odds relative to the anchor season):")
    for surface, m in bundle.surfaces.items():
        d = m.fitted_offsets
        if not d:
            print(f"  {surface}: none")
            continue
        picks = [s for s in (min(d), 2000, 2010, 2020, max(d) - 1, max(d)) if s in d]
        print(f"  {surface}: " + "  ".join(f"{s}={d[s]:+.3f}" for s in dict.fromkeys(picks)))

    print("\nTerm magnitudes on the TRAINING rows (mean |contribution|); "
          "run scripts/evaluate_model.py for the holdout seasons:")
    for surface, b in batches.items():
        stats = evaluate_terms(bundle.surfaces[surface], b["x_i"], b["x_j"])
        print(f"  {surface}: {stats}")


if __name__ == "__main__":
    main()
