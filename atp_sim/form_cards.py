"""Form cards: eight standardised attributes per player per event date.

Implements VERIFY_SPEC sections 4 to 9. The one rule that cannot be broken: a card
for date D uses only appearances dated strictly before D. It is enforced by the
window arithmetic itself (`window_counts`), not by the order in which matches are
streamed, so it holds for any key, including keys with no match on that date.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .data import LIVE_SURFACES

ATTR_NAMES = (
    "serve_strength", "ace_rate", "df_rate", "return_strength",
    "bp_saved", "bp_converted", "form", "age",
)
N_ATTRS = len(ATTR_NAMES)
WINDOW_DAYS = 364
FORM_MATCHES = 10

RATES = ("serve", "ace", "df", "ret", "bps", "bpc")
K = {"serve": 200, "ace": 50, "df": 250, "ret": 300, "bps": 200, "bpc": 350}
COUNT_COLS = ("svpt", "svwon", "ace", "df", "bpf", "bps", "rpt", "rwon", "obpf", "obps")
# (x index, constants attr, card column) in the order of the x vector
STD_ATTRS = (
    ("serve", "shr_serve"), ("ace", "shr_ace"), ("df", "shr_df"), ("ret", "shr_ret"),
    ("bps", "shr_bps"), ("bpc", "shr_bpc"), ("form", "form"), ("age", "age"),
)
EPOCH = pd.Timestamp("1970-01-01")
KEY_SCALE = 100_000  # > max day number, so (player_id * KEY_SCALE + day) is unique and sortable

CARD_COLUMNS = (
    ["player_id", "tourney_date", "season", "n_52w", "n_10"]
    + [f"{c}_52" for c in COUNT_COLS] + ["svpt_10", "svwon_10"]
    + [f"raw_{a}" for a in RATES] + ["raw_serve10"]
    + [f"shr_{a}" for a in RATES] + ["shr_serve10", "form", "age", "dob_missing"]
    + [f"x_{k}" for k in range(N_ATTRS)]
)


def build_log(valid: pd.DataFrame) -> pd.DataFrame:
    """Two appearances per valid match, sorted by (player, date, event, match number)."""

    def side(p: str, o: str, who: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "player_id": valid[f"{who}_id"].to_numpy(np.int64),
                "tourney_date": valid["tourney_date"].to_numpy(),
                "season": valid["season"].to_numpy(np.int64),
                "tourney_id": valid["tourney_id"].astype(str).to_numpy(),
                "match_num": valid["match_num"].to_numpy(np.int64),
                "svpt": valid[f"{p}_svpt"].to_numpy(np.int64),
                "svwon": (valid[f"{p}_1stWon"] + valid[f"{p}_2ndWon"]).to_numpy(np.int64),
                "ace": valid[f"{p}_ace"].to_numpy(np.int64),
                "df": valid[f"{p}_df"].to_numpy(np.int64),
                "bpf": valid[f"{p}_bpFaced"].to_numpy(np.int64),
                "bps": valid[f"{p}_bpSaved"].to_numpy(np.int64),
                "rpt": valid[f"{o}_svpt"].to_numpy(np.int64),
                "rwon": (valid[f"{o}_svpt"] - valid[f"{o}_1stWon"] - valid[f"{o}_2ndWon"]).to_numpy(np.int64),
                "obpf": valid[f"{o}_bpFaced"].to_numpy(np.int64),
                "obps": valid[f"{o}_bpSaved"].to_numpy(np.int64),
            }
        )

    log = pd.concat([side("w", "l", "winner"), side("l", "w", "loser")], ignore_index=True)
    log = log.sort_values(["player_id", "tourney_date", "tourney_id", "match_num"], kind="mergesort")
    log = log.reset_index(drop=True)
    log["day"] = (log["tourney_date"] - EPOCH).dt.days.to_numpy(np.int64)
    return log


def appearance_keys(valid: pd.DataFrame) -> pd.DataFrame:
    """Every (player_id, tourney_date, season) at which a player has a valid match."""
    w = valid[["winner_id", "tourney_date", "season"]].rename(columns={"winner_id": "player_id"})
    l = valid[["loser_id", "tourney_date", "season"]].rename(columns={"loser_id": "player_id"})
    keys = pd.concat([w, l], ignore_index=True).drop_duplicates(["player_id", "tourney_date"])
    return keys.sort_values(["player_id", "tourney_date"]).reset_index(drop=True)


def population_keys(valid: pd.DataFrame, season: int) -> pd.DataFrame:
    """P(season): the server cards of that season's would-be rows, one entry per row."""
    m = valid[(valid["season"] == season) & valid["surface"].isin(LIVE_SURFACES)]
    w = m[["winner_id", "tourney_date"]].rename(columns={"winner_id": "player_id"})
    l = m[["loser_id", "tourney_date"]].rename(columns={"loser_id": "player_id"})
    return pd.concat([w, l], ignore_index=True)


