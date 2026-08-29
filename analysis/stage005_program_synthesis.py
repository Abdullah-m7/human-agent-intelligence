#!/usr/bin/env python3
"""Stage-005 nested-compute verifier-bounded program-synthesis runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.program_agent.agent import (
    BASE_SEED,
    BUDGETS,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    OpenAICompatSynthesisClient,
    canonical_json,
    contract_hashes,
    seed_for_candidate,
)
from src.program_agent.candidate import (
    CandidateEvaluation,
    budget_state,
    certified_ambiguity,
    evaluate_candidate,
)
from src.program_agent.sandbox import SandboxPolicy


SPLIT_FILE = REPO / "benchmarks" / "capability_twin" / "stage005_split.json"
DEFAULT_DATA = Path("/tmp/ARC-AGI/data/training")
DEFAULT_OUT = REPO / "results" / "stage005_program_synthesis"
CONTRACT_PATHS = (
    "src/program_agent",
    "analysis/stage005_program_synthesis.py",
    "analysis/stage005_compute_selection.py",
    "analysis/stage005_marginal_autonomy.py",
    "benchmarks/capability_twin/stage005_split.json",
    "papers/01_agentic_bottleneck/STAGE005_PROGRAM_SYNTHESIS_PROTOCOL_V1.md",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_split(path: Path = SPLIT_FILE) -> dict[str, Any]:
    split = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "source_training_task_ids",
        "human_task_blacklist",
        "engineering_tasks",
        "calibration_tasks",
    }
    missing = required - set(split)
    if missing:
        raise ValueError(f"split missing fields: {sorted(missing)}")
    source = list(split["source_training_task_ids"])
    blacklist = list(split["human_task_blacklist"])
    engineering = list(split["engineering_tasks"])
    calibration = list(split["calibration_tasks"])
    if len(source) != len(set(source)):
        raise ValueError("source training IDs are not unique")
    if len(blacklist) != 75 or len(blacklist) != len(set(blacklist)):
        raise ValueError("human task blacklist must contain 75 unique IDs")
    if len(engineering) != 20 or len(calibration) != 60:
        raise ValueError("Stage005 split must contain 20 engineering and 60 calibration tasks")
    if set(engineering) & set(calibration):
        raise ValueError("engineering and calibration splits overlap")
    if (set(engineering) | set(calibration)) & set(blacklist):
        raise ValueError("Stage005 split overlaps the CogARC blacklist")
    eligible = [task_id for task_id in source if task_id not in set(blacklist)]
    ranked = sorted(eligible, key=lambda task_id: (hashlib.sha256(task_id.encode()).hexdigest(), task_id))
    if engineering != ranked[:20] or calibration != ranked[20:80]:
        raise ValueError("Stage005 split is not the declared SHA256-mechanical selection")
    return split


def phase_task_ids(split: dict[str, Any], phase: str) -> list[str]:
    return list(split["engineering_tasks" if phase == "engineering" else "calibration_tasks"])


def assert_data_separation(data_dir: Path, task_ids: Sequence[str], split: dict[str, Any]) -> None:
    if "cogarc" in str(data_dir.resolve()).lower():
        raise SystemExit("REFUSING: Stage005 may not read a CogARC data directory")
    overlap = sorted(set(task_ids) & set(split["human_task_blacklist"]))
    if overlap:
        raise SystemExit(f"REFUSING: Stage005 task IDs overlap CogARC blacklist: {overlap}")
    missing = [task_id for task_id in task_ids if not (data_dir / f"{task_id}.json").is_file()]
    if missing:
        raise SystemExit(f"missing ARC training tasks: {missing}")


def load_arc_task(data_dir: Path, task_id: str) -> dict[str, Any]:
    task = json.loads((data_dir / f"{task_id}.json").read_text(encoding="utf-8"))
    if not task.get("train") or not task.get("test"):
        raise ValueError(f"malformed ARC task: {task_id}")
    return task


def expected_provenance(
    phase: str,
    model: str,
    model_label: str,
    model_file_sha256: str,
    split_sha256: str,
    source_data_commit: str,
    max_candidates: int,
    contract_commit: str,
    llama_cpp_build: str,
    server_args: str,
    policy: SandboxPolicy,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "model": model,
        "model_label": model_label,
        "model_file_sha256": model_file_sha256,
        "split_sha256": split_sha256,
        "source_data_commit": source_data_commit,
        "max_candidates": max_candidates,
        "budgets": [budget for budget in BUDGETS if budget <= max_candidates],
        "base_seed": BASE_SEED,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "contract_commit": contract_commit,
        "llama_cpp_build": llama_cpp_build,
        "server_args": server_args,
        "sandbox_policy": asdict(policy),
        **contract_hashes(),
    }


def validate_resume_row(
    row: dict[str, Any], expected: dict[str, Any], allowed_tasks: Sequence[str]
) -> None:
    if row.get("task_id") not in set(allowed_tasks):
        raise ValueError(f"resume row task outside phase split: {row.get('task_id')}")
    index = row.get("candidate_index")
    if not isinstance(index, int) or not 1 <= index <= expected["max_candidates"]:
        raise ValueError(f"invalid candidate index in resume row: {index}")
    if row.get("seed") != seed_for_candidate(index):
        raise ValueError(f"seed schedule mismatch for candidate {index}")
    mismatches = {
        key: (row.get(key), value)
        for key, value in expected.items()
        if row.get(key) != value
    }
    if mismatches:
        detail = ", ".join(f"{key}: row={got!r} current={want!r}" for key, (got, want) in mismatches.items())
        raise ValueError(f"resume provenance mismatch: {detail}")


def load_resume_rows(
    path: Path, expected: dict[str, Any], allowed_tasks: Sequence[str]
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        validate_resume_row(row, expected, allowed_tasks)
        key = (row["task_id"], row["candidate_index"])
        if key in seen:
            raise ValueError(f"duplicate candidate row at line {line_no}: {key}")
        seen.add(key)
        rows.append(row)
    return rows


def _candidate_from_row(row: dict[str, Any]) -> CandidateEvaluation:
    names = {field.name for field in fields(CandidateEvaluation)}
    return CandidateEvaluation(**{key: value for key, value in row["evaluation"].items() if key in names})


def build_task_rows(
    candidate_rows: Sequence[dict[str, Any]],
    task_ids: Sequence[str],
    data_dir: Path,
    max_candidates: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {task_id: [] for task_id in task_ids}
    for row in candidate_rows:
        if row["task_id"] in grouped:
            grouped[row["task_id"]].append(row)
    task_rows: list[dict[str, Any]] = []
    budgets = [budget for budget in BUDGETS if budget <= max_candidates]
    for task_id in task_ids:
        rows = sorted(grouped[task_id], key=lambda row: row["candidate_index"])
        if len(rows) != max_candidates:
            raise ValueError(f"task {task_id} has {len(rows)}/{max_candidates} candidate rows")
        candidates = [_candidate_from_row(row) for row in rows]
        task = load_arc_task(data_dir, task_id)
        target = task["test"][0]
        states = {f"B{budget}": budget_state(candidates, budget, target["output"]) for budget in budgets}
        task_rows.append(
            {
                "task_id": task_id,
                "source_n_test_queries": len(task["test"]),
                "target_index": 0,
                "budgets": states,
                "ambiguity": certified_ambiguity(candidates),
                "total_model_latency_s": sum(float(row["model_latency_s"]) for row in rows),
                "total_prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in rows),
                "total_completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in rows),
            }
        )
    return task_rows


def summarize_task_rows(task_rows: Sequence[dict[str, Any]], budgets: Sequence[int]) -> dict[str, Any]:
    n = len(task_rows)
    budget_reports: dict[str, Any] = {}
    for budget in budgets:
        key = f"B{budget}"
        states = [row["budgets"][key] for row in task_rows]
        acts = sum(bool(state["act"]) for state in states)
        correct_acts = sum(bool(state["act_correct"]) for state in states)
        wrong_acts = sum(bool(state["wrong_act"]) for state in states)
        budget_reports[key] = {
            "budget": budget,
            "n_tasks": n,
            "standalone_accuracy": sum(bool(state["standalone_correct"]) for state in states) / n if n else None,
            "act_coverage": acts / n if n else None,
            "act_precision": correct_acts / acts if acts else None,
            "unsafe_autonomy_mass": wrong_acts / n if n else None,
            "certification_yield": acts / n if n else None,
            "mean_best_train_fit": sum(float(state["best_visible_train_fit"]) for state in states) / n if n else None,
            "valid_program_rate": sum(int(state["valid_candidate_count"]) for state in states) / (n * budget) if n else None,
            "n_acts": acts,
            "n_wrong_acts": wrong_acts,
        }
    ambiguity_multiple = [row for row in task_rows if row["ambiguity"]["certified_candidate_count"] > 1]
    ambiguity_disagree = [row for row in ambiguity_multiple if not row["ambiguity"]["all_certified_predictions_agree"]]
    return {
        "n_tasks": n,
        "budgets": budget_reports,
        "certified_program_ambiguity": {
            "tasks_with_multiple_certified_programs": len(ambiguity_multiple),
            "tasks_with_prediction_disagreement": len(ambiguity_disagree),
            "disagreement_rate": (len(ambiguity_disagree) / len(ambiguity_multiple) if ambiguity_multiple else None),
        },
        "mean_model_latency_s_per_task": (
            sum(float(row["total_model_latency_s"]) for row in task_rows) / n if n else None
        ),
        "mean_prompt_tokens_per_task": (
            sum(int(row["total_prompt_tokens"]) for row in task_rows) / n if n else None
        ),
        "mean_completion_tokens_per_task": (
            sum(int(row["total_completion_tokens"]) for row in task_rows) / n if n else None
        ),
    }


def attach_summary_provenance(
    summary: dict[str, Any],
    phase: str,
    task_ids: Sequence[str],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Keep metric reports distinct from the provenance budget ladder."""
    report = dict(summary)
    report.update({"phase": phase, "task_ids": list(task_ids)})
    for key, value in expected.items():
        if key == "budgets":
            report["budget_ladder"] = value
        else:
            report[key] = value
    return report


