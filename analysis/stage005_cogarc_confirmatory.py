#!/usr/bin/env python3
"""Pre-specified Stage-005 CogARC confirmatory analysis.

The CLI is fail-closed: it validates the frozen execution lock and source Git
revision before reading agent rows or archived human outcomes.  Importing this
module performs no CogARC I/O.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import linregress

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from analysis.cogarc_capability_twin_poc import load_humans
from analysis.stage005_program_ambiguity import ambiguity_report
from src.program_agent.confirmatory import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS,
    HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS,
    HUMAN_LEVERAGE_SPLITS,
    HUMAN_LEVERAGE_TASKS_PER_HALF,
    LOCK_FILE,
    ConfirmatoryAbort,
    validate_execution_lock,
    validate_full_task_set,
    validate_source_checkout,
)


FLOAT_TOLERANCE = 1e-12
MIN_ACT_COUNT = 6


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError(f"empty JSONL file: {path}")
    return rows


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denom
    return [center - half, center + half]


def exact_discordant_binomial_p(gains: int, losses: int) -> float | None:
    """Two-sided exact McNemar/binomial p-value, reported descriptively only."""
    n = gains + losses
    if n == 0:
        return None
    k = min(gains, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def _state_frame(
    task_rows: Sequence[Mapping[str, Any]], expected_task_ids: Sequence[str] | None = None
) -> pd.DataFrame:
    if expected_task_ids is not None:
        validate_full_task_set([str(row["task_id"]) for row in task_rows], expected_task_ids)
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    for row in task_rows:
        task_id = str(row["task_id"])
        if task_id in seen:
            raise ValueError(f"duplicate task row: {task_id}")
        seen.add(task_id)
        if int(row.get("target_index", -1)) != 0:
            raise ValueError(f"non-confirmatory target index for {task_id}")
        low = row["budgets"]["B1"]
        high = row["budgets"]["B8"]
        records.append(
            {
                "trial": task_id,
                "correct_B1": int(bool(low["standalone_correct"])),
                "correct_B8": int(bool(high["standalone_correct"])),
                "act_B1": int(bool(low["act"])),
                "act_B8": int(bool(high["act"])),
                "wrong_act_B1": int(bool(low["wrong_act"])),
                "wrong_act_B8": int(bool(high["wrong_act"])),
                "selected_B1": low.get("selected_candidate_index"),
                "selected_B8": high.get("selected_candidate_index"),
            }
        )
    states = pd.DataFrame(records)
    if states.empty:
        raise ValueError("no task rows")
    regressed = states[(states.act_B1 == 1) & (states.act_B8 == 0)]
    if len(regressed):
        raise ValueError("ACT_B1 is not a subset of ACT_B8")
    retained = states[states.act_B1 == 1]
    if not (
        (retained.selected_B1 == retained.selected_B8)
        & (retained.correct_B1 == retained.correct_B8)
    ).all():
        raise ValueError("nested earliest-certified routing was not preserved from B1 to B8")
    return states


def routing_decisions(task_rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, bool, bool, Any, Any]]:
    """Routing depends only on frozen budget states, never ambiguity diagnostics."""
    states = _state_frame(task_rows)
    return [
        (str(r.trial), bool(r.act_B1), bool(r.act_B8), r.selected_B1, r.selected_B8)
        for r in states.itertuples(index=False)
    ]


def _paired_bootstrap(values: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(values)
    draws = rng.integers(0, n, size=(BOOTSTRAP_RESAMPLES, n))
    estimates = values[draws].mean(axis=1)
    return {
        "method": "paired_task_percentile_bootstrap",
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "point_estimate": float(values.mean()),
        "ci95_percentile": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
    }


def primary_verdict(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Frozen verdict tree; secondary analyses are intentionally not arguments."""
    low = metrics["B1"]
    high = metrics["B8"]
    joint_low = metrics["joint_one_shot_task_balanced_B1"]
    joint_high = metrics["joint_one_shot_task_balanced_B8"]
    capability_up = high["standalone_accuracy"] > low["standalone_accuracy"]
    autonomy_up = high["act_coverage"] > low["act_coverage"]
    unsafe_up = high["unsafe_autonomy_mass"] > low["unsafe_autonomy_mass"]
    joint_down = joint_high < joint_low

    if not capability_up:
        strict = "INCONCLUSIVE_CAPABILITY_ORDER"
    elif low["n_acts"] < MIN_ACT_COUNT or high["n_acts"] < MIN_ACT_COUNT:
        strict = "INCONCLUSIVE_LOW_AUTONOMY_COVERAGE"
    elif autonomy_up and unsafe_up and joint_down:
        strict = "STRICT_ATPI_REPLICATION"
    else:
        strict = "NO_STRICT_ATPI_REPLICATION"
    broader = "AUTONOMY_TEAM_INVERSION" if capability_up and autonomy_up and joint_down else None
    return {
        "strict_atpi_verdict": strict,
        "secondary_broader_descriptor": broader,
        "criteria": {
            "standalone_capability_increased": capability_up,
            "act_coverage_increased": autonomy_up,
            "unsafe_autonomy_mass_increased": unsafe_up,
            "joint_one_shot_task_balanced_decreased": joint_down,
        },
    }


