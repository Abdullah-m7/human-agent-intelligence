"""Candidate parsing, verification, ranking, and budget-state construction."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional, Sequence

from .sandbox import SandboxPolicy, execute_program, validate_source


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_index: int
    seed: int
    valid: bool
    certified: bool
    visible_train_exact_fit: float
    source: Optional[str]
    source_sha256: Optional[str]
    source_length: Optional[int]
    ast_node_count: Optional[int]
    branch_count: Optional[int]
    target_prediction: Optional[list[list[int]]]
    error: Optional[str]
    sandbox_elapsed_s: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_program_response(content: str) -> tuple[Optional[str], Optional[str]]:
    candidates: list[str] = []
    raw = content.strip()
    if raw.startswith("def solve("):
        candidates.append(raw)
    try:
        obj = json.loads(content)
        if isinstance(obj, dict) and isinstance(obj.get("program"), str):
            candidates.append(obj["program"])
    except Exception:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if match:
            try:
                obj = json.loads(match.group(0))
                if isinstance(obj, dict) and isinstance(obj.get("program"), str):
                    candidates.append(obj["program"])
            except Exception:
                pass
    fence = re.search(r"```(?:python)?\s*(.*?)```", content, flags=re.S | re.I)
    if fence:
        candidates.append(fence.group(1))
    for source in candidates:
        source = source.strip()
        if source:
            return source, None
    return None, "program_parse_error"


def evaluate_candidate(
    content: str,
    training: Sequence[dict[str, Any]],
    target_input: list[list[int]],
    candidate_index: int,
    seed: int,
    policy: SandboxPolicy = SandboxPolicy(),
) -> CandidateEvaluation:
    source, parse_error = parse_program_response(content)
    if source is None:
        return CandidateEvaluation(
            candidate_index,
            seed,
            False,
            False,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            parse_error,
            0.0,
        )
    validation = validate_source(source, policy)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if not validation.valid:
        return CandidateEvaluation(
            candidate_index,
            seed,
            False,
            False,
            0.0,
            source,
            digest,
            len(source),
            validation.ast_node_count,
            validation.branch_count,
            None,
            validation.error,
            0.0,
        )

    grids = [pair["input"] for pair in training] + [target_input]
    execution = execute_program(source, grids, policy)
    if not execution.valid or execution.outputs is None:
        return CandidateEvaluation(
            candidate_index,
            seed,
            False,
            False,
            0.0,
            source,
            digest,
            len(source),
            validation.ast_node_count,
            validation.branch_count,
            None,
            execution.error,
            execution.elapsed_s,
        )

    train_outputs = execution.outputs[:-1]
    correct = sum(output == pair["output"] for output, pair in zip(train_outputs, training))
    fit = correct / len(training) if training else 0.0
    return CandidateEvaluation(
        candidate_index,
        seed,
        True,
        fit == 1.0,
        fit,
        source,
        digest,
        len(source),
        validation.ast_node_count,
        validation.branch_count,
        execution.outputs[-1],
        None,
        execution.elapsed_s,
    )


def select_best(candidates: Sequence[CandidateEvaluation]) -> Optional[CandidateEvaluation]:
    valid = [candidate for candidate in candidates if candidate.valid]
    if not valid:
        return None
    return min(valid, key=lambda candidate: (-candidate.visible_train_exact_fit, candidate.candidate_index))


def budget_state(
    candidates: Sequence[CandidateEvaluation],
    budget: int,
    hidden_target_output: list[list[int]],
) -> dict[str, Any]:
    prefix = [candidate for candidate in candidates if candidate.candidate_index <= budget]
    selected = select_best(prefix)
    if selected is None:
        return {
            "budget": budget,
            "candidate_count": len(prefix),
            "valid_candidate_count": 0,
            "certified_candidate_count": 0,
            "selected_candidate_index": None,
            "selected_program_hash": None,
            "standalone_prediction": None,
            "standalone_correct": False,
            "best_visible_train_fit": 0.0,
            "act": False,
            "act_correct": False,
            "wrong_act": False,
            "selected_source_length": None,
            "selected_ast_node_count": None,
            "selected_branch_count": None,
        }
    standalone_correct = selected.target_prediction == hidden_target_output
    act = selected.certified
    return {
        "budget": budget,
        "candidate_count": len(prefix),
        "valid_candidate_count": sum(candidate.valid for candidate in prefix),
        "certified_candidate_count": sum(candidate.certified for candidate in prefix),
        "selected_candidate_index": selected.candidate_index,
        "selected_program_hash": selected.source_sha256,
        "standalone_prediction": selected.target_prediction,
        "standalone_correct": standalone_correct,
        "best_visible_train_fit": selected.visible_train_exact_fit,
        "act": act,
        "act_correct": bool(act and standalone_correct),
        "wrong_act": bool(act and not standalone_correct),
        "selected_source_length": selected.source_length,
        "selected_ast_node_count": selected.ast_node_count,
        "selected_branch_count": selected.branch_count,
    }


def certified_ambiguity(candidates: Sequence[CandidateEvaluation]) -> dict[str, Any]:
    certified = [candidate for candidate in candidates if candidate.valid and candidate.certified]
    serialized = {
        json.dumps(candidate.target_prediction, separators=(",", ":"), sort_keys=True)
        for candidate in certified
    }
    return {
        "certified_candidate_count": len(certified),
        "unique_certified_target_predictions": len(serialized),
        "all_certified_predictions_agree": len(serialized) <= 1,
    }
