"""Stylized human-agent bottleneck model for Paper 01.

This module models system-level capabilities. It does not simulate or infer human IQ.
"""

from __future__ import annotations

import argparse
import csv
import itertools
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class Params:
    agent: float
    human: float
    specification: float
    verification: float
    specificity: float
    autonomy: float
    beta_spec: float = 0.20


def clip01(x: float) -> float:
    return min(1.0, max(0.0, x))


def effective_agent(p: Params) -> float:
    """Agent accuracy after upstream specification quality changes the task fit."""
    return clip01(p.agent + p.beta_spec * (p.specification - 0.5))


def gated_accuracy(p: Params) -> float:
    """Expected correctness when the human review gate is active."""
    a = effective_agent(p)
    preserve_correct = a * (p.specificity + (1.0 - p.specificity) * p.human)
    rescue_error = (1.0 - a) * p.verification * p.human
    return preserve_correct + rescue_error


def joint_accuracy(p: Params) -> float:
    """Mix autonomous execution and human-gated execution."""
    a = effective_agent(p)
    return p.autonomy * a + (1.0 - p.autonomy) * gated_accuracy(p)


def sensitivity(p: Params, field: str, eps: float = 1e-5) -> float:
    """Finite-difference derivative of joint accuracy with respect to one field."""
    x = getattr(p, field)
    lo = max(0.0, x - eps)
    hi = min(1.0, x + eps)
    if hi == lo:
        return 0.0
    p_lo = replace(p, **{field: lo})
    p_hi = replace(p, **{field: hi})
    return (joint_accuracy(p_hi) - joint_accuracy(p_lo)) / (hi - lo)


def sensitivity_shares(p: Params) -> dict[str, float]:
    fields = ("human", "specification", "verification", "specificity")
    vals = {f: abs(sensitivity(p, f)) for f in fields}
    total = sum(vals.values())
    if total == 0:
        return {f: 0.0 for f in fields}
    return {f: vals[f] / total for f in fields}


def iter_stage001(beta_spec: float = 0.20):
    grid = {
        "agent": [0.55, 0.70, 0.85, 0.95],
        "human": [0.45, 0.60, 0.75, 0.90],
        "specification": [0.30, 0.50, 0.70, 0.90],
        "verification": [0.30, 0.50, 0.70, 0.90],
        "specificity": [0.70, 0.85, 0.95],
        "autonomy": [0.00, 0.25, 0.50, 0.75, 1.00],
    }
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        yield Params(**dict(zip(keys, values)), beta_spec=beta_spec)


def row(p: Params) -> dict[str, float]:
    a_eff = effective_agent(p)
    p_gate = gated_accuracy(p)
    j = joint_accuracy(p)
    sens = {f: sensitivity(p, f) for f in ("human", "specification", "verification", "specificity")}
    shares = sensitivity_shares(p)
    return {
        **p.__dict__,
        "agent_effective": a_eff,
        "gated_accuracy": p_gate,
        "joint_accuracy": j,
        "gating_gain_vs_full_autonomy": p_gate - a_eff,
        **{f"dJ_d_{k}": v for k, v in sens.items()},
        **{f"share_{k}": v for k, v in shares.items()},
    }


def write_stage001(path: Path, beta_spec: float = 0.20) -> int:
    rows = [row(p) for p in iter_stage001(beta_spec)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/stage001_grid.csv"))
    parser.add_argument("--beta-spec", type=float, default=0.20)
    args = parser.parse_args()
    n = write_stage001(args.output, args.beta_spec)
    print(f"wrote {n} rows to {args.output}")


if __name__ == "__main__":
    main()
