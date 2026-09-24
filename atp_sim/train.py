"""Fit one bilinear serve model per surface (DESIGN.md §§5, 9).

Run 1 adds a training-only per-season offset to mu (see `SeasonOffsets`). Pass the rows'
seasons to `train_surface` and mu is anchored on the last of them; leave them out and the
fit is the Run 0 all-era fit.
"""

from __future__ import annotations

from typing import Iterable

import torch
from torch.utils.data import DataLoader, TensorDataset

from .data import LIVE_SURFACES
from .model import (
    BilinearServeModel,
    SeasonOffsets,
    SurfaceBundle,
    binomial_nll,
    init_mu_from_rate,
    regularised_loss,
)


def _serve_rate(won: torch.Tensor, svpt: torch.Tensor) -> float:
    return float(won.sum() / svpt.sum().clamp_min(1.0))


def _offset_summary(offsets: SeasonOffsets) -> str:
    d = offsets.as_dict()
    first, last = min(d), offsets.anchor
    before = max(s for s in d if s < last) if len(d) > 1 else last
    return f"delta[{first}]={d[first]:+.3f} … delta[{before}]={d[before]:+.3f}  (delta[{last}]=0)"


def train_surface(
    x_i: torch.Tensor,
    x_j: torch.Tensor,
    won: torch.Tensor,
    svpt: torch.Tensor,
    *,
    season: torch.Tensor | None = None,
    epochs: int = 40,
    batch_size: int = 2048,
    lr: float = 0.05,
    l2_ab: float = 1e-4,
    l2_W: float = 1e-2,
    seed: int = 0,
    verbose: bool = True,
    lr_decay: bool = False,
) -> BilinearServeModel:
    """Mini-batch Adam on binomial NLL with heavy W regularisation.

    With `season`, every season (the last included) gets a training-only level, started at
    its own observed rate, while mu is held at 0; once training ends, mu takes the last
    season's level. The returned model never contains delta;
    the fitted values are kept on `model.fitted_offsets` (a plain dict) for reporting.

    `lr_decay` cools the learning rate linearly to 5% of `lr` over the run, so the fit
    settles instead of jittering by about `lr` in log-odds around the optimum.
    """
    torch.manual_seed(seed)
    offsets: SeasonOffsets | None = None
    if season is not None:
        if len(season) != len(won):
            raise ValueError("season must have one entry per row")
        season = season.to(torch.int64)
        ids = sorted(set(season.tolist()))
        # like mu, each season's level starts at its observed log-odds
        init = {s: init_mu_from_rate(_serve_rate(won[season == s], svpt[season == s])) for s in ids}
        offsets = SeasonOffsets(ids, init)
        # mu is held at 0 while the per-season levels carry the intercept; it is set to the
        # anchor season's level once training ends
        model = BilinearServeModel(init_mu=0.0)
        groups = [
            {"params": [model.a, model.b], "weight_decay": 0.0},
            {"params": [model.W], "weight_decay": 0.0},
            {"params": [offsets.level], "weight_decay": 0.0},
        ]
    else:
        model = BilinearServeModel(init_mu=init_mu_from_rate(_serve_rate(won, svpt)))
        groups = [
            {"params": [model.mu, model.a, model.b], "weight_decay": 0.0},
            {"params": [model.W], "weight_decay": 0.0},
        ]
    opt = torch.optim.Adam(groups, lr=lr)
    sched = (torch.optim.lr_scheduler.LinearLR(opt, start_factor=1.0, end_factor=0.05, total_iters=epochs)
             if lr_decay else None)

    season_col = season.to(torch.int64) if season is not None else torch.zeros(len(won), dtype=torch.int64)
    loader = DataLoader(
        TensorDataset(x_i, x_j, won, svpt, season_col),
        batch_size=batch_size,
        shuffle=True,
    )

    def predict(bx_i, bx_j, bseason):
        z = model.logit(bx_i, bx_j)
        if offsets is not None:
            z = z + offsets(bseason)
        return torch.sigmoid(z)

    for epoch in range(1, epochs + 1):
        total = 0.0
        n = 0
        for bx_i, bx_j, bwon, bsvpt, bseason in loader:
            opt.zero_grad()
            p = predict(bx_i, bx_j, bseason)
            loss = regularised_loss(model, p, bwon, bsvpt, l2_ab=l2_ab, l2_W=l2_W)
            loss.backward()
            opt.step()
            total += float(loss.item())
            n += 1
        if sched is not None:
            sched.step()
        if verbose and (epoch == 1 or epoch % 5 == 0 or epoch == epochs):
            with torch.no_grad():
                p_all = predict(x_i, x_j, season_col)
                mae = ((p_all * svpt) - won).abs().sum() / svpt.sum()
            extra = f"  {_offset_summary(offsets)}" if offsets is not None else ""
            mu_now = offsets.anchor_level() if offsets is not None else float(model.mu.detach())
            print(
                f"  epoch {epoch:3d}/{epochs}  loss={total / max(n, 1):.1f}  "
                f"point-MAE={mae:.4f}  mu={mu_now:.3f}{extra}"
            )
    if offsets is not None:
        with torch.no_grad():
            model.mu.fill_(offsets.anchor_level())
    model.fitted_offsets = offsets.as_dict() if offsets is not None else None
    return model