def compute_confirmatory_metrics(
    task_rows: Sequence[Mapping[str, Any]],
    humans: pd.DataFrame,
    *,
    expected_task_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    states = _state_frame(task_rows, expected_task_ids)
    required_human = {"trial", "person_id", "human_first", "human_final"}
    missing = required_human - set(humans.columns)
    if missing:
        raise ValueError(f"human rows missing columns: {sorted(missing)}")
    relevant = humans[humans.trial.astype(str).isin(set(states.trial))].copy()
    relevant["trial"] = relevant.trial.astype(str)
    task_h = relevant.groupby("trial", as_index=False).agg(
        human_first=("human_first", "mean"),
        human_final=("human_final", "mean"),
        n_human=("person_id", "size"),
    )
    tasks = states.merge(task_h, on="trial", how="left", validate="one_to_one")
    if tasks[["human_first", "human_final"]].isna().any().any():
        raise ValueError("some confirmatory tasks lack included archived human outcomes")

    for budget in (1, 8):
        tasks[f"joint_first_B{budget}"] = np.where(
            tasks[f"act_B{budget}"] == 1,
            tasks[f"correct_B{budget}"],
            tasks.human_first,
        )
        tasks[f"joint_final_B{budget}"] = np.where(
            tasks[f"act_B{budget}"] == 1,
            tasks[f"correct_B{budget}"],
            tasks.human_final,
        )

    new = tasks[(tasks.act_B1 == 0) & (tasks.act_B8 == 1)].copy()
    new_n = int(len(new))
    new_correct = int(new.correct_B8.sum())
    marginal_advantage = (
        float((new.correct_B8 - new.human_first).mean()) if new_n else None
    )
    displacement = float((new.correct_B8 - new.human_first).sum() / len(tasks))
    delta_joint = float((tasks.joint_first_B8 - tasks.joint_first_B1).mean())
    if not math.isclose(delta_joint, displacement, abs_tol=FLOAT_TOLERANCE, rel_tol=0.0):
        raise AssertionError(
            "Autonomy displacement identity failed: "
            f"delta_joint={delta_joint}, displacement={displacement}"
        )

    report: dict[str, Any] = {
        "n_tasks": int(len(tasks)),
        "B1": {
            "standalone_correct": int(tasks.correct_B1.sum()),
            "standalone_accuracy": float(tasks.correct_B1.mean()),
            "n_acts": int(tasks.act_B1.sum()),
            "act_coverage": float(tasks.act_B1.mean()),
            "act_precision": (
                float(tasks.loc[tasks.act_B1 == 1, "correct_B1"].mean())
                if int(tasks.act_B1.sum())
                else None
            ),
            "n_wrong_acts": int(tasks.wrong_act_B1.sum()),
            "unsafe_autonomy_mass": float(tasks.wrong_act_B1.mean()),
        },
        "B8": {
            "standalone_correct": int(tasks.correct_B8.sum()),
            "standalone_accuracy": float(tasks.correct_B8.mean()),
            "n_acts": int(tasks.act_B8.sum()),
            "act_coverage": float(tasks.act_B8.mean()),
            "act_precision": (
                float(tasks.loc[tasks.act_B8 == 1, "correct_B8"].mean())
                if int(tasks.act_B8.sum())
                else None
            ),
            "n_wrong_acts": int(tasks.wrong_act_B8.sum()),
            "unsafe_autonomy_mass": float(tasks.wrong_act_B8.mean()),
        },
        "joint_one_shot_task_balanced_B1": float(tasks.joint_first_B1.mean()),
        "joint_one_shot_task_balanced_B8": float(tasks.joint_first_B8.mean()),
        "delta_joint_one_shot_task_balanced_B8_minus_B1": delta_joint,
        "task_balanced_retry3_B1": float(tasks.joint_final_B1.mean()),
        "task_balanced_retry3_B8": float(tasks.joint_final_B8.mean()),
        "differences_B8_minus_B1": {
            "standalone_accuracy": float(tasks.correct_B8.mean() - tasks.correct_B1.mean()),
            "act_coverage": float(tasks.act_B8.mean() - tasks.act_B1.mean()),
            "unsafe_autonomy_mass": float(
                tasks.wrong_act_B8.mean() - tasks.wrong_act_B1.mean()
            ),
        },
        "new_autonomy": {
            "n": new_n,
            "correct": new_correct,
            "precision": new_correct / new_n if new_n else None,
            "error_rate": (new_n - new_correct) / new_n if new_n else None,
            "precision_wilson95": wilson_interval(new_correct, new_n),
            "mean_human_one_shot": float(new.human_first.mean()) if new_n else None,
            "marginal_agent_advantage": marginal_advantage,
            "autonomy_displacement_term": displacement,
        },
        "autonomy_displacement_identity": {
            "delta_joint": delta_joint,
            "autonomy_displacement_term": displacement,
            "absolute_error": abs(delta_joint - displacement),
            "tolerance": FLOAT_TOLERANCE,
            "holds": True,
            "interpretation": "exact_routing_accounting_not_causal_proof",
        },
        "primary_joint_uncertainty": _paired_bootstrap(
            (tasks.joint_first_B8 - tasks.joint_first_B1).to_numpy(float)
        ),
    }

    gains = int(((tasks.correct_B1 == 0) & (tasks.correct_B8 == 1)).sum())
    losses = int(((tasks.correct_B1 == 1) & (tasks.correct_B8 == 0)).sum())
    report["standalone_paired_transition"] = {
        "B1_wrong_to_B8_correct": gains,
        "B1_correct_to_B8_wrong": losses,
        "discordant_exact_mcnemar_binomial_p_two_sided": exact_discordant_binomial_p(
            gains, losses
        ),
        "role": "descriptive_not_selector_or_verdict_threshold",
    }

    participant = relevant.merge(states, on="trial", how="inner", validate="many_to_one")
    for human_col, receiver in (("human_first", "one_shot"), ("human_final", "retry3")):
        for budget in (1, 8):
            joint = np.where(
                participant[f"act_B{budget}"] == 1,
                participant[f"correct_B{budget}"],
                participant[human_col],
            )
            report[f"participant_weighted_{receiver}_B{budget}"] = float(joint.mean())
    report["primary_verdict"] = primary_verdict(report)
    return report


def human_leverage_crossfit(
    humans: pd.DataFrame,
    task_rows: Sequence[Mapping[str, Any]],
    *,
    seeds: int = HUMAN_LEVERAGE_SPLITS,
) -> dict[str, Any]:
    """Stage003 Human Leverage adapted only from 75-task 37/38 to 60-task 30/30."""
    states = _state_frame(task_rows)
    tasks = np.array(sorted(states.trial.unique()))
    if len(tasks) != 2 * HUMAN_LEVERAGE_TASKS_PER_HALF:
        return {
            "status": "SECONDARY_UNAVAILABLE",
            "reason": "Human Leverage requires exactly 60 tasks for frozen 30/30 splits",
        }
    z = humans.copy()
    z["trial"] = z.trial.astype(str)
    z = z[z.trial.isin(set(tasks))]
    records: list[dict[str, Any]] = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        perm = tasks.copy()
        rng.shuffle(perm)
        capability_tasks = set(perm[:HUMAN_LEVERAGE_TASKS_PER_HALF])
        evaluation_tasks = set(perm[HUMAN_LEVERAGE_TASKS_PER_HALF:])
        train = z[z.trial.isin(capability_tasks)]
        ability = train.groupby("person_id").agg(
            n_capability=("human_final", "size"),
            ability_first=("human_first", "mean"),
            ability_final=("human_final", "mean"),
        )
        test = z[z.trial.isin(evaluation_tasks)].merge(
            ability, left_on="person_id", right_index=True, how="inner"
        )
        test = test[test.n_capability >= HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS]
        test = test.merge(states, on="trial", how="inner", validate="many_to_one")
        for human_col, receiver, ability_col in (
            ("human_first", "ONE_SHOT", "ability_first"),
            ("human_final", "RETRY3", "ability_final"),
        ):
            for budget in (1, 8):
                x = test.copy()
                x["system"] = np.where(
                    x[f"act_B{budget}"] == 1, x[f"correct_B{budget}"], x[human_col]
                )
                people = x.groupby("person_id").agg(
                    n_evaluation=("system", "size"),
                    ability=(ability_col, "first"),
                    system=("system", "mean"),
                    agent=(f"correct_B{budget}", "mean"),
                )
                people = people[
                    people.n_evaluation >= HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS
                ].copy()
                people["leverage"] = people.system - people.agent
                if len(people) < 2 or people.ability.nunique() < 2:
                    continue
                regression = linregress(people.ability, people.leverage)
                records.append(
                    {
                        "split": seed,
                        "receiver": receiver,
                        "budget": f"B{budget}",
                        "n_people": int(len(people)),
                        "slope": float(regression.slope),
                        "r": float(regression.rvalue),
                        "mean_leverage": float(people.leverage.mean()),
                    }
                )
    per_split = pd.DataFrame(records)
    if per_split.empty:
        return {
            "status": "SECONDARY_UNAVAILABLE",
            "reason": "Stage003-compatible participant thresholds yielded no estimable splits",
        }
    summaries: list[dict[str, Any]] = []
    for (receiver, budget), group in per_split.groupby(["receiver", "budget"]):
        summaries.append(
            {
                "receiver": receiver,
                "budget": budget,
                "estimable_splits": int(group.split.nunique()),
                "slope_mean": float(group.slope.mean()),
                "slope_p05": float(group.slope.quantile(0.05)),
                "slope_p50": float(group.slope.median()),
                "slope_p95": float(group.slope.quantile(0.95)),
                "association_r_mean": float(group.r.mean()),
            }
        )
    differences: list[dict[str, Any]] = []
    for receiver in ("ONE_SHOT", "RETRY3"):
        receiver_rows = per_split[per_split.receiver == receiver]
        wide = receiver_rows.pivot(index="split", columns="budget", values="slope").dropna()
        if {"B1", "B8"}.issubset(wide.columns):
            delta = wide.B8 - wide.B1
            differences.append(
                {
                    "receiver": receiver,
                    "estimable_paired_splits": int(len(delta)),
                    "slope_difference_B8_minus_B1_mean": float(delta.mean()),
                    "slope_difference_p05": float(delta.quantile(0.05)),
                    "slope_difference_p50": float(delta.median()),
                    "slope_difference_p95": float(delta.quantile(0.95)),
                }
            )
    return {
        "status": "AVAILABLE",
        "analysis_role": "SECONDARY_DOES_NOT_AFFECT_PRIMARY_VERDICT",
        "construct": "ARC_TASK_CAPABILITY_NOT_IQ",
        "method": "Stage003 repeated task-level cross-fitting adapted to 60-task 30/30 splits",
        "splits_requested": seeds,
        "minimum_capability_trials": HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS,
        "minimum_evaluation_trials": HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS,
        "summaries": summaries,
        "slope_differences": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--cogarc-root", type=Path, required=True)
    parser.add_argument("--lock-file", type=Path, default=LOCK_FILE)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    # No CogARC task payload or human outcome path is touched before both checks.
    try:
        gate = validate_execution_lock(args.lock_file)
        validate_source_checkout(args.cogarc_root)
    except ConfirmatoryAbort as exc:
        raise SystemExit(str(exc)) from exc

    task_rows = load_jsonl(args.rows)
    candidate_rows = load_jsonl(args.candidates)
    humans = load_humans(args.cogarc_root)
    report = compute_confirmatory_metrics(
        task_rows, humans, expected_task_ids=gate.task_ids
    )
    report["program_ambiguity"] = ambiguity_report(task_rows, candidate_rows)
    report["program_ambiguity"]["analysis_role"] = (
        "CONFIRMATORY_DESCRIPTIVE_NOT_A_ROUTING_GATE"
    )
    report["program_ambiguity"]["unique_certified_target_predictions_by_task"] = {
        str(row["task_id"]): int(row["ambiguity"]["unique_certified_target_predictions"])
        for row in task_rows
        if int(row["ambiguity"]["certified_candidate_count"]) > 0
    }
    report["human_leverage_secondary"] = human_leverage_crossfit(humans, task_rows)
    report["confirmatory_lock_sha256"] = gate.lock_sha256
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