def window_counts(log: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    """52-week and last-10 sums for every key, from per-player cumulative sums.

    Window = appearances with day in [D - WINDOW_DAYS, D). Searching the sorted
    (player, day) key with side='left' at D excludes every same-day appearance.
    """
    key_arr = log["player_id"].to_numpy(np.int64) * KEY_SCALE + log["day"].to_numpy(np.int64)
    if len(key_arr) and not np.all(np.diff(key_arr) >= 0):
        raise AssertionError("log is not sorted by (player_id, day)")
    counts = log[list(COUNT_COLS)].to_numpy(np.int64)
    cs = np.vstack([np.zeros((1, counts.shape[1]), np.int64), np.cumsum(counts, axis=0)])

    pid = keys["player_id"].to_numpy(np.int64)
    day = (keys["tourney_date"] - EPOCH).dt.days.to_numpy(np.int64)
    hi = np.searchsorted(key_arr, pid * KEY_SCALE + day, side="left")
    lo = np.searchsorted(key_arr, pid * KEY_SCALE + np.maximum(day - WINDOW_DAYS, 0), side="left")
    lo10 = np.maximum(hi - FORM_MATCHES, lo)
    s52 = cs[hi] - cs[lo]
    s10 = cs[hi] - cs[lo10]

    out = keys[["player_id", "tourney_date", "season"]].copy().reset_index(drop=True)
    out["n_52w"] = hi - lo
    out["n_10"] = hi - lo10
    for j, c in enumerate(COUNT_COLS):
        out[f"{c}_52"] = s52[:, j]
    out["svpt_10"] = s10[:, 0]
    out["svwon_10"] = s10[:, 1]
    return out


def season_priors(log: pd.DataFrame) -> pd.DataFrame:
    """m_prior per season: pooled rates of the previous season; the first season uses itself."""
    g = log.groupby("season")[list(COUNT_COLS)].sum()
    pooled = pd.DataFrame(
        {
            "serve": g["svwon"] / g["svpt"],
            "ace": g["ace"] / g["svpt"],
            "df": g["df"] / g["svpt"],
            "ret": g["rwon"] / g["rpt"],
            "bps": g["bps"] / g["bpf"],
            "bpc": (g["obpf"] - g["obps"]) / g["obpf"],
        }
    )
    if pooled.empty:
        raise ValueError("no valid appearances: cannot compute season priors")
    priors = pooled.copy()
    priors.index = priors.index + 1
    first = int(pooled.index.min())
    priors.loc[first] = pooled.loc[first]
    priors.index.name = "season"
    return priors.sort_index()


def _rate_parts(cards: pd.DataFrame, attr: str) -> tuple[np.ndarray, np.ndarray]:
    if attr == "bpc":
        return (cards["obpf_52"] - cards["obps_52"]).to_numpy(np.float64), cards["obpf_52"].to_numpy(np.float64)
    num, den = {"serve": ("svwon", "svpt"), "ace": ("ace", "svpt"), "df": ("df", "svpt"),
                "ret": ("rwon", "rpt"), "bps": ("bps", "bpf")}[attr]
    return cards[f"{num}_52"].to_numpy(np.float64), cards[f"{den}_52"].to_numpy(np.float64)


def _shrunk(num: np.ndarray, den: np.ndarray, k: float, m: np.ndarray) -> np.ndarray:
    return np.where(den == 0, m, (num + k * m) / (den + k))


def shrink(cards: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    """Raw rates, shrunk rates and form (section 7)."""
    seasons = cards["season"].to_numpy(np.int64)
    missing = sorted(set(seasons) - set(priors.index))
    if missing:
        raise ValueError(f"no prior for seasons {missing}: load the previous season too")
    out = cards.copy()
    for attr in RATES:
        num, den = _rate_parts(out, attr)
        m = priors[attr].reindex(seasons).to_numpy(np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            out[f"raw_{attr}"] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
        out[f"shr_{attr}"] = _shrunk(num, den, K[attr], m)
    m_serve = priors["serve"].reindex(seasons).to_numpy(np.float64)
    n10, d10 = out["svwon_10"].to_numpy(np.float64), out["svpt_10"].to_numpy(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["raw_serve10"] = np.where(d10 > 0, n10 / np.where(d10 > 0, d10, 1.0), np.nan)
    out["shr_serve10"] = _shrunk(n10, d10, K["serve"], m_serve)
    out["form"] = out["shr_serve10"] - out["shr_serve"]
    return out


def attach_age(cards: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    out = cards.copy()
    dob = players["dob"].reindex(out["player_id"].to_numpy()).to_numpy()
    out["age"] = (out["tourney_date"].to_numpy() - dob) / np.timedelta64(1, "D") / 365.25
    out["dob_missing"] = np.isnan(out["age"].to_numpy(np.float64))
    return out


def season_constants(cards: pd.DataFrame, valid: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    """mu and sigma for season Y+1 from P(Y), for every season Y present in `valid`."""
    rows = []
    for season in sorted(valid["season"].unique()):
        pop = population_keys(valid, int(season))
        if pop.empty:
            continue
        merged = pop.merge(cards, on=["player_id", "tourney_date"], how="left", validate="many_to_one")
        if merged["n_52w"].isna().any():
            raise AssertionError("population card missing; cards must cover every appearance")
        target = int(season) + 1
        for attr, col in STD_ATTRS:
            v = merged[col].to_numpy(np.float64)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                mu, sigma = float(np.nanmean(v)), float(np.nanstd(v))
            rows.append(
                {
                    "season": target, "attr": attr,
                    "k": K.get(attr, np.nan),
                    "m_prior": float(priors.loc[target, attr]) if attr in RATES else np.nan,
                    "mu": mu, "sigma": sigma, "n_pop": int(len(merged)),
                }
            )
    return pd.DataFrame(rows, columns=["season", "attr", "k", "m_prior", "mu", "sigma", "n_pop"])


def standardise_cards(cards: pd.DataFrame, constants: pd.DataFrame) -> pd.DataFrame:
    """x = (value - mu) / sigma per season; sigma 0 or a missing value gives 0; no constants gives NaN."""
    out = cards.copy()
    seasons = out["season"].to_numpy(np.int64)
    if constants.empty:
        for k in range(N_ATTRS):
            out[f"x_{k}"] = np.nan
        return out
    mu_w = constants.pivot(index="season", columns="attr", values="mu")
    sg_w = constants.pivot(index="season", columns="attr", values="sigma")
    has_const = np.isin(seasons, mu_w.index.to_numpy())
    for k, (attr, col) in enumerate(STD_ATTRS):
        mu = mu_w[attr].reindex(seasons).to_numpy(np.float64)
        sigma = sg_w[attr].reindex(seasons).to_numpy(np.float64)
        v = out[col].to_numpy(np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            x = (v - mu) / np.where(sigma > 0, sigma, 1.0)
        x = np.where(has_const & (np.isnan(v) | ~(sigma > 0)), 0.0, x)
        x = np.where(has_const, x, np.nan)
        out[f"x_{k}"] = x
    return out


def _coerce_keys(keys: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "player_id": keys["player_id"].to_numpy(np.int64),
            "tourney_date": pd.to_datetime(keys["tourney_date"]).to_numpy(),
            "season": keys["season"].to_numpy(np.int64),
        }
    )
    return out


def build_cards(
    valid: pd.DataFrame,
    players: pd.DataFrame,
    keys: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cards for every appearance in `valid` (or for the given keys) plus the constants table.

    `keys` needs columns player_id, tourney_date, season. Cards for the standardisation
    populations are always computed internally, so requesting a single key still yields
    the same constants as a full build on the same matches.
    """
    log = build_log(valid)
    priors = season_priors(log)
    all_keys = _coerce_keys(appearance_keys(valid))
    requested = all_keys if keys is None else _coerce_keys(keys)
    need = pd.concat([all_keys, requested], ignore_index=True).drop_duplicates(["player_id", "tourney_date"])

    cards = window_counts(log, need.reset_index(drop=True))
    cards = shrink(cards, priors)
    cards = attach_age(cards, players)
    constants = season_constants(cards, valid, priors)
    cards = standardise_cards(cards, constants)

    if keys is not None:
        sel = requested[["player_id", "tourney_date"]].drop_duplicates()
        cards = sel.merge(cards, on=["player_id", "tourney_date"], how="left", validate="one_to_one")
    cards = cards.sort_values(["player_id", "tourney_date"]).reset_index(drop=True)
    return cards[CARD_COLUMNS], constants


def standardise(raw: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """Map a raw card to x with given constants; missing values map to 0 (tour average)."""
    z = (raw - mean) / np.where(std > 0, std, 1.0)
    return np.where(np.isnan(raw) | ~(std > 0), 0.0, z)
