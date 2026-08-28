#!/usr/bin/env python3
"""Post-discovery paired bootstrap for a transition between two agent states.

This analysis was added after inspecting the first Stage-003 receiver discovery,
so it is explicitly diagnostic rather than preregistered. It resamples the same
common tasks for WEAK and STRONG and keeps all five receiver strata paired.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from analysis.paper04_receiver_contract import PRIMARY_STRATA, load_agent_rows
from analysis.paper04_task_bootstrap import validate_matched_rates
from src.receiver_contract import receiver_contract_profile


def _summary(values: Iterable[float]) -> dict[str, Any]:
    x = np.asarray(list(values), dtype=float)
    return {
        "n": int(len(x)),
        "mean": float(x.mean()),
        "p025": float(np.quantile(x, 0.025)),
        "p50": float(np.quantile(x, 0.50)),
        "p975": float(np.quantile(x, 0.975)),
        "fraction_gt_0": float(np.mean(x > 0)),
        "fraction_lt_0": float(np.mean(x < 0)),
    }


def _task_stratum_index(rates: pd.DataFrame, agent: pd.DataFrame, tasks: list[str]) -> dict[int, pd.DataFrame]:
    joined = validate_matched_rates(rates, agent, tasks)
    return {
        int(q): g.set_index("trial").sort_index()
        for q, g in joined.groupby("capability_stratum")
    }


def _profile(index: dict[int, pd.DataFrame], q: int, sampled_tasks: list[str]) -> dict[str, Any]:
    x = index[q].loc[sampled_tasks]
    return receiver_contract_profile(
        x.agent_correct.to_numpy(int),
        x.act.to_numpy(int),
        x.human_first.to_numpy(float),
        x.human_final.to_numpy(float),
    )


def paired_state_transition_bootstrap(
    rates: pd.DataFrame,
    weak: pd.DataFrame,
    strong: pd.DataFrame,
    task_ids: list[str],
    n_boot: int = 5000,
    seed: int = 240829,
) -> dict[str, Any]:
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    if set(weak.trial) != set(strong.trial):
        raise ValueError("weak and strong states must contain the same task set")
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("task_ids must be unique before resampling")

    widx = _task_stratum_index(rates, weak, task_ids)
    sidx = _task_stratum_index(rates, strong, task_ids)
    tasks = np.asarray(task_ids, dtype=object)
    rng = np.random.default_rng(seed)

    by_q: dict[int, dict[str, list[float]]] = {
        q: {
            "delta_one_shot_joint": [],
            "delta_retry_joint": [],
            "delta_one_shot_harmful_displacement": [],
            "delta_retry_harmful_displacement": [],
            "delta_recovery_suppression": [],
            "delta_recovery_capture_ratio": [],
        }
        for q in PRIMARY_STRATA
    }
    slope_delta_one: list[float] = []
    slope_delta_retry: list[float] = []

    for _ in range(n_boot):
        sampled = rng.choice(tasks, size=len(tasks), replace=True).tolist()
        delta_one_curve: list[float] = []
        delta_retry_curve: list[float] = []
        for q in PRIMARY_STRATA:
            w = _profile(widx, q, sampled)
            s = _profile(sidx, q, sampled)
            d_one = float(s["one_shot"]["joint_performance"] - w["one_shot"]["joint_performance"])
            d_retry = float(s["retry_enabled"]["joint_performance"] - w["retry_enabled"]["joint_performance"])
            delta_one_curve.append(d_one)
            delta_retry_curve.append(d_retry)
            by_q[q]["delta_one_shot_joint"].append(d_one)
            by_q[q]["delta_retry_joint"].append(d_retry)
            by_q[q]["delta_one_shot_harmful_displacement"].append(
                float(s["one_shot"]["harmful_displacement_mass"] - w["one_shot"]["harmful_displacement_mass"])
            )
            by_q[q]["delta_retry_harmful_displacement"].append(
                float(s["retry_enabled"]["harmful_displacement_mass"] - w["retry_enabled"]["harmful_displacement_mass"])
            )
            by_q[q]["delta_recovery_suppression"].append(
                float(s["recovery_suppression_mass"] - w["recovery_suppression_mass"])
            )
            wc = w["recovery_capture_ratio"]
            sc = s["recovery_capture_ratio"]
            if wc is not None and sc is not None:
                by_q[q]["delta_recovery_capture_ratio"].append(float(sc - wc))

        x = np.asarray(PRIMARY_STRATA, dtype=float)
        slope_delta_one.append(float(np.polyfit(x, np.asarray(delta_one_curve), 1)[0]))
        slope_delta_retry.append(float(np.polyfit(x, np.asarray(delta_retry_curve), 1)[0]))

    return {
        "status": "POST_DISCOVERY_DIAGNOSTIC",
        "n_common_tasks": int(len(tasks)),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "bootstrap_unit": "common_supported_task",
        "pairing": "same_task_multiset_for_weak_strong_and_all_five_receiver_strata",
        "by_capability_stratum": {
            str(q): {metric: _summary(values) for metric, values in by_q[q].items() if values}
            for q in PRIMARY_STRATA
        },
        "capability_gradient_of_transition": {
            "delta_one_shot_joint_slope": _summary(slope_delta_one),
            "delta_retry_joint_slope": _summary(slope_delta_retry),
        },
        "interpretation_guard": (
            "This paired transition bootstrap was specified after the first receiver-discovery output was inspected. "
            "It quantifies task-distribution uncertainty around the observed 240-to-321 transition but is not a preregistered confirmatory endpoint."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates", type=Path, required=True)
    ap.add_argument("--weak-rows", type=Path, required=True)
    ap.add_argument("--strong-rows", type=Path, required=True)
    ap.add_argument("--analysis-report", type=Path, required=True)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=240829)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    report_meta = json.loads(args.analysis_report.read_text(encoding="utf-8"))
    if report_meta.get("primary_gate") != "PRIMARY_ANALYSIS_READY":
        raise SystemExit(f"REFUSING TRANSITION BOOTSTRAP: primary gate is {report_meta.get('primary_gate')!r}")
    tasks = list(report_meta.get("common_support_tasks", []))
    rates = pd.read_csv(args.rates)
    weak = load_agent_rows(args.weak_rows)
    strong = load_agent_rows(args.strong_rows)
    report = paired_state_transition_bootstrap(
        rates,
        weak,
        strong,
        tasks,
        n_boot=args.n_boot,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
