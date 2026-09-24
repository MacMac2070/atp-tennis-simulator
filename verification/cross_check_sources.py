"""Cross-check the Sackmann archive against TennisMyLife (TML), season by season.

Read-only on data/. Joins the two sources on the unordered pair of normalised
player names plus round, within the same tournament (start dates within
MAX_DATE_GAP_DAYS), then reports coverage and field-by-field agreement.

Usage:  python verification/cross_check_sources.py [--start 1992] [--end 2026]
Writes: runs/cross_check_summary.md
        runs/cross_check_mismatches.csv
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from atp_sim.data import STAT_COLS, load_matches  # noqa: E402

TML_DIR = os.path.join(ROOT, "verification", "external", "tml")
OUT_DIR = os.path.join(ROOT, "runs")

MAX_DATE_GAP_DAYS = 15  # TML dates Grand Slam rows by match day, Sackmann by tournament start
SERVE_WON = ("1stWon", "2ndWon")


def norm_name(name: object) -> str:
    """Lower-case ASCII letters only, so accents, hyphens and spacing cannot break the join."""
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", text.lower())


def norm_score(score: object) -> str:
    """Compare scores on digits and retirement markers only, ignoring spacing and bracket style."""
    text = str(score).upper().replace("RET", " RET").replace("DEF", " DEF")
    return " ".join(re.sub(r"[^0-9A-Z\-() ]", " ", text).split())


def load_tml(start: int, end: int) -> pd.DataFrame:
    frames = []
    for year in range(start, end + 1):
        path = os.path.join(TML_DIR, f"{year}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing TML file {path}")
        df = pd.read_csv(path, low_memory=False)
        df["season"] = year
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def add_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    w, l = out["winner_name"].map(norm_name), out["loser_name"].map(norm_name)
    out["w_key"] = w
    out["pair"] = [" | ".join(sorted(p)) for p in zip(w, l)]
    out["date"] = pd.to_datetime(out["tourney_date"].astype("Int64").astype(str), format="%Y%m%d")
    out["nscore"] = out["score"].map(norm_score)
    out["row"] = range(len(out))
    return out


def join_sources(sack: pd.DataFrame, tml: pd.DataFrame) -> pd.DataFrame:
    """One-to-one join: closest tournament date wins when a pair met twice in the same round."""
    both = sack.merge(tml, on=["season", "pair", "round"], suffixes=("_s", "_t"))
    both["gap"] = (both["date_s"] - both["date_t"]).abs().dt.days
    both = both[both["gap"] <= MAX_DATE_GAP_DAYS].sort_values("gap")
    both = both.drop_duplicates("row_s").drop_duplicates("row_t")

    # Second pass for spelling differences ("Albert Ramos" vs "Albert Ramos-Vinolas"): same
    # tournament date, round and score, accepted only when that key is unique on both sides.
    key = ["season", "tourney_date", "round", "nscore"]
    rest_s = sack[~sack["row"].isin(both["row_s"])]
    rest_t = tml[~tml["row"].isin(both["row_t"])]
    rest_s = rest_s[~rest_s.duplicated(key, keep=False)]
    rest_t = rest_t[~rest_t.duplicated(key, keep=False)]
    extra = rest_s.merge(rest_t, on=key, suffixes=("_s", "_t"))
    extra["pair"] = extra["pair_s"]
    extra["gap"] = 0
    extra["name_fallback"] = True
    both["name_fallback"] = False
    return pd.concat([both, extra], ignore_index=True)


def serve_rate(df: pd.DataFrame) -> pd.Series:
    """Share of service points won per season and surface, winner and loser pooled."""
    d = df.dropna(subset=STAT_COLS)
    d = d[(d["w_svpt"] > 0) & (d["l_svpt"] > 0)]
    won = sum(d[f"{s}_{c}"] for s in ("w", "l") for c in SERVE_WON)
    tot = d["w_svpt"] + d["l_svpt"]
    g = pd.DataFrame({"season": d["season"], "surface": d["surface"], "won": won, "tot": tot})
    g = g.groupby(["season", "surface"])[["won", "tot"]].sum()
    return (g["won"] / g["tot"]).rename("rate")


def differs(a: pd.Series, b: pd.Series) -> pd.Series:
    """True where the two values disagree; both-missing counts as agreement."""
    return ~((a == b) | (a.isna() & b.isna()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", type=int, default=1992)
    ap.add_argument("--end", type=int, default=2026)
    args = ap.parse_args()

    sack = add_keys(load_matches(args.start, args.end))
    tml = add_keys(load_tml(args.start, args.end))
    # Coverage is only fair where both sources have been updated to the same date.
    cutoff = min(sack["date"].max(), tml["date"].max())
    sack = sack[sack["date"] <= cutoff]
    tml = tml[tml["date"] <= cutoff + pd.Timedelta(days=MAX_DATE_GAP_DAYS)]
    both = join_sources(sack, tml)
    # Later TML rows were only kept so late rounds could join; unmatched ones are not a coverage gap.
    tml = tml[(tml["date"] <= cutoff) | tml["row"].isin(both["row_t"])]

    lines = ["# Sackmann vs TennisMyLife cross-check", "",
             f"Both sources cut at tournament start date {cutoff.date()} (the earlier of the two last dates).", "",
             "## Coverage and agreement by season", "",
             "| Season | Sackmann | TML | Matched | Sack only | TML only | Winner diff | Score diff |"
             " Surface diff | Minutes diff | Rows with any serve-stat diff |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]

    mismatches = []
    for season, m in both.groupby("season"):
        s_n = int((sack["season"] == season).sum())
        t_n = int((tml["season"] == season).sum())
        # A fallback row has an identical winner-oriented score, so the winner is the same player.
        win = (m["w_key_s"] != m["w_key_t"]) & ~m["name_fallback"]
        score = m["score_s"].map(norm_score) != m["score_t"].map(norm_score)
        surf = m["surface_s"].fillna("") != m["surface_t"].fillna("")
        mins = differs(m["minutes_s"], m["minutes_t"])
        # Stats are compared in the winner/loser orientation, so only where the winner agrees.
        stat_diff = pd.Series(False, index=m.index)
        for c in STAT_COLS:
            stat_diff |= differs(m[f"{c}_s"], m[f"{c}_t"])
        stat_diff &= ~win
        lines.append(f"| {season} | {s_n} | {t_n} | {len(m)} | {s_n - len(m)} | {t_n - len(m)} | "
                     f"{int(win.sum())} | {int(score.sum())} | {int(surf.sum())} | {int(mins.sum())} | "
                     f"{int(stat_diff.sum())} |")
        bad = m[win | score | surf | stat_diff].copy()
        bad["winner_diff"], bad["score_diff"] = win, score
        bad["surface_diff"], bad["stat_diff"] = surf, stat_diff
        mismatches.append(bad)

    lines += ["", "## Serve-stat agreement by column (matched rows with the same winner)", "",
              "| Column | Both present | Differ | Missing in one source only | Mean abs diff when differing | Max abs diff |",
              "|---|---|---|---|---|---|"]
    same_w = both[(both["w_key_s"] == both["w_key_t"]) | both["name_fallback"]]
    for c in STAT_COLS:
        a, b = same_w[f"{c}_s"], same_w[f"{c}_t"]
        ok = a.notna() & b.notna()
        d = (a[ok] - b[ok]).abs()
        nz = d[d > 0]
        lines.append(f"| {c} | {int(ok.sum())} | {len(nz)} | {int((a.isna() ^ b.isna()).sum())} | "
                     f"{nz.mean() if len(nz) else 0:.2f} | {nz.max() if len(nz) else 0:.0f} |")

    lines += ["", "## Share of service points won, by source (recent seasons)", "",
              "| Season | Surface | Sackmann | TML | Difference |", "|---|---|---|---|---|"]
    rs, rt = serve_rate(sack), serve_rate(tml)
    for (season, surface) in rs.index:
        if season >= args.end - 5 and surface in ("Hard", "Clay", "Grass"):
            t = rt.get((season, surface), float("nan"))
            lines.append(f"| {season} | {surface} | {rs[(season, surface)]:.4f} | {t:.4f} | "
                         f"{rs[(season, surface)] - t:+.4f} |")

    os.makedirs(OUT_DIR, exist_ok=True)
    keep = ["season", "round", "pair", "tourney_name_s", "tourney_name_t", "date_s", "date_t",
            "winner_name_s", "winner_name_t", "score_s", "score_t", "surface_s", "surface_t",
            "winner_diff", "score_diff", "surface_diff", "stat_diff"]
    keep += [f"{c}_{x}" for c in STAT_COLS for x in ("s", "t")]
    pd.concat(mismatches)[keep].to_csv(os.path.join(OUT_DIR, "cross_check_mismatches.csv"), index=False)

    # Unmatched rows, kept for diagnosis (a weak join looks like bad data otherwise).
    cols = ["season", "tourney_name", "tourney_level", "tourney_date", "round", "winner_name", "loser_name", "score"]
    sack[~sack["row"].isin(both["row_s"])][cols].to_csv(os.path.join(OUT_DIR, "cross_check_sackmann_only.csv"), index=False)
    tml[~tml["row"].isin(both["row_t"])][cols].to_csv(os.path.join(OUT_DIR, "cross_check_tml_only.csv"), index=False)

    with open(os.path.join(OUT_DIR, "cross_check_summary.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
