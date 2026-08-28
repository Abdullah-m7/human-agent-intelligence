"""Alternative Stage-002 models for the Agentic Bottleneck paper.

These models are designed to test whether Stage-001 role-migration patterns are
artifacts of two simplifying assumptions:

1. independence between human and agent task errors; and
2. random human gating rather than confidence-selective review.

They remain system-level computational models. No parameter is an IQ score and
no output should be interpreted as a prevalence estimate for real humans.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import log, sqrt

import numpy as np

from src.agentic_bottleneck import Params, effective_agent


def bernoulli_joint(
    p_agent: float, p_human: float, requested_corr: float
) -> tuple[float, float, float, float, float]:
    """Return a valid 2x2 Bernoulli joint distribution.

    ``requested_corr`` is converted to a candidate P(A=1,H=1) and projected to
    the Fréchet bounds when the requested correlation is infeasible for the
    supplied marginals. The final element is the realized correlation.
    """
    pa = min(1.0, max(0.0, p_agent))
    ph = min(1.0, max(0.0, p_human))
    denom = sqrt(pa * (1.0 - pa) * ph * (1.0 - ph))
    lower = max(0.0, pa + ph - 1.0)
    upper = min(pa, ph)
    if denom == 0.0:
        p11 = pa * ph
        realized = 0.0
    else:
        candidate = pa * ph + requested_corr * denom
        p11 = min(upper, max(lower, candidate))
        realized = (p11 - pa * ph) / denom
    p10 = pa - p11
    p01 = ph - p11
    p00 = 1.0 - p11 - p10 - p01
    return p11, p10, p01, p00, realized


def correlated_gated_accuracy(p: Params, error_corr: float) -> float:
    """Expected correctness of human gating with correlated human/agent errors."""
    a = effective_agent(p)
    p11, _, p01, _, _ = bernoulli_joint(a, p.human, error_corr)
    # Correct agent output is preserved with specificity Q. If falsely rejected,
    # the fallback is correct only in the A-correct/H-correct joint state.
    # Wrong agent output is rescued only when detected and the human is correct.
    return a * p.specificity + (1.0 - p.specificity) * p11 + p.verification * p01


def correlated_joint_accuracy(p: Params, error_corr: float) -> float:
    a = effective_agent(p)
    gate = correlated_gated_accuracy(p, error_corr)
    return p.autonomy * a + (1.0 - p.autonomy) * gate


def correlated_sensitivity(
    p: Params, error_corr: float, field: str, eps: float = 1e-5
) -> float:
    x = getattr(p, field)
    lo = max(0.0, x - eps)
    hi = min(1.0, x + eps)
    if hi == lo:
        return 0.0
    p_lo = replace(p, **{field: lo})
    p_hi = replace(p, **{field: hi})
    return (
        correlated_joint_accuracy(p_hi, error_corr)
        - correlated_joint_accuracy(p_lo, error_corr)
    ) / (hi - lo)


@dataclass(frozen=True)
class SelectiveReviewParams:
    agent: float
    human: float
    specification: float
    verification: float
    specificity: float
    review_threshold: float
    beta_spec: float = 0.20
    difficulty_scale: float = 1.20
    review_sharpness: float = 35.0
    difficulty_points: int = 101


def _clip_probability(x: float) -> float:
    return min(1.0 - 1e-8, max(1e-8, x))


def _logit(p: float) -> float:
    p = _clip_probability(p)
    return log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-x))


def selective_profile(p: SelectiveReviewParams) -> dict[str, float]:
    """Average accuracy/autonomy under difficulty-sensitive selective review.

    The agent and human face the same evenly weighted latent difficulty grid.
    The review policy is calibrated to the agent's probability of being correct:
    lower-confidence items are more likely to be reviewed. This creates an
    endogenous autonomy rate rather than mixing review and autonomy at random.
    """
    base_agent = _clip_probability(
        p.agent + p.beta_spec * (p.specification - 0.5)
    )
    base_human = _clip_probability(p.human)
    difficulty = np.linspace(-1.0, 1.0, p.difficulty_points)
    pa = _sigmoid(_logit(base_agent) - p.difficulty_scale * difficulty)
    ph = _sigmoid(_logit(base_human) - p.difficulty_scale * difficulty)

    # A smooth threshold prevents finite-difference sensitivities from being
    # dominated by discontinuous routing changes at one exact confidence value.
    review_prob = _sigmoid(
        p.review_sharpness * (p.review_threshold - pa)
    )
    gate = pa * (p.specificity + (1.0 - p.specificity) * ph)
    gate += (1.0 - pa) * p.verification * ph
    joint = (1.0 - review_prob) * pa + review_prob * gate

    return {
        "joint_accuracy": float(np.mean(joint)),
        "effective_autonomy": float(np.mean(1.0 - review_prob)),
        "mean_agent_accuracy": float(np.mean(pa)),
        "mean_human_accuracy": float(np.mean(ph)),
        "mean_reviewed_accuracy": float(np.sum(review_prob * gate) / max(np.sum(review_prob), 1e-12)),
        "review_fraction": float(np.mean(review_prob)),
    }


def selective_sensitivity(
    p: SelectiveReviewParams, field: str, eps: float = 1e-5
) -> float:
    x = getattr(p, field)
    lo = max(0.0, x - eps)
    hi = min(1.0, x + eps)
    if hi == lo:
        return 0.0
    p_lo = replace(p, **{field: lo})
    p_hi = replace(p, **{field: hi})
    return (
        selective_profile(p_hi)["joint_accuracy"]
        - selective_profile(p_lo)["joint_accuracy"]
    ) / (hi - lo)


def selective_sensitivity_shares(p: SelectiveReviewParams) -> dict[str, float]:
    fields = ("human", "specification", "verification", "specificity")
    values = {field: abs(selective_sensitivity(p, field)) for field in fields}
    total = sum(values.values())
    if total == 0.0:
        return {field: 0.0 for field in fields}
    return {field: value / total for field, value in values.items()}
