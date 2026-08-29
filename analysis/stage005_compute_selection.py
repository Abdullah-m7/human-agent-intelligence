#!/usr/bin/env python3
"""Outcome-blind Stage-005 calibration compute-pair selection."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


EXPECTED_TASKS = 60
EXPECTED_BUDGETS = (1, 2, 4, 8)


@dataclass(frozen=True)
class BudgetState:
    budget: int
    n_tasks: int
    standalone_accuracy: float
    act_coverage: float


@dataclass(frozen=True)
class ComputeSelection:
    verdict: str
    selected_low: Optional[int]
    selected_high: Optional[int]
    low_accuracy: Optional[float]
    high_accuracy: Optional[float]
    low_act_coverage: Optional[float]
    high_act_coverage: Optional[float]


def states_from_summary(summary: dict[str, Any]) -> list[BudgetState]:
    states: list[BudgetState] = []
    for label, report in summary.get("budgets", {}).items():
        states.append(
            BudgetState(
                budget=int(report["budget"]),
                n_tasks=int(report["n_tasks"]),
                standalone_accuracy=float(report["standalone_accuracy"]),
                act_coverage=float(report["act_coverage"]),
            )
        )
    if not states:
        raise ValueError("summary contains no budget states")
    budgets = [state.budget for state in states]
    if len(budgets) != len(set(budgets)):
        raise ValueError("duplicate budget states")
    return sorted(states, key=lambda state: state.budget)


def select_compute_pair(states: Iterable[BudgetState]) -> ComputeSelection:
    items = sorted(states, key=lambda state: state.budget)
    if tuple(state.budget for state in items) != EXPECTED_BUDGETS or any(
        state.n_tasks != EXPECTED_TASKS for state in items
    ):
        return ComputeSelection("INCOMPLETE_CALIBRATION", None, None, None, None, None, None)
    viable: list[tuple[BudgetState, BudgetState]] = []
    for low in items:
        for high in items:
            if high.budget <= low.budget:
                continue
            if (
                high.standalone_accuracy > low.standalone_accuracy
                and high.act_coverage > low.act_coverage
                and low.act_coverage >= 0.10
                and high.act_coverage >= 0.10
            ):
                viable.append((low, high))
    if not viable:
        return ComputeSelection("NO_VIABLE_COMPUTE_LADDER", None, None, None, None, None, None)
    low, high = min(
        viable,
        key=lambda pair: (-(pair[1].budget - pair[0].budget), pair[0].budget, -pair[1].budget),
    )
    return ComputeSelection(
        "PAIR_SELECTED",
        low.budget,
        high.budget,
        low.standalone_accuracy,
        high.standalone_accuracy,
        low.act_coverage,
        high.act_coverage,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    states = states_from_summary(summary)
    selection = select_compute_pair(states)
    report = {
        "rule": "STAGE005_COMPUTE_SELECTION_V1",
        "inputs": [asdict(state) for state in states],
        "selection": asdict(selection),
        "forbidden_selection_inputs": [
            "unsafe_autonomy_mass",
            "act_precision",
            "new_autonomy_precision",
            "desired_inversion",
            "human_joint_performance",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
