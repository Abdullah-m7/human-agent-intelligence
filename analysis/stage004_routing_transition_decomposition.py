#!/usr/bin/env python3
"""Routing-transition decomposition for two Human+Agent states.

For task t with human success probability H_t, agent correctness C_t, and
binary autonomous action A_t:

    J = E[A*C + (1-A)*H] = E[H] + E[A*(C-H)].

Thus the joint-performance change from WEAK to STRONG can be decomposed exactly
by the four ACT/DEFER transition regions. This analysis is descriptive and does
not select the model pair or change the Stage-004 primary verdict.
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
from analysis.stage004_joint_metrics import load_agent_rows

REGIONS = {
    (0, 0): "defer_both",
    (1, 1): "act_both",
    (0, 1): "new_strong_autonomy",
    (1, 0): "strong_retrenchment",
}


def task_human_rates(humans: pd.DataFrame, human_col: str) -> pd.DataFrame:
    if human_col not in humans.columns:
        raise ValueError(f"missing human outcome column: {human_col}")
    return (
        humans.groupby("trial", as_index=False)
        .agg(human_success=(human_col, "mean"), n_human=("person_id", "size"))
    )


def prepare_rows(weak: pd.DataFrame, strong: pd.DataFrame, human_rates: pd.DataFrame) -> pd.DataFrame:
    w = weak[["trial", "agent_correct", "act"]].rename(
        columns={"agent_correct": "weak_correct", "act": "weak_act"}
    )
    s = strong[["trial", "agent_correct", "act"]].rename(
        columns={"agent_correct": "strong_correct", "act": "strong_act"}
    )
    x = w.merge(s, on="trial", how="inner", validate="one_to_one")
    x = x.merge(human_rates[["trial", "human_success"]], on="trial", how="left", validate="one_to_one")
    if x.human_success.isna().any():
        raise ValueError("some paired agent tasks lack a human success rate")
    if len(x) != len(w) or len(x) != len(s):
        raise ValueError("weak and strong states must contain the same task set")
    for col in ("weak_correct", "weak_act", "strong_correct", "strong_act"):
        vals = set(pd.to_numeric(x[col], errors="raise").astype(int).unique())
        if not vals <= {0, 1}:
            raise ValueError(f"non-binary values in {col}: {sorted(vals)}")
        x[col] = x[col].astype(int)
    x["weak_joint"] = np.where(x.weak_act == 1, x.weak_correct, x.human_success)
    x["strong_joint"] = np.where(x.strong_act == 1, x.strong_correct, x.human_success)
    x["delta_joint"] = x.strong_joint - x.weak_joint
    x["region"] = [REGIONS[(wa, sa)] for wa, sa in zip(x.weak_act, x.strong_act)]
    return x


def decompose(x: pd.DataFrame) -> dict[str, Any]:
    n = len(x)
    if n == 0:
        raise ValueError("no paired tasks")

    regions: dict[str, Any] = {}
    contribution_sum = 0.0
    for name in REGIONS.values():
        r = x[x.region == name]
        # Contribution is on the full task-distribution scale; region
        # contributions therefore add exactly to overall delta joint.
        contribution = float(r.delta_joint.sum() / n)
        contribution_sum += contribution
        regions[name] = {
            "n_tasks": int(len(r)),
            "task_mass": float(len(r) / n),
            "mean_delta_joint_within_region": (float(r.delta_joint.mean()) if len(r) else None),
            "contribution_to_total_delta_joint": contribution,
        }

    weak_joint = float(x.weak_joint.mean())
    strong_joint = float(x.strong_joint.mean())
    delta_joint = strong_joint - weak_joint
    if not np.isclose(contribution_sum, delta_joint, atol=1e-12):
        raise AssertionError("routing-transition contributions do not sum to delta joint")

    # Direct algebraic identity: J = E[H] + E[A(C-H)].
    human = x.human_success.to_numpy(float)
    weak_value = float(np.mean(x.weak_act * (x.weak_correct - human)))
    strong_value = float(np.mean(x.strong_act * (x.strong_correct - human)))
    human_baseline = float(np.mean(human))
    if not np.isclose(weak_joint, human_baseline + weak_value, atol=1e-12):
        raise AssertionError("weak joint identity failed")
    if not np.isclose(strong_joint, human_baseline + strong_value, atol=1e-12):
        raise AssertionError("strong joint identity failed")

    new_auto = regions["new_strong_autonomy"]
    return {
        "n_tasks": n,
        "human_baseline": human_baseline,
        "weak_joint": weak_joint,
        "strong_joint": strong_joint,
        "delta_joint_strong_minus_weak": delta_joint,
        "weak_routing_value_over_human": weak_value,
        "strong_routing_value_over_human": strong_value,
        "delta_routing_value": strong_value - weak_value,
        "regions": regions,
        "autonomy_displacement_term": new_auto["contribution_to_total_delta_joint"],
        "interpretation_guard": (
            "The autonomy_displacement_term is an exact descriptive contribution "
            "from tasks that switch WEAK:DEFER -> STRONG:ACT. It is not a causal "
            "effect estimate and does not alter the preregistered primary verdict."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weak-rows", type=Path, required=True)
    ap.add_argument("--strong-rows", type=Path, required=True)
    ap.add_argument("--receiver", choices=["one_shot", "retry3"], default="one_shot")
    ap.add_argument("--cogarc-root", type=Path, default=Path("/tmp/CogARC-dataRepository"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    weak = load_agent_rows(args.weak_rows)
    strong = load_agent_rows(args.strong_rows)
    humans = load_humans(args.cogarc_root)
    human_col = "human_first" if args.receiver == "one_shot" else "human_final"
    rates = task_human_rates(humans, human_col)
    report = decompose(prepare_rows(weak, strong, rates))
    report["receiver"] = args.receiver
    report["weak_rows"] = str(args.weak_rows)
    report["strong_rows"] = str(args.strong_rows)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
