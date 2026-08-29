#!/usr/bin/env python3
"""Create the mechanical Stage-005 engineering/calibration split from task IDs only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
STAGE004_SPLIT = REPO / "benchmarks" / "capability_twin" / "stage004_split.json"
DEFAULT_OUT = REPO / "benchmarks" / "capability_twin" / "stage005_split.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arc-training-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    stage004 = json.loads(STAGE004_SPLIT.read_text(encoding="utf-8"))
    blacklist = list(stage004["development_tasks"]) + list(stage004["evaluation_tasks"])
    source = sorted(path.stem for path in args.arc_training_dir.glob("*.json"))
    if len(source) != 400 or len(set(source)) != 400:
        raise SystemExit(f"expected 400 unique ARC-AGI-1 training task IDs, found {len(source)}")
    if len(blacklist) != 75 or len(set(blacklist)) != 75:
        raise SystemExit("expected 75 unique CogARC blacklist IDs")
    eligible = [task_id for task_id in source if task_id not in set(blacklist)]
    ranked = sorted(eligible, key=lambda task_id: (hashlib.sha256(task_id.encode()).hexdigest(), task_id))
    report = {
        "schema_version": 1,
        "split_name": "stage005_verifier_program_synthesis_v1",
        "source": "https://github.com/fchollet/ARC-AGI data/training",
        "source_commit": args.source_commit,
        "selection_rule": (
            "Exclude all 75 CogARC IDs; sort remaining ARC-AGI-1 official training task IDs "
            "by SHA256(task_id), tie by task_id; take first 20 engineering and next 60 calibration."
        ),
        "source_training_task_ids": source,
        "human_task_blacklist": blacklist,
        "engineering_tasks": ranked[:20],
        "calibration_tasks": ranked[20:80],
        "cogarc_overlap": sorted((set(ranked[:80]) & set(blacklist))),
        "cogarc_payload_policy": "IDs_ONLY_BLACKLIST; NO_COGARC_TASK_PAYLOADS_IN_STAGE005_ENGINEERING_OR_CALIBRATION",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_tasks": len(source),
        "blacklist": len(blacklist),
        "engineering": len(report["engineering_tasks"]),
        "calibration": len(report["calibration_tasks"]),
        "overlap": report["cogarc_overlap"],
        "out": str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
