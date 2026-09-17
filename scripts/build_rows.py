#!/usr/bin/env python3
"""Build the training table: rows.parquet, cards.parquet, constants.csv, build_report.md."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from atp_sim.dataset import build_all, save_build


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, default=1991)
    p.add_argument("--end-year", type=int, default=2026)
    p.add_argument("--out-dir", default=os.path.join(ROOT, "runs"))
    args = p.parse_args()

    print(f"Building training rows {args.start_year} to {args.end_year} ...")
    result = build_all(args.start_year, args.end_year)
    paths = save_build(result, args.out_dir)
    print(f"Wrote {len(result.rows):,} rows -> {paths['rows']}")
    print(f"Wrote {len(result.cards):,} cards -> {paths['cards']}")
    print(f"Surfaces: {result.rows['surface'].value_counts().to_dict()}")
    print(f"Exclusions: {result.exclusions}")
    print(f"Report: {paths['report']}")
    print(f"Elapsed {result.elapsed:.1f}s")


if __name__ == "__main__":
    main()
