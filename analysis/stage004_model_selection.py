#!/usr/bin/env python3
"""Executable Stage-004 development eligibility and agent-pair selection.

The selector deliberately does not consume team outcomes, Unsafe Autonomy Mass,
ACT precision, or Human Leverage. The frozen selection rule permits only
operational viability and standalone development capability to choose the pair.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Optional

EXPECTED_DEV_TASKS = 15
MIN_PARSE_RATE = 0.80
MIN_ACT_COVERAGE = 2 / 15


@dataclass(frozen=True)
class Candidate:
    model_label: str
    n_tasks: int
    standalone_accuracy: float
    production_parse_rate: float
    hdc_parse_rate: float
    act_coverage: float
    mean_production_completion_tokens: Optional[float] = None


@dataclass(frozen=True)
class Eligibility:
    model_label: str
    eligible: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Selection:
    verdict: str
    weak_model: Optional[str]
    strong_model: Optional[str]
    weak_accuracy: Optional[float]
    strong_accuracy: Optional[float]
    eligible_models: tuple[str, ...]


def _number(summary: dict[str, Any], key: str) -> float:
    value = summary.get(key)
    if value is None:
        raise ValueError(f"missing required development metric: {key}")
    return float(value)


def candidate_from_summary(summary: dict[str, Any]) -> Candidate:
    """Extract only metrics permitted by the frozen pair-selection rule."""
    if not summary.get("model_label"):
        raise ValueError("missing required development field: model_label")
    token_value = summary.get("mean_production_completion_tokens")
    return Candidate(
        model_label=str(summary["model_label"]),
        n_tasks=int(_number(summary, "n_tasks")),
        standalone_accuracy=_number(summary, "standalone_accuracy"),
        production_parse_rate=_number(summary, "production_parse_rate"),
        hdc_parse_rate=_number(summary, "hdc_parse_rate"),
        act_coverage=_number(summary, "act_coverage"),
        mean_production_completion_tokens=(float(token_value) if token_value is not None else None),
    )


def assess(candidate: Candidate) -> Eligibility:
    reasons: list[str] = []
    if candidate.n_tasks != EXPECTED_DEV_TASKS:
        reasons.append(f"incomplete_dev:{candidate.n_tasks}/{EXPECTED_DEV_TASKS}")
    if candidate.production_parse_rate < MIN_PARSE_RATE:
        reasons.append(f"production_parse_below_{MIN_PARSE_RATE:.2f}")
    if candidate.hdc_parse_rate < MIN_PARSE_RATE:
        reasons.append(f"hdc_parse_below_{MIN_PARSE_RATE:.2f}")
    if candidate.standalone_accuracy <= 0:
        reasons.append("zero_standalone_accuracy")
    if candidate.act_coverage < MIN_ACT_COVERAGE:
        reasons.append(f"act_coverage_below_{MIN_ACT_COVERAGE:.6f}")
    return Eligibility(candidate.model_label, not reasons, tuple(reasons))


def _token_tiebreak(candidate: Candidate) -> float:
    return candidate.mean_production_completion_tokens if candidate.mean_production_completion_tokens is not None else float("inf")


def select_pair(candidates: Iterable[Candidate]) -> Selection:
    items = list(candidates)
    labels = [c.model_label for c in items]
    if len(labels) != len(set(labels)):
        raise ValueError("duplicate model_label in development candidates")

    eligible = [c for c in items if assess(c).eligible]
    eligible.sort(key=lambda c: (-c.standalone_accuracy, _token_tiebreak(c), c.model_label))
    eligible_names = tuple(c.model_label for c in eligible)

    if len(eligible) < 2:
        return Selection("NO_ELIGIBLE_LLM_PAIR", None, None, None, None, eligible_names)

    # Frozen rule: choose the highest-ranked adjacent pair with a strict
    # standalone-accuracy ordering. A tie itself cannot create WEAK/STRONG.
    chosen: Optional[tuple[Candidate, Candidate]] = None
    for high, low in zip(eligible, eligible[1:]):
        if high.standalone_accuracy > low.standalone_accuracy:
            chosen = (high, low)
            break
    if chosen is None:
        return Selection("NO_STRICT_CAPABILITY_ORDER", None, None, None, None, eligible_names)

    strong, weak = chosen
    return Selection(
        verdict="PAIR_SELECTED",
        weak_model=weak.model_label,
        strong_model=strong.model_label,
        weak_accuracy=weak.standalone_accuracy,
        strong_accuracy=strong.standalone_accuracy,
        eligible_models=eligible_names,
    )


def load_summary(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"summary is not an object: {path}")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("summaries", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    candidates: list[Candidate] = []
    eligibility: list[Eligibility] = []
    for path in args.summaries:
        candidate = candidate_from_summary(load_summary(path))
        candidates.append(candidate)
        eligibility.append(assess(candidate))

    selection = select_pair(candidates)
    report = {
        "rule_version": "STAGE004_MODEL_SELECTION_RULE_V1",
        "candidates": [asdict(c) for c in candidates],
        "eligibility": [asdict(e) for e in eligibility],
        "selection": asdict(selection),
        "forbidden_selection_inputs": [
            "unsafe_autonomy_mass",
            "act_precision",
            "joint_performance",
            "human_leverage",
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
