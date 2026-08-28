"""Receiver-contract accounting for Human+Agent systems.

The human receiver may have a first-pass success probability and a higher
retry-enabled success probability. Agent autonomy can therefore displace not
only an initial human judgment but also the receiver's opportunity to recover.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def _vec(x, name: str, binary: bool = False) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if not np.isfinite(a).all():
        raise ValueError(f"{name} contains non-finite values")
    if binary:
        if not np.isin(a, [0.0, 1.0]).all():
            raise ValueError(f"{name} must be binary")
    elif ((a < 0) | (a > 1)).any():
        raise ValueError(f"{name} must lie in [0,1]")
    return a


def receiver_contract_profile(
    agent_correct,
    agent_act,
    human_first,
    human_final,
) -> dict[str, Any]:
    """Return task-balanced receiver/autonomy accounting.

    `human_first` and `human_final` may be binary outcomes for one receiver or
    empirical success probabilities for a receiver stratum on each task.
    `human_final` must weakly dominate `human_first` task by task because retry
    is treated as an expanded opportunity set rather than a different person.
    """
    c = _vec(agent_correct, "agent_correct", binary=True)
    a = _vec(agent_act, "agent_act", binary=True)
    h1 = _vec(human_first, "human_first")
    hf = _vec(human_final, "human_final")
    if not (c.shape == a.shape == h1.shape == hf.shape):
        raise ValueError("all receiver-contract arrays must share shape")
    if len(c) == 0:
        raise ValueError("receiver-contract arrays must not be empty")
    if np.any(hf + 1e-12 < h1):
        raise ValueError("human_final must weakly dominate human_first task by task")

    j1 = a * c + (1 - a) * h1
    jf = a * c + (1 - a) * hf
    recovery = hf - h1

    def policy_terms(h: np.ndarray) -> dict[str, float]:
        beneficial = float(np.mean(a * c * (1 - h)))
        harmful = float(np.mean(a * (1 - c) * h))
        net = beneficial - harmful
        joint = float(np.mean(a * c + (1 - a) * h))
        human = float(np.mean(h))
        if not np.isclose(joint, human + net, atol=1e-12):
            raise AssertionError("receiver-relative routing identity failed")
        return {
            "human_baseline": human,
            "joint_performance": joint,
            "beneficial_autonomy_mass": beneficial,
            "harmful_displacement_mass": harmful,
            "net_routing_value": net,
        }

    first = policy_terms(h1)
    final = policy_terms(hf)
    recovery_potential = float(np.mean(recovery))
    recovery_captured = float(np.mean((1 - a) * recovery))
    recovery_suppressed = float(np.mean(a * recovery))
    if not np.isclose(recovery_potential, recovery_captured + recovery_suppressed, atol=1e-12):
        raise AssertionError("recovery accounting identity failed")
    if not np.isclose(float(np.mean(jf - j1)), recovery_captured, atol=1e-12):
        raise AssertionError("joint retry-value identity failed")

    return {
        "n_tasks": int(len(c)),
        "agent_accuracy": float(np.mean(c)),
        "act_coverage": float(np.mean(a)),
        "one_shot": first,
        "retry_enabled": final,
        "human_recovery_potential": recovery_potential,
        "joint_recovery_value": recovery_captured,
        "recovery_suppression_mass": recovery_suppressed,
        "recovery_capture_ratio": (
            recovery_captured / recovery_potential if recovery_potential > 0 else None
        ),
    }