def _current_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def _assert_contract_tree_clean() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *CONTRACT_PATHS], cwd=REPO, text=True
    ).strip()
    if status:
        raise SystemExit(f"calibration contract files differ from HEAD:\n{status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["engineering", "calibration"], required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--model-file", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--source-data-commit", required=True)
    parser.add_argument("--llama-cpp-build", required=True)
    parser.add_argument("--server-args", required=True)
    parser.add_argument("--contract-commit", default="UNFROZEN_ENGINEERING")
    parser.add_argument("--max-candidates", type=int, choices=[1, 2, 4, 8], default=8)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--split-file", type=Path, default=SPLIT_FILE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if args.phase == "calibration":
        if args.limit is not None:
            raise SystemExit("calibration must run the complete fixed split; --limit is forbidden")
        if args.max_candidates != max(BUDGETS):
            raise SystemExit("calibration requires the frozen full B1/B2/B4/B8 ladder")
        if args.contract_commit in {"", "UNFROZEN_ENGINEERING"}:
            raise SystemExit("calibration requires the pre-calibration contract-freeze commit")
        if _current_head() != args.contract_commit:
            raise SystemExit("calibration HEAD does not equal the declared contract-freeze commit")
        _assert_contract_tree_clean()

    split = load_split(args.split_file)
    task_ids = phase_task_ids(split, args.phase)
    if args.limit is not None:
        task_ids = task_ids[: args.limit]
    assert_data_separation(args.data_dir, task_ids, split)
    if not args.model_file.is_file():
        raise SystemExit(f"missing model file: {args.model_file}")

    model_sha = sha256_file(args.model_file)
    split_sha = sha256_bytes(args.split_file.read_bytes())
    policy = SandboxPolicy()
    expected = expected_provenance(
        args.phase,
        args.model,
        args.model_label,
        model_sha,
        split_sha,
        args.source_data_commit,
        args.max_candidates,
        args.contract_commit,
        args.llama_cpp_build,
        args.server_args,
        policy,
    )

    phase_dir = args.out_dir / args.phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = phase_dir / "candidates.jsonl"
    rows_path = phase_dir / "rows.jsonl"
    summary_path = phase_dir / "summary.json"
    provenance_path = phase_dir / "provenance.json"

    try:
        candidate_rows = load_resume_rows(candidates_path, expected, task_ids)
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"REFUSING RESUME: {exc}") from exc
    done = {(row["task_id"], row["candidate_index"]) for row in candidate_rows}
    client = OpenAICompatSynthesisClient(args.base_url, args.model)

    total_calls = len(task_ids) * args.max_candidates
    completed_calls = len(done)
    for task_id in task_ids:
        task = load_arc_task(args.data_dir, task_id)
        target = task["test"][0]
        for candidate_index in range(1, args.max_candidates + 1):
            key = (task_id, candidate_index)
            if key in done:
                continue
            seed = seed_for_candidate(candidate_index)
            call = client.infer(task["train"], target["input"], seed)
            evaluation = evaluate_candidate(
                call.content,
                task["train"],
                target["input"],
                candidate_index,
                seed,
                policy,
            )
            row = {
                **expected,
                "task_id": task_id,
                "candidate_index": candidate_index,
                "seed": seed,
                "request_sha256": call.request_sha256,
                "content_sha256": call.content_sha256,
                "model_content": call.content,
                "model_latency_s": call.latency_s,
                "prompt_tokens": call.prompt_tokens,
                "completion_tokens": call.completion_tokens,
                "finish_reason": call.finish_reason,
                "evaluation": evaluation.to_dict(),
                "candidate_target_correct": bool(
                    evaluation.target_prediction is not None
                    and evaluation.target_prediction == target["output"]
                ),
            }
            with candidates_path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(row) + "\n")
            candidate_rows.append(row)
            done.add(key)
            completed_calls += 1
            print(
                f"[{completed_calls}/{total_calls}] {task_id} c={candidate_index} "
                f"valid={int(evaluation.valid)} fit={evaluation.visible_train_exact_fit:.3f} "
                f"cert={int(evaluation.certified)}",
                flush=True,
            )

    task_rows = build_task_rows(candidate_rows, task_ids, args.data_dir, args.max_candidates)
    rows_path.write_text(
        "".join(canonical_json(row) + "\n" for row in task_rows), encoding="utf-8"
    )
    budgets = [budget for budget in BUDGETS if budget <= args.max_candidates]
    summary = attach_summary_provenance(
        summarize_task_rows(task_rows, budgets), args.phase, task_ids, expected
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance_path.write_text(
        json.dumps(
            {
                **expected,
                "model_file": str(args.model_file.resolve()),
                "data_dir": str(args.data_dir.resolve()),
                "split_file": str(args.split_file.resolve()),
                "task_ids": task_ids,
                "runner_head": _current_head(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
