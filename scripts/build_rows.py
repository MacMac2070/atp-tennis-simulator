#!/usr/bin/env python3
"""Build rows.parquet — one training row per server per match."""

from __future__ import annotations

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.dataset import build_training_table, save_rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, default=1991)
    p.add_argument("--end-year", type=int, default=2026)
    p.add_argument("--out", default=os.path.join(ROOT, "runs", "rows.parquet"))
    args = p.parse_args()

    t0 = time.time()
    print(f"Building training rows {args.start_year}–{args.end_year}...")
    df, mean, std = build_training_table(args.start_year, args.end_year)
    save_rows(df, mean, std, args.out)
    print(f"Wrote {len(df):,} rows → {args.out}")
    print(f"Surfaces: {df['surface'].value_counts().to_dict()}")
    print(f"Elapsed {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
