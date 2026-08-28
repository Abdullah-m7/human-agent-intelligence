"""Core metrics for the Human–Agent Capability Twin benchmark."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class AgentTaskState:
    correct: int
    act: int
    evidence: float = 0.0

    def __post_init__(self) -> None:
        if self.correct not in (0, 1) or self.act not in (0, 1):
            raise ValueError("correct and act must be binary")


def routed_outcome(agent_correct: np.ndarray, agent_act: np.ndarray, human_correct: np.ndarray) -> np.ndarray:
    """Return task correctness for ACT/DEFER routing."""
    a = np.asarray(agent_correct, dtype=int)
    act = np.asarray(agent_act, dtype=int)
    h = np.asarray(human_correct, dtype=int)
    if not (a.shape == act.shape == h.shape):
        raise ValueError("agent_correct, agent_act, and human_correct must share shape")
    if not (np.isin(a, [0, 1]).all() and np.isin(act, [0, 1]).all() and np.isin(h, [0, 1]).all()):
        raise ValueError("routing arrays must be binary")
    return np.where(act == 1, a, h)


def human_leverage(agent_correct: np.ndarray, agent_act: np.ndarray, human_correct: np.ndarray) -> float:
    """Joint performance minus AI-only performance on the same task rows."""
    a = np.asarray(agent_correct, dtype=int)
    return float(routed_outcome(a, agent_act, human_correct).mean() - a.mean())


def recovery_value(
    agent_correct: np.ndarray,
    agent_act: np.ndarray,
    human_one_shot: np.ndarray,
    human_retry: np.ndarray,
) -> float:
    """Added joint value from a retry-enabled human receiver."""
    one = routed_outcome(agent_correct, agent_act, human_one_shot).mean()
    retry = routed_outcome(agent_correct, agent_act, human_retry).mean()
    return float(retry - one)


def autonomy_profile(agent_correct: np.ndarray, agent_act: np.ndarray) -> dict[str, float]:
    """Decompose autonomous coverage into safe and unsafe autonomous mass.

    ``safe_autonomy_mass`` is P(ACT and correct); ``unsafe_autonomy_mass`` is
    P(ACT and wrong). Their sum is ACT coverage. Conditional ACT precision is
    reported separately. This decomposition is valid even when an agent can be
    correct on rows it would choose to defer, unlike ``coverage - accuracy``.
    """
    a = np.asarray(agent_correct, dtype=int)
    act = np.asarray(agent_act, dtype=int)
    if a.shape != act.shape:
        raise ValueError("agent_correct and agent_act must share shape")
    if not (np.isin(a, [0, 1]).all() and np.isin(act, [0, 1]).all()):
        raise ValueError("agent correctness and act decisions must be binary")
    coverage = float(act.mean())
    safe = float(((act == 1) & (a == 1)).mean())
    unsafe = float(((act == 1) & (a == 0)).mean())
    precision = safe / coverage if coverage > 0 else float("nan")
    return {
        "act_coverage": coverage,
        "act_precision": precision,
        "safe_autonomy_mass": safe,
        "unsafe_autonomy_mass": unsafe,
    }


def unsafe_autonomy_mass(agent_correct: np.ndarray, agent_act: np.ndarray) -> float:
    """Return P(ACT and wrong), the task-mass exposed to wrong autonomous action."""
    return autonomy_profile(agent_correct, agent_act)["unsafe_autonomy_mass"]


def validate_nested_gate(evidence: Iterable[float], low: float, high: float) -> bool:
    """Return True when the stricter evidence gate is a subset of the looser gate."""
    x = np.asarray(list(evidence), dtype=float)
    return bool(np.all((x >= high) <= (x >= low)))
