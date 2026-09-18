"""Fit one bilinear serve model per surface (design §§5, 9)."""

from __future__ import annotations

from typing import Iterable

import torch
from torch.utils.data import DataLoader, TensorDataset

from .data import LIVE_SURFACES
from .model import (
    BilinearServeModel,
    SurfaceBundle,
    init_mu_from_rate,
    regularised_loss,
)


def _serve_rate(won: torch.Tensor, svpt: torch.Tensor) -> float:
    return float(won.sum() / svpt.sum().clamp_min(1.0))


def train_surface(
    x_i: torch.Tensor,
    x_j: torch.Tensor,
    won: torch.Tensor,
    svpt: torch.Tensor,
    *,
    epochs: int = 40,
    batch_size: int = 2048,
    lr: float = 0.05,
    l2_ab: float = 1e-4,
    l2_W: float = 1e-2,
    seed: int = 0,
    verbose: bool = True,
) -> BilinearServeModel:
    """SGD on binomial NLL with heavy W regularisation."""
    torch.manual_seed(seed)
    model = BilinearServeModel(init_mu=init_mu_from_rate(_serve_rate(won, svpt)))
    opt = torch.optim.Adam(
        [
            {"params": [model.mu, model.a, model.b], "weight_decay": 0.0},
            {"params": [model.W], "weight_decay": 0.0},
        ],
        lr=lr,
    )

    loader = DataLoader(
        TensorDataset(x_i, x_j, won, svpt),
        batch_size=batch_size,
        shuffle=True,
    )

    for epoch in range(1, epochs + 1):
        total = 0.0
        n = 0
        for bx_i, bx_j, bwon, bsvpt in loader:
            opt.zero_grad()
            p = model(bx_i, bx_j)
            loss = regularised_loss(model, p, bwon, bsvpt, l2_ab=l2_ab, l2_W=l2_W)
            loss.backward()
            opt.step()
            total += float(loss.item())
            n += 1
        if verbose and (epoch == 1 or epoch % 5 == 0 or epoch == epochs):
            with torch.no_grad():
                p_all = model(x_i, x_j)
                mae = ((p_all * svpt) - won).abs().sum() / svpt.sum()
            print(
                f"  epoch {epoch:3d}/{epochs}  loss={total / max(n, 1):.1f}  "
                f"point-MAE={mae:.4f}  mu={float(model.mu.detach()):.3f}"
            )
    return model


def train_all_surfaces(
    batches: dict[str, dict[str, torch.Tensor]],
    card_mean: torch.Tensor,
    card_std: torch.Tensor,
    surfaces: Iterable[str] = LIVE_SURFACES,
    **train_kwargs,
) -> SurfaceBundle:
    models: dict[str, BilinearServeModel] = {}
    for surface in surfaces:
        if surface not in batches:
            continue
        b = batches[surface]
        print(f"\n=== {surface} ({len(b['won']):,} rows) ===")
        models[surface] = train_surface(
            b["x_i"], b["x_j"], b["won"], b["svpt"], **train_kwargs
        )
    if not models:
        raise ValueError("No surface batches to train on")
    bundle = SurfaceBundle(surfaces=models, card_mean=card_mean, card_std=card_std)
    assert bundle.total_parameters() == 81 * len(models)
    return bundle


def evaluate_terms(
    model: BilinearServeModel,
    x_i: torch.Tensor,
    x_j: torch.Tensor,
) -> dict[str, float]:
    """Mean absolute contribution of each formula layer (design §7)."""
    with torch.no_grad():
        t = model.term_breakdown(x_i, x_j)
    return {
        "mean_|serve|": float(t["serve"].abs().mean()),
        "mean_|return|": float(t["return"].abs().mean()),
        "mean_|interaction|": float(t["interaction"].abs().mean()),
        "mean_p": float(t["p"].mean()),
    }