def train_all_surfaces(
    batches: dict[str, dict[str, torch.Tensor]],
    card_mean: torch.Tensor,
    card_std: torch.Tensor,
    surfaces: Iterable[str] = LIVE_SURFACES,
    train_through: int | None = None,
    **train_kwargs,
) -> SurfaceBundle:
    models: dict[str, BilinearServeModel] = {}
    for surface in surfaces:
        if surface not in batches:
            continue
        b = batches[surface]
        print(f"\n=== {surface} ({len(b['won']):,} rows) ===")
        models[surface] = train_surface(
            b["x_i"], b["x_j"], b["won"], b["svpt"], season=b.get("season"), **train_kwargs
        )
    if not models:
        raise ValueError("No surface batches to train on")
    bundle = SurfaceBundle(surfaces=models, card_mean=card_mean, card_std=card_std,
                           train_through=train_through)
    assert bundle.total_parameters() == 81 * len(models)
    return bundle


def evaluate_holdout(
    model: BilinearServeModel,
    batch: dict[str, torch.Tensor],
    train_rate: float,
    last_rate: float | None = None,
) -> dict[str, float]:
    """Score one surface on rows the fit never saw.

    Two constant baselines: `train_rate` (the pooled training-era rate, Run 0's straw man)
    and, when given, `last_rate` (the last training season's rate, the bar an anchored
    mu has to beat).
    """
    with torch.no_grad():
        p = model(batch["x_i"], batch["x_j"])
        won, svpt = batch["won"], batch["svpt"]
        const = torch.full_like(p, train_rate)
        out = {
            "rows": float(len(won)),
            "actual": float(won.sum() / svpt.sum()),
            "predicted": float((p * svpt).sum() / svpt.sum()),
            "nll": float(binomial_nll(p, won, svpt)),
            "nll_constant": float(binomial_nll(const, won, svpt)),
            "point_mae": float(((p * svpt) - won).abs().sum() / svpt.sum()),
            "point_mae_constant": float(((const * svpt) - won).abs().sum() / svpt.sum()),
        }
        if last_rate is not None:
            last = torch.full_like(p, last_rate)
            out["nll_last"] = float(binomial_nll(last, won, svpt))
            out["point_mae_last"] = float(((last * svpt) - won).abs().sum() / svpt.sum())
        return out


def evaluate_terms(
    model: BilinearServeModel,
    x_i: torch.Tensor,
    x_j: torch.Tensor,
) -> dict[str, float]:
    """Mean absolute contribution of each formula layer (DESIGN.md §7)."""
    with torch.no_grad():
        t = model.term_breakdown(x_i, x_j)
    return {
        "mean_|serve|": float(t["serve"].abs().mean()),
        "mean_|return|": float(t["return"].abs().mean()),
        "mean_|interaction|": float(t["interaction"].abs().mean()),
        "mean_p": float(t["p"].mean()),
    }
