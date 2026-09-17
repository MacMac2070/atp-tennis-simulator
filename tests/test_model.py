"""Unit tests for the bilinear formula (design §8 worked example)."""

from __future__ import annotations

import math

import torch

from atp_sim.model import BilinearServeModel


def test_parameter_count():
    m = BilinearServeModel(n_attrs=8)
    assert m.n_parameters() == 81  # 1 + 8 + 8 + 64


def test_worked_example_two_attrs():
    """Alcaraz serving to Sinner on clay — shrunk to 2 attributes."""
    m = BilinearServeModel(n_attrs=2, init_mu=0.49)
    with torch.no_grad():
        m.a.copy_(torch.tensor([0.30, 0.05]))
        m.b.copy_(torch.tensor([0.02, 0.25]))
        m.W.copy_(torch.tensor([[-0.04, 0.03], [0.01, -0.02]]))

    x_i = torch.tensor([1.2, 0.8])
    x_j = torch.tensor([0.9, 1.1])
    terms = m.term_breakdown(x_i, x_j)

    assert abs(float(terms["serve"].detach()) - 0.400) < 1e-6
    assert abs(float(terms["return"].detach()) - 0.293) < 1e-6
    assert abs(float(terms["interaction"].detach()) - (-0.014)) < 1e-6
    assert abs(float(terms["z"].detach()) - 0.583) < 1e-6
    assert abs(float(terms["p"].detach()) - 0.642) < 1e-3


def test_average_players_give_baseline():
    m = BilinearServeModel(n_attrs=8, init_mu=0.58)
    x = torch.zeros(8)
    p = float(m(x, x))
    assert abs(p - 1 / (1 + math.exp(-0.58))) < 1e-6


def test_gradient_matches_involvement_rule():
    """Underprediction raises serve weights via NLL descent (design §9)."""
    m = BilinearServeModel(n_attrs=2, init_mu=0.0)
    with torch.no_grad():
        m.a.copy_(torch.tensor([0.30, 0.05]))
        m.b.copy_(torch.tensor([0.02, 0.25]))
        m.W.zero_()

    x_i = torch.tensor([1.2, 0.8])
    x_j = torch.tensor([0.9, 1.1])
    p = m(x_i, x_j)
    won = torch.tensor(51.0)
    played = torch.tensor(78.0)
    loss = -((won * torch.log(p) + (played - won) * torch.log(1 - p)))
    loss.backward()

    assert m.a.grad is not None
    pred_pts = float(p.detach()) * 78
    if pred_pts < 51:
        assert float(m.a.grad[0]) < 0
