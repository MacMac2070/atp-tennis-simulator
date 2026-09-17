"""Bilinear serve model (design §§6–9).

    z = mu + a·x_i - b·x_j + x_iᵀ W x_j
    p = sigmoid(z)

81 parameters per surface; three surfaces → 243 numbers total.
Form cards are frozen inputs. Only mu, a, b, W are learned.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from .form_cards import ATTR_NAMES, N_ATTRS

__all__ = ["ATTR_NAMES", "N_ATTRS", "BilinearServeModel", "SurfaceBundle"]


class BilinearServeModel(nn.Module):
    """Point-win probability on one surface."""

    def __init__(self, n_attrs: int = N_ATTRS, init_mu: float = 0.0):
        super().__init__()
        self.n_attrs = n_attrs
        self.mu = nn.Parameter(torch.tensor(float(init_mu)))
        self.a = nn.Parameter(torch.zeros(n_attrs))
        self.b = nn.Parameter(torch.zeros(n_attrs))
        self.W = nn.Parameter(torch.zeros(n_attrs, n_attrs))

    def logit(self, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
        """Log-odds z for server card x_i vs returner card x_j."""
        serve = (self.a * x_i).sum(dim=-1)
        ret = (self.b * x_j).sum(dim=-1)
        interaction = torch.einsum("...k,kl,...l->...", x_i, self.W, x_j)
        return self.mu + serve - ret + interaction

    def forward(self, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.logit(x_i, x_j))

    def term_breakdown(
        self, x_i: torch.Tensor, x_j: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        serve = (self.a * x_i).sum(dim=-1)
        ret = (self.b * x_j).sum(dim=-1)
        interaction = torch.einsum("...k,kl,...l->...", x_i, self.W, x_j)
        z = self.mu + serve - ret + interaction
        return {
            "mu": self.mu.expand_as(z),
            "serve": serve,
            "return": ret,
            "interaction": interaction,
            "z": z,
            "p": torch.sigmoid(z),
        }

    def n_parameters(self) -> int:
        return 1 + 2 * self.n_attrs + self.n_attrs * self.n_attrs


@dataclass
class SurfaceBundle:
    """The three independently fitted surface models (243 params)."""

    surfaces: dict[str, BilinearServeModel]
    card_mean: torch.Tensor
    card_std: torch.Tensor

    def predict(self, surface: str, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
        return self.surfaces[surface](x_i, x_j)

    def state_dict(self) -> dict:
        return {
            "surfaces": {s: m.state_dict() for s, m in self.surfaces.items()},
            "card_mean": self.card_mean,
            "card_std": self.card_std,
            "attr_names": list(ATTR_NAMES),
        }

    @classmethod
    def from_state_dict(cls, state: dict) -> "SurfaceBundle":
        surfaces = {}
        for name, sd in state["surfaces"].items():
            m = BilinearServeModel()
            m.load_state_dict(sd)
            surfaces[name] = m
        return cls(
            surfaces=surfaces,
            card_mean=state["card_mean"],
            card_std=state["card_std"],
        )

    def save(self, path: str) -> None:
        torch.save(self.state_dict(), path)

    @classmethod
    def load(cls, path: str, map_location: str | None = None) -> "SurfaceBundle":
        state = torch.load(path, map_location=map_location, weights_only=False)
        return cls.from_state_dict(state)

    def total_parameters(self) -> int:
        return sum(m.n_parameters() for m in self.surfaces.values())


def binomial_nll(
    p: torch.Tensor,
    won: torch.Tensor,
    played: torch.Tensor,
) -> torch.Tensor:
    """Mean per-point negative log-likelihood (binomial)."""
    p = p.clamp(1e-6, 1 - 1e-6)
    total = -(won * torch.log(p) + (played - won) * torch.log(1 - p)).sum()
    return total / played.sum().clamp_min(1.0)


def regularised_loss(
    model: BilinearServeModel,
    p: torch.Tensor,
    won: torch.Tensor,
    played: torch.Tensor,
    l2_ab: float = 1e-4,
    l2_W: float = 1e-2,
) -> torch.Tensor:
    """Per-point NLL plus heavy L2 on W (design §7) and light L2 on a, b."""
    nll = binomial_nll(p, won, played)
    reg = (
        l2_ab * (model.a.pow(2).sum() + model.b.pow(2).sum())
        + l2_W * model.W.pow(2).sum()
    )
    return nll + reg


def init_mu_from_rate(serve_win_rate: float) -> float:
    """mu starts at the observed tour-average log-odds (design §7)."""
    rate = min(max(serve_win_rate, 1e-4), 1 - 1e-4)
    return float(torch.logit(torch.tensor(rate)))
