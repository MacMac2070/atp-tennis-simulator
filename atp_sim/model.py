"""Bilinear serve model (DESIGN.md §§6 to 9).

    z = mu + a·x_i - b·x_j + x_iᵀ W x_j
    p = sigmoid(z)

81 parameters per surface; three surfaces → 243 numbers total.
Form cards are frozen inputs. Only mu, a, b, W are learned.

Training only (Run 1): z = mu + delta[season] + ... with delta fixed at 0 for the last
training season, so mu is that season's level rather than the all-era average. The cards
are standardised per season and carry no level of their own. `SeasonOffsets` holds the per-season levels behind delta;
it is never saved, so the model above is unchanged at prediction time.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from .form_cards import ATTR_NAMES, N_ATTRS

__all__ = ["ATTR_NAMES", "N_ATTRS", "BilinearServeModel", "SeasonOffsets", "SurfaceBundle"]


class SeasonOffsets(nn.Module):
    """One intercept per season, used only while training.

    While it is in play the model's own mu is held at 0 and the row's season supplies the
    whole intercept: z = level[season] + a·x_i − b·x_j + x_iᵀ W x_j. When training ends,
    mu is set to the last season's level (the anchor) and this module is dropped, so the
    saved model is unchanged and mu means "the level of the anchor season". Reported as
    delta = level − level[anchor], which is 0 for the anchor by construction.

    Why a full level per season rather than mu plus a delta: each level is then set by its
    own season's rows alone, which Adam handles well. mu and a per-season delta would be
    nearly collinear (only the anchor's rows separate them) and converge very slowly.
    """

    def __init__(self, seasons, init_levels: dict[int, float] | None = None):
        super().__init__()
        ids = sorted({int(s) for s in seasons})
        if not ids:
            raise ValueError("SeasonOffsets needs at least one season")
        self.register_buffer("season_ids", torch.tensor(ids, dtype=torch.int64))
        self.anchor = ids[-1]
        start = torch.zeros(len(ids))
        if init_levels is not None:
            start = torch.tensor([float(init_levels[s]) for s in ids])
        self.level = nn.Parameter(start)

    def forward(self, season: torch.Tensor) -> torch.Tensor:
        """The intercept for each row's season. Unknown seasons are an error."""
        season = season.to(torch.int64)
        idx = torch.searchsorted(self.season_ids, season).clamp_max(len(self.season_ids) - 1)
        if not bool((self.season_ids[idx] == season).all()):
            raise ValueError("a row's season was not seen when the offsets were built")
        return self.level[idx]

    def anchor_level(self) -> float:
        return float(self.level.detach()[-1])

    def as_dict(self) -> dict[int, float]:
        """{season: delta relative to the anchor}, anchor included as 0.0."""
        d = (self.level - self.level[-1]).detach().tolist()
        return {int(s): float(v) for s, v in zip(self.season_ids.tolist(), d)}


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
    train_through: int | None = None  # last season the fit saw; None means unrecorded

    def predict(self, surface: str, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
        return self.surfaces[surface](x_i, x_j)

    def state_dict(self) -> dict:
        return {
            "surfaces": {s: m.state_dict() for s, m in self.surfaces.items()},
            "card_mean": self.card_mean,
            "card_std": self.card_std,
            "attr_names": list(ATTR_NAMES),
            "train_through": self.train_through,
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
            train_through=state.get("train_through"),
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
    """Per-point NLL plus heavy L2 on W (DESIGN.md §7) and light L2 on a, b.

    Season levels (`SeasonOffsets`) are deliberately not regularised: each rests on
    thousands of rows, and even a light penalty summed over 33 seasons pulls the
    anchor season's level measurably off its data.
    """
    nll = binomial_nll(p, won, played)
    reg = (
        l2_ab * (model.a.pow(2).sum() + model.b.pow(2).sum())
        + l2_W * model.W.pow(2).sum()
    )
    return nll + reg


def init_mu_from_rate(serve_win_rate: float) -> float:
    """mu starts at the observed tour-average log-odds (DESIGN.md §7)."""
    rate = min(max(serve_win_rate, 1e-4), 1 - 1e-4)
    return float(torch.logit(torch.tensor(rate)))
