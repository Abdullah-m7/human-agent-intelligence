#!/usr/bin/env python3
"""Descriptive diagnostics for verifier-consistent Stage-005 programs.

This analysis is intentionally downstream of the frozen compute-pair selector.
It never changes candidate ranking, ACT, or the selected compute pair.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"empty JSONL file: {path}")
    return rows


def ambiguity_report(
    task_rows: Sequence[dict[str, Any]], candidate_rows: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    candidates_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidate_rows:
        candidates_by_task[candidate["task_id"]].append(candidate)

    tasks: list[dict[str, Any]] = []
    for row in task_rows:
        task_id = row["task_id"]
        certified = sorted(
            (
                candidate
                for candidate in candidates_by_task[task_id]
                if candidate["evaluation"]["certified"]
            ),
            key=lambda candidate: candidate["candidate_index"],
        )
        if not certified:
            continue
        correctness = [bool(candidate["candidate_target_correct"]) for candidate in certified]
        tasks.append(
            {
                "task_id": task_id,
                "certified_candidate_count": len(certified),
                "unique_certified_target_predictions": row["ambiguity"][
                    "unique_certified_target_predictions"
                ],
                "all_certified_predictions_agree": row["ambiguity"][
                    "all_certified_predictions_agree"
                ],
                "certified_correct_count": sum(correctness),
                "certified_wrong_count": len(correctness) - sum(correctness),
                "all_certified_predictions_correct": all(correctness),
                "all_certified_predictions_wrong": not any(correctness),
                "selected_b8_candidate_index": row["budgets"]["B8"][
                    "selected_candidate_index"
                ],
                "selected_b8_correct": row["budgets"]["B8"]["standalone_correct"],
                "candidate_details": [
                    {
                        "candidate_index": candidate["candidate_index"],
                        "target_correct": bool(candidate["candidate_target_correct"]),
                        "source_sha256": candidate["evaluation"]["source_sha256"],
                    }
                    for candidate in certified
                ],
            }
        )

    multiple = [task for task in tasks if task["certified_candidate_count"] > 1]
    disagree = [task for task in multiple if not task["all_certified_predictions_agree"]]
    unanimous_wrong = [
        task
        for task in multiple
        if task["all_certified_predictions_agree"] and task["all_certified_predictions_wrong"]
    ]
    return {
        "analysis_role": "POST_CALIBRATION_DESCRIPTIVE_NOT_USED_FOR_COMPUTE_SELECTION",
        "n_tasks_with_any_certified_program": len(tasks),
        "n_tasks_with_multiple_certified_programs": len(multiple),
        "n_tasks_with_certified_prediction_disagreement": len(disagree),
        "conditional_disagreement_rate": len(disagree) / len(multiple) if multiple else None,
        "n_tasks_with_unanimous_wrong_multiple_certified_programs": len(unanimous_wrong),
        "disagreement_tasks": disagree,
        "unanimous_wrong_tasks": unanimous_wrong,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = ambiguity_report(load_jsonl(args.rows), load_jsonl(args.candidates))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
