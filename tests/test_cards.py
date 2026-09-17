"""Card arithmetic worked by hand from the synthetic archive in conftest.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from atp_sim.data import parse_players, prepare_matches
from atp_sim.form_cards import ATTR_NAMES, K, N_ATTRS, build_cards
from tests.conftest import mk, raw_frame

# Season 2018 appearances (M1 and M2, both sides), pooled: the priors for 2019 and,
# because 2018 is the first season, also for 2018.
SVPT, SVWON, ACE, DF, BPF, BPS = 274, 175, 20, 10, 23, 10
M = {"serve": SVWON / SVPT, "ace": ACE / SVPT, "df": DF / SVPT,
     "ret": (SVPT - SVWON) / SVPT, "bps": BPS / BPF, "bpc": (BPF - BPS) / BPF}


def shr(num, den, attr):
    return (num + K[attr] * M[attr]) / (den + K[attr])


def age(dob, on):
    return (pd.Timestamp(on) - pd.Timestamp(dob)).days / 365.25


def card(cards, pid, date):
    sel = cards[(cards["player_id"] == pid) & (cards["tourney_date"] == pd.Timestamp(date))]
    assert len(sel) == 1
    return sel.iloc[0]


def test_attr_names_contract():
    assert ATTR_NAMES == ("serve_strength", "ace_rate", "df_rate", "return_strength",
                          "bp_saved", "bp_converted", "form", "age")
    assert N_ATTRS == 8
    assert K == {"serve": 200, "ace": 50, "df": 250, "ret": 300, "bps": 200, "bpc": 350}


def test_hand_computed_card_player1_2019_03_04(synthetic):
    valid, players = synthetic
    cards, constants = build_cards(valid, players)
    c = card(cards, 1, "2019-03-04")

    # window [2018-03-05, 2019-03-04): M1 (player 1 served 80, won 55) and M2 (64, 38)
    assert (c["n_52w"], c["n_10"]) == (2, 2)
    assert (c["svpt_52"], c["svwon_52"], c["ace_52"], c["df_52"], c["bpf_52"], c["bps_52"]) == (144, 93, 13, 6, 11, 4)
    assert (c["rpt_52"], c["rwon_52"], c["obpf_52"], c["obps_52"]) == (130, 48, 12, 6)
    assert (c["svpt_10"], c["svwon_10"]) == (144, 93)

    assert c["raw_serve"] == pytest.approx(93 / 144)
    assert c["raw_bpc"] == pytest.approx(6 / 12)
    assert c["shr_serve"] == pytest.approx(shr(93, 144, "serve"), abs=1e-12)
    assert c["shr_ace"] == pytest.approx(shr(13, 144, "ace"), abs=1e-12)
    assert c["shr_df"] == pytest.approx(shr(6, 144, "df"), abs=1e-12)
    assert c["shr_ret"] == pytest.approx(shr(48, 130, "ret"), abs=1e-12)
    assert c["shr_bps"] == pytest.approx(shr(4, 11, "bps"), abs=1e-12)
    assert c["shr_bpc"] == pytest.approx(shr(6, 12, "bpc"), abs=1e-12)
    assert c["form"] == 0.0
    assert c["age"] == pytest.approx(age("1990-01-01", "2019-03-04"))
    assert not c["dob_missing"]

    # Constants for 2019 come from P(2018): the four server cards of M1 and M2.
    nohist = [shr(0, 0, a) for a in ("serve", "ace", "df", "ret", "bps", "bpc")]
    p2_0604 = [shr(42, 70, "serve"), shr(4, 70, "ace"), shr(3, 70, "df"), shr(25, 80, "ret"), shr(4, 8, "bps"), shr(2, 5, "bpc")]
    p1_0604 = [shr(55, 80, "serve"), shr(8, 80, "ace"), shr(2, 80, "df"), shr(28, 70, "ret"), shr(3, 5, "bps"), shr(4, 8, "bpc")]
    pop = np.array([nohist, nohist, p2_0604, p1_0604])
    ages = np.array([age("1990-01-01", "2018-03-05"), age("1992-06-15", "2018-03-05"),
                     age("1992-06-15", "2018-06-04"), age("1990-01-01", "2018-06-04")])
    mu, sd = pop.mean(axis=0), pop.std(axis=0)
    vals = [c["shr_serve"], c["shr_ace"], c["shr_df"], c["shr_ret"], c["shr_bps"], c["shr_bpc"]]
    for k in range(6):
        assert c[f"x_{k}"] == pytest.approx((vals[k] - mu[k]) / sd[k], abs=1e-9)
    assert c["x_6"] == 0.0  # every 2018 card has form 0, sigma 0 -> x 0
    assert c["x_7"] == pytest.approx((c["age"] - ages.mean()) / ages.std(), abs=1e-9)

    k2019 = constants[constants["season"] == 2019].set_index("attr")
    assert k2019.loc["serve", "m_prior"] == pytest.approx(M["serve"])
    assert k2019.loc["serve", "mu"] == pytest.approx(mu[0])
    assert k2019.loc["serve", "sigma"] == pytest.approx(sd[0])
    assert int(k2019.loc["serve", "n_pop"]) == 4
    assert 2018 not in set(constants["season"])  # first season has no constants


def test_no_history_card_and_missing_dob(synthetic):
    valid, players = synthetic
    cards, _ = build_cards(valid, players)
    c = card(cards, 3, "2019-03-04")
    assert c["n_52w"] == 0
    for attr in ("serve", "ace", "df", "ret", "bps", "bpc"):
        assert c[f"shr_{attr}"] == M[attr]
        assert np.isnan(c[f"raw_{attr}"])
    assert c["form"] == 0.0
    assert np.isnan(c["age"]) and c["dob_missing"]
    assert c["x_7"] == 0.0


def test_first_season_cards_have_no_x(synthetic):
    valid, players = synthetic
    cards, _ = build_cards(valid, players)
    c = card(cards, 1, "2018-06-04")
    assert c["n_52w"] == 1 and c["svpt_52"] == 80
    assert np.isnan(c["x_0"])


def test_last10_inside_window_and_form():
    """12 matches inside the window: last-10 drops the two oldest; with 10, form is exactly 0."""
    stats = (60, 40, 30, 10, 3, 1, 2, 4)
    D = pd.Timestamp("2019-12-02")

    def archive(n):
        rows = []
        for k in range(n):
            date = (D - pd.Timedelta(days=300 - 7 * k)).strftime("%Y-%m-%d")
            rows.append(mk(f"L{k:02d}", "L", "Hard", "A", date, 1, 11, 12,
                           (50 + k, 40, 20 + k, 5, 1, 1, 1, 2), stats))
        rows.append(mk("LD", "L", "Hard", "A", D.strftime("%Y-%m-%d"), 1, 11, 12, stats, stats))
        return raw_frame(rows)

    players = parse_players(pd.DataFrame({"player_id": [11, 12], "dob": [np.nan, np.nan]}))
    keys = pd.DataFrame({"player_id": [11], "tourney_date": [D], "season": [2019]})

    valid12, _ = prepare_matches(archive(12))
    c12 = build_cards(valid12, players, keys=keys)[0].iloc[0]
    assert c12["n_52w"] == 12 and c12["n_10"] == 10
    assert c12["svpt_52"] == sum(50 + k for k in range(12))
    assert c12["svpt_10"] == sum(50 + k for k in range(2, 12))
    assert c12["svwon_10"] == sum(25 + k for k in range(2, 12))
    assert c12["form"] != 0.0
    assert c12["form"] == pytest.approx(c12["shr_serve10"] - c12["shr_serve"], abs=1e-15)

    valid10, _ = prepare_matches(archive(10))
    c10 = build_cards(valid10, players, keys=keys)[0].iloc[0]
    assert c10["n_52w"] == 10 and c10["n_10"] == 10
    assert c10["form"] == 0.0


def test_constants_come_only_from_previous_season(synthetic):
    valid, players = synthetic
    _, base = build_cards(valid, players)

    # Perturb a 2019 match: 2019's constants (from 2018) must not move, 2020's must.
    bumped = valid.copy()
    i = bumped.index[bumped["tourney_id"] == "T19A"][0]
    bumped.loc[i, "w_1stWon"] = bumped.loc[i, "w_1stWon"] - 10
    _, after = build_cards(bumped, players)

    b19 = base[base["season"] == 2019].set_index("attr")
    a19 = after[after["season"] == 2019].set_index("attr")
    pd.testing.assert_frame_equal(b19, a19)
    b20 = base[base["season"] == 2020].set_index("attr")
    a20 = after[after["season"] == 2020].set_index("attr")
    assert b20.loc["serve", "mu"] != a20.loc["serve", "mu"]


def test_standardised_population_has_mean_zero_sd_one(synthetic):
    """Applying season Y constants to P(Y-1) gives mean 0 and SD 1 exactly."""
    from atp_sim.form_cards import population_keys

    valid, players = synthetic
    cards, constants = build_cards(valid, players)
    pop = population_keys(valid, 2018)  # one row per would-be server row of 2018
    merged = pop.merge(cards, on=["player_id", "tourney_date"], how="left")
    k = constants[constants["season"] == 2019].set_index("attr")
    z = (merged["shr_serve"] - k.loc["serve", "mu"]) / k.loc["serve", "sigma"]
    assert z.mean() == pytest.approx(0.0, abs=1e-12)
    assert z.std(ddof=0) == pytest.approx(1.0, abs=1e-12)


def test_determinism_real(real):
    valid, players, _ = real
    a, ca = build_cards(valid, players)
    b, cb = build_cards(valid, players)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(ca, cb)


def test_age_matches_sackmann_real(real):
    valid, players, _ = real
    cards, _ = build_cards(valid, players)
    w = valid[["winner_id", "tourney_date", "winner_age"]].rename(columns={"winner_id": "player_id", "winner_age": "csv_age"})
    l = valid[["loser_id", "tourney_date", "loser_age"]].rename(columns={"loser_id": "player_id", "loser_age": "csv_age"})
    both = pd.concat([w, l]).merge(cards[["player_id", "tourney_date", "age", "dob_missing"]], on=["player_id", "tourney_date"])
    both = both[~both["dob_missing"] & both["csv_age"].notna()]
    diff = (both["age"] - both["csv_age"]).abs()
    assert (diff <= 0.15).mean() >= 0.995
    assert diff.max() <= 1.0  # anything larger was nulled by clean_players_dob
