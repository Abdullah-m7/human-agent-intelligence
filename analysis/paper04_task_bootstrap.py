#!/usr/bin/env python3
"""Paired task bootstrap for Paper-04 receiver-contract gradients.

Capability strata are treated as already frozen by the cross-fitted receiver
analysis. Each bootstrap resamples the *common supported ARC tasks* and keeps
all five receiver strata paired on the same sampled task multiset.
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
from src.receiver_contract import receiver_contract_profile


def _summary(values: Iterable[float]) -> dict[str, Any]:
    x = np.asarray(list(values), dtype=float)
    if x.size == 0:
        return {"n": 0, "mean": None, "p025": None, "p50": None, "p975": None, "fraction_gt_0": None, "fraction_lt_0": None}
    return {
        "n": int(x.size),
        "mean": float(x.mean()),
        "p025": float(np.quantile(x, 0.025)),
        "p50": float(np.quantile(x, 0.50)),
        "p975": float(np.quantile(x, 0.975)),
        "fraction_gt_0": float(np.mean(x > 0)),
        "fraction_lt_0": float(np.mean(x < 0)),
    }


def validate_matched_rates(rates: pd.DataFrame, agent: pd.DataFrame, task_ids: list[str]) -> pd.DataFrame:
    required = {"trial", "capability_stratum", "human_first", "human_final", "n_human"}
    missing = required - set(rates.columns)
    if missing:
        raise ValueError(f"rates missing columns: {sorted(missing)}")
    tasks = list(task_ids)
    if len(tasks) != len(set(tasks)):
        raise ValueError("task_ids must be unique before bootstrap resampling")
    if not tasks:
        raise ValueError("no common tasks supplied")
    if not set(tasks) <= set(agent.trial):
        raise ValueError("some common tasks are absent from agent rows")
    r = rates[rates.trial.isin(set(tasks))].copy()
    if r[["trial", "capability_stratum"]].duplicated().any():
        raise ValueError("rates contain duplicate task/stratum rows")
    needed = set(PRIMARY_STRATA)
    for trial in tasks:
        got = set(r.loc[r.trial == trial, "capability_stratum"].astype(int))
        if got != needed:
            raise ValueError(f"task {trial} does not contain exactly all primary strata")
    joined = r.merge(agent, on="trial", how="left", validate="many_to_one")
    if joined[["agent_correct", "act"]].isna().any().any():
        raise ValueError("matched rates contain tasks without agent states")
    return joined


def _curves_for_sample(joined: pd.DataFrame, sampled_tasks: list[str]) -> dict[str, np.ndarray]:
    # Indexing with a sampled list intentionally preserves duplicate tasks in a
    # bootstrap resample.
    by_q = {
        int(q): g.set_index("trial").sort_index()
        for q, g in joined.groupby("capability_stratum")
    }
    one_net: list[float] = []
    one_harm: list[float] = []
    retry_net: list[float] = []
    retry_harm: list[float] = []
    recovery_suppression: list[float] = []
    for q in PRIMARY_STRATA:
        x = by_q[q].loc[sampled_tasks]
        p = receiver_contract_profile(
            x.agent_correct.to_numpy(int),
            x.act.to_numpy(int),
            x.human_first.to_numpy(float),
            x.human_final.to_numpy(float),
        )
        one_net.append(float(p["one_shot"]["net_routing_value"]))
        one_harm.append(float(p["one_shot"]["harmful_displacement_mass"]))
        retry_net.append(float(p["retry_enabled"]["net_routing_value"]))
        retry_harm.append(float(p["retry_enabled"]["harmful_displacement_mass"]))
        recovery_suppression.append(float(p["recovery_suppression_mass"]))
    return {
        "one_shot_net": np.asarray(one_net),
        "one_shot_harmful": np.asarray(one_harm),
        "retry_net": np.asarray(retry_net),
        "retry_harmful": np.asarray(retry_harm),
        "recovery_suppression": np.asarray(recovery_suppression),
    }


def _slope(curve: np.ndarray) -> float:
    return float(np.polyfit(np.asarray(PRIMARY_STRATA, dtype=float), curve, 1)[0])


def paired_task_bootstrap(
    rates: pd.DataFrame,
    agent: pd.DataFrame,
    task_ids: list[str],
    n_boot: int = 2000,
    seed: int = 240829,
) -> dict[str, Any]:
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    joined = validate_matched_rates(rates, agent, task_ids)
    tasks = np.asarray(task_ids, dtype=object)
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {
        "one_shot_net_routing_slope": [],
        "one_shot_harmful_displacement_slope": [],
        "retry_net_routing_slope": [],
        "retry_harmful_displacement_slope": [],
        "recovery_suppression_slope": [],
        "retry_minus_one_shot_net_slope": [],
    }
    for _ in range(n_boot):
        sample = rng.choice(tasks, size=len(tasks), replace=True).tolist()
        c = _curves_for_sample(joined, sample)
        one_net = _slope(c["one_shot_net"])
        retry_net = _slope(c["retry_net"])
        values["one_shot_net_routing_slope"].append(one_net)
        values["one_shot_harmful_displacement_slope"].append(_slope(c["one_shot_harmful"]))
        values["retry_net_routing_slope"].append(retry_net)
        values["retry_harmful_displacement_slope"].append(_slope(c["retry_harmful"]))
        values["recovery_suppression_slope"].append(_slope(c["recovery_suppression"]))
        values["retry_minus_one_shot_net_slope"].append(retry_net - one_net)
    return {
        "n_common_tasks": int(len(tasks)),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "bootstrap_unit": "common_supported_task",
        "pairing": "all_five_receiver_strata_share_each_sampled_task_multiset",
        "summaries": {key: _summary(vals) for key, vals in values.items()},
        "interpretation_guard": (
            "Intervals represent heterogeneity across the common ARC task distribution with frozen receiver strata. "
            "They do not include uncertainty from re-estimating capability strata or establish causal effects."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates", type=Path, required=True)
    ap.add_argument("--agent-rows", type=Path, required=True)
    ap.add_argument("--analysis-report", type=Path, required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=240829)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rates = pd.read_csv(args.rates)
    agent = load_agent_rows(args.agent_rows)
    analysis_report = json.loads(args.analysis_report.read_text(encoding="utf-8"))
    if analysis_report.get("primary_gate") != "PRIMARY_ANALYSIS_READY":
        raise SystemExit(
            f"REFUSING PRIMARY BOOTSTRAP: receiver analysis gate is {analysis_report.get('primary_gate')!r}"
        )
    tasks = list(analysis_report.get("common_support_tasks", []))
    report = paired_task_bootstrap(rates, agent, tasks, n_boot=args.n_boot, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
