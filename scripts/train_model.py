#!/usr/bin/env python3
"""Train the bilinear serve model on rows.parquet → model.pt."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.dataset import load_rows, rows_to_tensors
from atp_sim.train import evaluate_terms, train_all_surfaces


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", default=os.path.join(ROOT, "runs", "rows.parquet"))
    p.add_argument("--out", default=os.path.join(ROOT, "runs", "model.pt"))
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=2048)
    p.add_argument("--lr", type=float, default=0.05)
    p.add_argument("--l2-W", type=float, default=1e-2, dest="l2_W")
    p.add_argument("--l2-ab", type=float, default=1e-4, dest="l2_ab")
    args = p.parse_args()

    df, mean, std = load_rows(args.rows)
    batches = rows_to_tensors(df)
    bundle = train_all_surfaces(
        batches,
        mean,
        std,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        l2_W=args.l2_W,
        l2_ab=args.l2_ab,
    )
    parent = os.path.dirname(args.out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    bundle.save(args.out)
    print(f"\nSaved {bundle.total_parameters()} parameters → {args.out}")

    print("\nTerm magnitudes (mean |contribution|):")
    for surface, b in batches.items():
        stats = evaluate_terms(bundle.surfaces[surface], b["x_i"], b["x_j"])
        print(f"  {surface}: {stats}")


if __name__ == "__main__":
    main()
