#!/usr/bin/env python3
"""Regenerate Stage-003 symbolic agent states at the participant-visible target.

This adapter intentionally scores only CogARC source `test[0]`, matching the
participant target established by the Stage-003 target-alignment audit. It
imports the pinned public ARC symbolic solver rather than copying solver code.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PREFIXES = (15, 40, 80, 120, 180, 240, 321)
EXPECTED = {
    15: {"correct": 6, "acts": 6, "wrong_acts": 0},
    40: {"correct": 9, "acts": 9, "wrong_acts": 0},
    80: {"correct": 11, "acts": 11, "wrong_acts": 0},
    120: {"correct": 13, "acts": 13, "wrong_acts": 0},
    180: {"correct": 17, "acts": 17, "wrong_acts": 0},
    240: {"correct": 20, "acts": 20, "wrong_acts": 0},
    321: {"correct": 25, "acts": 37, "wrong_acts": 12},
}


def import_solver(solver_root: Path):
    root = str(solver_root.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    harness = importlib.import_module("harness")
    registry = importlib.import_module("registry")
    return harness, registry


def score_task(task, detectors, harness) -> dict[str, int]:
    """Score the first CogARC query and structural ACT state before ground-truth use."""
    fits = harness.fitting_transforms(task["train"], detectors)
    test_input, ground_truth = task["test"][0]
    candidates = harness.candidates_for(test_input, fits)[:2]
    correct = int(any(np.array_equal(candidate, ground_truth) for candidate in candidates))
    act = int(len(fits) > 0)
    return {
        "agent_correct": correct,
        "act": act,
        "wrong_act": int(act and not correct),
        "nfit": int(len(fits)),
        "n_candidates": int(len(candidates)),
    }


def regenerate(task_dir: Path, solver_root: Path, out_dir: Path) -> dict:
    harness, registry = import_solver(solver_root)
    tasks = harness.load_tasks(str(task_dir))
    detectors = registry.load_all()
    if len(tasks) != 75:
        raise ValueError(f"expected exactly 75 CogARC tasks, got {len(tasks)}")
    if len(detectors) < max(PREFIXES):
        raise ValueError(f"solver exposes only {len(detectors)} detectors; need {max(PREFIXES)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    aggregate_rows = []
    for k in PREFIXES:
        rows = []
        for trial in sorted(tasks):
            row = {"trial": trial, **score_task(tasks[trial], detectors[:k], harness)}
            rows.append(row)
        d = pd.DataFrame(rows)
        got = {
            "correct": int(d.agent_correct.sum()),
            "acts": int(d.act.sum()),
            "wrong_acts": int(d.wrong_act.sum()),
        }
        if got != EXPECTED[k]:
            raise AssertionError(f"Stage-003 regeneration mismatch at prefix {k}: got={got}, expected={EXPECTED[k]}")
        path = out_dir / f"symbolic_{k}.csv"
        d.to_csv(path, index=False)
        aggregate_rows.append({
            "detectors": k,
            "n_tasks": int(len(d)),
            "correct": got["correct"],
            "acts": got["acts"],
            "wrong_acts": got["wrong_acts"],
            "standalone_accuracy": float(d.agent_correct.mean()),
            "act_coverage": float(d.act.mean()),
            "act_precision": float(d.loc[d.act == 1, "agent_correct"].mean()) if int(d.act.sum()) else None,
            "unsafe_autonomy_mass": float(d.wrong_act.mean()),
            "path": str(path),
        })
    aggregate = pd.DataFrame(aggregate_rows)
    aggregate.to_csv(out_dir / "symbolic_ladder_regeneration.csv", index=False)
    report = {
        "verdict": "STAGE003_TASK_STATE_REGENERATION_PASS",
        "participant_target_index": 0,
        "n_tasks": 75,
        "prefixes": list(PREFIXES),
        "aggregates": aggregate_rows,
    }
    (out_dir / "regeneration_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cogarc-root", type=Path, required=True)
    ap.add_argument("--solver-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    report = regenerate(
        args.cogarc_root / "Task JSONs",
        args.solver_root,
        args.out_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
