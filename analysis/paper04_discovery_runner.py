#!/usr/bin/env python3
"""Independent Stage-003 discovery runner for Paper 04.

This script consumes *regenerated and audited* symbolic agent states. It builds
the human receiver panel once, applies the frozen measurement/common-support
gates once, then evaluates all solver states on the identical matched task set.
If the primary gate is not ready it records HOLD and deliberately skips primary
bootstrap inference rather than substituting a weaker analysis.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from analysis.cogarc_capability_twin_poc import load_humans
from analysis.paper04_receiver_contract import (
    build_crossfitted_receiver_panel,
    common_support_tasks,
    load_agent_rows,
    measurement_reliability,
    stratum_profiles,
    task_stratum_rates,
    trend_summary,
    validate_human_panel,
)
from analysis.paper04_task_bootstrap import paired_task_bootstrap

PREFIXES = (15, 40, 80, 120, 180, 240, 321)


def agent_summary(agent: pd.DataFrame) -> dict[str, Any]:
    acts = int(agent.act.sum())
    wrong = int(((agent.act == 1) & (agent.agent_correct == 0)).sum())
    correct_acts = int(((agent.act == 1) & (agent.agent_correct == 1)).sum())
    n = len(agent)
    return {
        "n_tasks": int(n),
        "standalone_accuracy": float(agent.agent_correct.mean()),
        "act_coverage": float(agent.act.mean()),
        "act_precision": float(correct_acts / acts) if acts else None,
        "unsafe_autonomy_mass": float(wrong / n),
        "n_acts": acts,
        "n_wrong_acts": wrong,
    }


def profile_curve(profiles: dict[str, Any], key: str, nested: str | None = None) -> list[float | None]:
    out: list[float | None] = []
    for q in range(1, 6):
        row = profiles[str(q)].get("profile")
        if row is None:
            out.append(None)
        elif nested is None:
            value = row.get(key)
            out.append(None if value is None else float(value))
        else:
            value = row[nested].get(key)
            out.append(None if value is None else float(value))
    return out


def contract_reversals(profiles: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for q in range(1, 6):
        p = profiles[str(q)].get("profile")
        if p is None:
            continue
        one = float(p["one_shot"]["net_routing_value"])
        retry = float(p["retry_enabled"]["net_routing_value"])
        if np.sign(one) != np.sign(retry) and not (one == 0 and retry == 0):
            rows.append({
                "capability_stratum": q,
                "one_shot_net_routing_value": one,
                "retry_net_routing_value": retry,
            })
    return rows


def build_discovery(
    cogarc_root: Path,
    agent_dir: Path,
    out_dir: Path,
    min_history: int = 30,
    min_support: int = 10,
    min_common_tasks: int = 30,
    reliability_seeds: int = 200,
    n_boot: int = 2000,
    bootstrap_seed: int = 240829,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    humans = load_humans(cogarc_root)
    validate_human_panel(humans)

    agents: dict[int, pd.DataFrame] = {}
    task_sets: dict[int, tuple[str, ...]] = {}
    for k in PREFIXES:
        path = agent_dir / f"symbolic_{k}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        agent = load_agent_rows(path)
        agents[k] = agent
        task_sets[k] = tuple(agent.trial.tolist())
    reference_tasks = task_sets[PREFIXES[0]]
    if len(reference_tasks) != 75:
        raise ValueError(f"expected 75 regenerated symbolic tasks, got {len(reference_tasks)}")
    if any(tasks != reference_tasks for tasks in task_sets.values()):
        raise ValueError("symbolic ladder states do not share an identical ordered task set")

    task_ids = list(reference_tasks)
    panel = build_crossfitted_receiver_panel(humans, task_ids, min_history=min_history)
    rates = task_stratum_rates(panel, min_support=min_support)
    common = common_support_tasks(rates, min_support=min_support)
    reliability = measurement_reliability(humans, seeds=reliability_seeds)
    support_gate = "SUPPORT_PASS" if len(common) >= min_common_tasks else "PRIMARY_SUPPORT_HOLD"
    primary_gate = (
        "PRIMARY_ANALYSIS_READY"
        if reliability["gate"] == "MEASUREMENT_PASS" and support_gate == "SUPPORT_PASS"
        else "PRIMARY_ANALYSIS_HOLD"
    )

    panel.to_csv(out_dir / "crossfitted_receiver_panel.csv", index=False)
    rates.to_csv(out_dir / "receiver_task_stratum_rates.csv", index=False)

    state_reports: dict[str, Any] = {}
    for k in PREFIXES:
        agent = agents[k]
        profiles = stratum_profiles(rates, agent, min_support=min_support, task_ids=common)
        state: dict[str, Any] = {
            "detectors": k,
            "agent": agent_summary(agent),
            "primary_gate": primary_gate,
            "n_common_support_tasks": int(len(common)),
            "profiles": profiles,
            "one_shot_trends": trend_summary(profiles, "one_shot"),
            "retry_enabled_trends": trend_summary(profiles, "retry_enabled"),
            "curves": {
                "one_shot_net_routing_value": profile_curve(profiles, "net_routing_value", "one_shot"),
                "retry_net_routing_value": profile_curve(profiles, "net_routing_value", "retry_enabled"),
                "one_shot_harmful_displacement_mass": profile_curve(profiles, "harmful_displacement_mass", "one_shot"),
                "retry_harmful_displacement_mass": profile_curve(profiles, "harmful_displacement_mass", "retry_enabled"),
                "recovery_suppression_mass": profile_curve(profiles, "recovery_suppression_mass"),
                "recovery_capture_ratio": profile_curve(profiles, "recovery_capture_ratio"),
            },
            "contract_reversals": contract_reversals(profiles),
        }
        if primary_gate == "PRIMARY_ANALYSIS_READY":
            bootstrap = paired_task_bootstrap(
                rates,
                agent,
                common,
                n_boot=n_boot,
                seed=bootstrap_seed + k,
            )
            state["paired_task_bootstrap"] = bootstrap
            (out_dir / f"symbolic_{k}_bootstrap.json").write_text(
                json.dumps(bootstrap, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        else:
            state["paired_task_bootstrap"] = {
                "verdict": "SKIPPED_PRIMARY_GATE_NOT_READY",
                "primary_gate": primary_gate,
            }
        (out_dir / f"symbolic_{k}_receiver_report.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        state_reports[str(k)] = state

    comparison_240_321 = {
        "delta_agent_accuracy": (
            state_reports["321"]["agent"]["standalone_accuracy"]
            - state_reports["240"]["agent"]["standalone_accuracy"]
        ),
        "delta_unsafe_autonomy_mass": (
            state_reports["321"]["agent"]["unsafe_autonomy_mass"]
            - state_reports["240"]["agent"]["unsafe_autonomy_mass"]
        ),
        "q1_to_q5_one_shot_net_240": state_reports["240"]["curves"]["one_shot_net_routing_value"],
        "q1_to_q5_one_shot_net_321": state_reports["321"]["curves"]["one_shot_net_routing_value"],
        "q1_to_q5_one_shot_harmful_240": state_reports["240"]["curves"]["one_shot_harmful_displacement_mass"],
        "q1_to_q5_one_shot_harmful_321": state_reports["321"]["curves"]["one_shot_harmful_displacement_mass"],
        "q1_to_q5_recovery_suppression_240": state_reports["240"]["curves"]["recovery_suppression_mass"],
        "q1_to_q5_recovery_suppression_321": state_reports["321"]["curves"]["recovery_suppression_mass"],
    }

    report = {
        "paper": "Paper 04 Receiver Contract",
        "analysis_status": "DISCOVERY_ONLY",
        "n_human_rows": int(len(humans)),
        "n_people": int(humans.person_id.nunique()),
        "n_tasks": int(humans.trial.nunique()),
        "measurement_reliability": reliability,
        "support_gate": support_gate,
        "primary_gate": primary_gate,
        "min_history": min_history,
        "min_support_per_stratum_task": min_support,
        "min_common_tasks": min_common_tasks,
        "n_common_support_tasks": int(len(common)),
        "common_support_tasks": common,
        "n_boot": n_boot if primary_gate == "PRIMARY_ANALYSIS_READY" else 0,
        "bootstrap_seed_base": bootstrap_seed,
        "states": state_reports,
        "comparison_240_to_321": comparison_240_321,
        "interpretation_guard": (
            "All receiver gradients are task-specific, difficulty-adjusted, leave-one-task-out discovery estimates. "
            "They are not IQ effects or causal estimates. Bootstrap intervals resample the matched common ARC task panel only."
        ),
    }
    (out_dir / "paper04_discovery_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cogarc-root", type=Path, required=True)
    ap.add_argument("--agent-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--min-history", type=int, default=30)
    ap.add_argument("--min-support", type=int, default=10)
    ap.add_argument("--min-common-tasks", type=int, default=30)
    ap.add_argument("--reliability-seeds", type=int, default=200)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--bootstrap-seed", type=int, default=240829)
    args = ap.parse_args()
    report = build_discovery(
        args.cogarc_root,
        args.agent_dir,
        args.out_dir,
        min_history=args.min_history,
        min_support=args.min_support,
        min_common_tasks=args.min_common_tasks,
        reliability_seeds=args.reliability_seeds,
        n_boot=args.n_boot,
        bootstrap_seed=args.bootstrap_seed,
    )
    compact = {
        "primary_gate": report["primary_gate"],
        "measurement_reliability": report["measurement_reliability"],
        "n_common_support_tasks": report["n_common_support_tasks"],
        "comparison_240_to_321": report["comparison_240_to_321"],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
