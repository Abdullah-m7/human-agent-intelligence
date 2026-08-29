#!/usr/bin/env python3
"""Agent-only marginal-autonomy and certified-program diagnostics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


TRANSITIONS = ((1, 2), (2, 4), (4, 8))


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("task rows are empty")
    return rows


def marginal_report(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    transitions: list[dict[str, Any]] = []
    n = len(rows)
    for low_budget, high_budget in TRANSITIONS:
        low_key, high_key = f"B{low_budget}", f"B{high_budget}"
        low = [row["budgets"][low_key] for row in rows]
        high = [row["budgets"][high_key] for row in rows]
        new_indices = [index for index, (a, b) in enumerate(zip(low, high)) if not a["act"] and b["act"]]
        new_correct = sum(bool(high[index]["standalone_correct"]) for index in new_indices)
        transitions.append(
            {
                "transition": f"B{low_budget}->B{high_budget}",
                "low_budget": low_budget,
                "high_budget": high_budget,
                "delta_capability": (
                    sum(bool(state["standalone_correct"]) for state in high)
                    - sum(bool(state["standalone_correct"]) for state in low)
                )
                / n,
                "delta_act_coverage": (
                    sum(bool(state["act"]) for state in high) - sum(bool(state["act"]) for state in low)
                )
                / n,
                "delta_uam": (
                    sum(bool(state["wrong_act"]) for state in high)
                    - sum(bool(state["wrong_act"]) for state in low)
                )
                / n,
                "new_autonomy_n": len(new_indices),
                "new_autonomy_precision": (new_correct / len(new_indices) if new_indices else None),
                "new_autonomy_error_rate": (
                    1.0 - new_correct / len(new_indices) if new_indices else None
                ),
            }
        )

    multiple = [row for row in rows if row["ambiguity"]["certified_candidate_count"] > 1]
    disagree = [row for row in multiple if not row["ambiguity"]["all_certified_predictions_agree"]]

    complexity: dict[str, Any] = {}
    for budget in (1, 2, 4, 8):
        states = [row["budgets"][f"B{budget}"] for row in rows]
        certified = [state for state in states if state["act"]]
        correct = [state for state in certified if state["act_correct"]]
        wrong = [state for state in certified if state["wrong_act"]]

        def means(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
            return {
                metric: (sum(float(item[metric]) for item in items) / len(items) if items else None)
                for metric in (
                    "selected_source_length",
                    "selected_ast_node_count",
                    "selected_branch_count",
                )
            }

        complexity[f"B{budget}"] = {
            "certified_correct": means(correct),
            "certified_wrong": means(wrong),
            "n_certified_correct": len(correct),
            "n_certified_wrong": len(wrong),
        }

    return {
        "n_tasks": n,
        "transitions": transitions,
        "certified_program_ambiguity": {
            "tasks_with_multiple_certified_programs": len(multiple),
            "tasks_with_prediction_disagreement": len(disagree),
            "disagreement_rate": len(disagree) / len(multiple) if multiple else None,
        },
        "selected_certified_program_complexity": complexity,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = marginal_report(load_rows(args.rows))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
