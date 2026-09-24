"""Chronological split and a smoke test of the training loop (DESIGN.md §9)."""

from __future__ import annotations

import math

import pandas as pd
import pytest
import torch

from atp_sim.dataset import final_constants, rows_after, rows_through
from atp_sim.form_cards import STD_ATTRS
from atp_sim.model import BilinearServeModel, SeasonOffsets, SurfaceBundle, init_mu_from_rate
from atp_sim.train import evaluate_holdout, train_all_surfaces, train_surface


def test_rows_through_keeps_only_earlier_seasons():
    df = pd.DataFrame({"season": [2022, 2023, 2023, 2024, 2025], "won": [1, 2, 3, 4, 5]})
    part = rows_through(df, 2023)
    assert part["season"].max() == 2023
    assert part["won"].tolist() == [1, 2, 3]


def test_rows_through_refuses_an_empty_split():
    df = pd.DataFrame({"season": [2024, 2025]})
    with pytest.raises(ValueError):
        rows_through(df, 2023)
    with pytest.raises(ValueError):
        rows_through(pd.DataFrame({"won": [1]}), 2023)


def test_rows_after_is_the_complement_and_may_be_empty():
    df = pd.DataFrame({"season": [2023, 2024, 2025, 2026]})
    assert rows_after(df, 2024)["season"].tolist() == [2025, 2026]
    assert rows_after(df, 2026).empty
    assert len(rows_through(df, 2024)) + len(rows_after(df, 2024)) == len(df)


def test_constants_are_picked_by_season_not_latest():
    """A model fitted through T carries season T+1's constants, never a later season's."""
    constants = pd.DataFrame(
        [{"season": s, "attr": attr, "mu": s + i / 10, "sigma": 1.0}
         for s in (2025, 2027) for i, (attr, _) in enumerate(STD_ATTRS)]
    )
    mean_2025, _ = final_constants(constants, 2025)
    mean_latest, _ = final_constants(constants)
    assert mean_2025[0] == 2025.0 and mean_latest[0] == 2027.0
    with pytest.raises(ValueError):
        final_constants(constants, 2026)


def test_evaluate_holdout_scores_against_the_training_rate():
    x_i, x_j, won, svpt = _average_players(8, rate=0.70)
    m = BilinearServeModel(init_mu=init_mu_from_rate(0.70))
    r = evaluate_holdout(m, {"x_i": x_i, "x_j": x_j, "won": won, "svpt": svpt}, train_rate=0.60)
    assert math.isclose(r["actual"], 0.70, abs_tol=1e-6)
    assert math.isclose(r["predicted"], 0.70, abs_tol=1e-4)
    assert r["nll"] < r["nll_constant"]          # the right rate beats a stale constant
    assert r["point_mae"] < 1e-4 < r["point_mae_constant"]


def _average_players(n: int = 64, rate: float = 0.64):
    """Every card is exactly tour average, so only mu can explain the data."""
    x = torch.zeros(n, 8)
    svpt = torch.full((n,), 80.0)
    won = torch.full((n,), 80.0 * rate)
    return x, x.clone(), won, svpt


def test_train_surface_holds_the_baseline_for_average_players():
    x_i, x_j, won, svpt = _average_players()
    m = train_surface(x_i, x_j, won, svpt, epochs=60, batch_size=64, verbose=False)
    assert m.n_parameters() == 81
    assert all(torch.isfinite(p).all() for p in m.parameters())
    # zero cards give zero gradient to a, b and W, so only mu may move
    assert float(m.a.detach().abs().max()) == 0.0
    assert float(m.b.detach().abs().max()) == 0.0
    assert float(m.W.detach().abs().max()) == 0.0
    # Adam steps are about lr in size whatever the gradient, so mu wanders early, then settles on the rate
    assert math.isclose(float(m.mu.detach()), init_mu_from_rate(0.64), abs_tol=0.05)
    assert math.isclose(float(m(x_i[0], x_j[0]).detach()), 0.64, abs_tol=0.01)


def test_bundle_records_the_training_cutoff(tmp_path, capsys):
    x_i, x_j, won, svpt = _average_players(16)
    batches = {"Hard": {"x_i": x_i, "x_j": x_j, "won": won, "svpt": svpt}}
    bundle = train_all_surfaces(batches, torch.zeros(8), torch.ones(8), train_through=2023,
                                epochs=1, verbose=False)
    capsys.readouterr()
    assert bundle.total_parameters() == 81
    path = str(tmp_path / "model.pt")
    bundle.save(path)
    assert SurfaceBundle.load(path).train_through == 2023
    assert isinstance(SurfaceBundle.load(path).surfaces["Hard"], BilinearServeModel)


# --- Run 1: the training-only season offset that anchors mu on the last season ---

def _two_seasons(rate_old: float, rate_new: float, n: int = 64):
    """Average players (x = 0) in two seasons at different serve levels."""
    x = torch.zeros(2 * n, 8)
    svpt = torch.full((2 * n,), 80.0)
    won = torch.cat([torch.full((n,), 80.0 * rate_old), torch.full((n,), 80.0 * rate_new)])
    season = torch.cat([torch.full((n,), 2023), torch.full((n,), 2024)]).to(torch.int64)
    return x, x.clone(), won, svpt, season


def test_season_offsets_anchor_on_the_last_season():
    off = SeasonOffsets([2024, 2022, 2023, 2022], {2022: 0.2, 2023: 0.4, 2024: 0.5})
    assert off.anchor == 2024
    assert off.level.shape == (3,)
    out = off(torch.tensor([2024, 2022, 2023, 2024]))
    assert out.tolist() == pytest.approx([0.5, 0.2, 0.4, 0.5])
    assert off.anchor_level() == pytest.approx(0.5)
    assert off.as_dict() == {2022: pytest.approx(-0.3), 2023: pytest.approx(-0.1), 2024: 0.0}
    with pytest.raises(ValueError):
        off(torch.tensor([2021]))
    assert SeasonOffsets([2020]).level.tolist() == [0.0]


def test_train_surface_anchors_mu_on_the_last_season():
    x_i, x_j, won, svpt, season = _two_seasons(0.60, 0.66)
    pooled = train_surface(x_i, x_j, won, svpt, epochs=60, batch_size=64, verbose=False)
    anchored = train_surface(x_i, x_j, won, svpt, season=season, epochs=60, batch_size=64,
                             verbose=False)
    # Run 0 behaviour: mu is the pooled level
    assert math.isclose(float(pooled(x_i[0], x_j[0])), 0.63, abs_tol=0.01)
    assert pooled.fitted_offsets is None
    # Run 1 behaviour: mu is the 2024 level, 2023 carries its own deficit
    assert math.isclose(float(anchored(x_i[0], x_j[0])), 0.66, abs_tol=0.01)
    d = anchored.fitted_offsets
    assert set(d) == {2023, 2024} and d[2024] == 0.0
    assert math.isclose(d[2023], init_mu_from_rate(0.60) - init_mu_from_rate(0.66), abs_tol=0.06)
    # the cards were all zero, so nothing but mu (and delta) may have moved
    assert float(anchored.a.detach().abs().max()) == 0.0
    assert float(anchored.W.detach().abs().max()) == 0.0


def test_offsets_never_reach_the_saved_bundle(tmp_path, capsys):
    x_i, x_j, won, svpt, season = _two_seasons(0.60, 0.66, n=16)
    batches = {"Hard": {"x_i": x_i, "x_j": x_j, "won": won, "svpt": svpt, "season": season}}
    bundle = train_all_surfaces(batches, torch.zeros(8), torch.ones(8), train_through=2024,
                                epochs=2, verbose=False)
    capsys.readouterr()
    assert bundle.total_parameters() == 81
    state = bundle.state_dict()
    assert set(state["surfaces"]["Hard"]) == {"mu", "a", "b", "W"}
    path = str(tmp_path / "model.pt")
    bundle.save(path)
    loaded = SurfaceBundle.load(path)
    assert loaded.total_parameters() == 81
    assert not hasattr(loaded.surfaces["Hard"], "fitted_offsets") or loaded.surfaces["Hard"].fitted_offsets is None


def test_train_surface_rejects_mismatched_seasons():
    x_i, x_j, won, svpt = _average_players(8)
    with pytest.raises(ValueError):
        train_surface(x_i, x_j, won, svpt, season=torch.tensor([2024, 2024]), epochs=1, verbose=False)


def test_evaluate_holdout_reports_the_last_season_baseline():
    x_i, x_j, won, svpt = _average_players(8, rate=0.66)
    m = BilinearServeModel(init_mu=init_mu_from_rate(0.66))
    r = evaluate_holdout(m, {"x_i": x_i, "x_j": x_j, "won": won, "svpt": svpt},
                         train_rate=0.63, last_rate=0.655)
    assert "nll_last" in r and "point_mae_last" in r
    assert r["nll_last"] < r["nll_constant"]            # the fresher constant is the harder bar
    assert r["point_mae_last"] < r["point_mae_constant"]
    assert r["nll"] < r["nll_last"]
    r0 = evaluate_holdout(m, {"x_i": x_i, "x_j": x_j, "won": won, "svpt": svpt}, train_rate=0.63)
    assert "nll_last" not in r0
