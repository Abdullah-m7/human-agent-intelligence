#!/usr/bin/env python3
"""Cross-fitted receiver-contract analysis for Paper 04.

Human receiver capability on task t is estimated only from that participant's
other CogARC tasks. The held-out t outcome is then used to estimate capability-
stratum receiver performance. Agent rows are fixed inputs; this script never
queries an agent.
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
from src.receiver_contract import receiver_contract_profile


def load_agent_rows(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        d = pd.DataFrame(rows)
    else:
        d = pd.read_csv(path)
    rename = {}
    if "task_id" in d.columns and "trial" not in d.columns:
        rename["task_id"] = "trial"
    if "production_correct" in d.columns and "agent_correct" not in d.columns:
        rename["production_correct"] = "agent_correct"
    d = d.rename(columns=rename)
    required = {"trial", "agent_correct", "act"}
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f"agent rows missing columns: {sorted(missing)}")
    d = d[["trial", "agent_correct", "act"]].copy()
    if d.trial.duplicated().any():
        raise ValueError("agent rows must contain one row per task")
    for col in ("agent_correct", "act"):
        d[col] = pd.to_numeric(d[col], errors="raise").astype(int)
        if not set(d[col].unique()) <= {0, 1}:
            raise ValueError(f"{col} must be binary")
    return d.sort_values("trial").reset_index(drop=True)


def leave_one_task_capability(
    humans: pd.DataFrame,
    target_task: str,
    min_history: int = 30,
) -> pd.DataFrame:
    """First-pass receiver capability estimated without the target task."""
    hist = humans[humans.trial != target_task]
    scores = (
        hist.groupby("person_id", as_index=False)
        .agg(capability=("human_first", "mean"), n_history=("human_first", "size"))
    )
    scores = scores[scores.n_history >= min_history].copy()
    if scores.empty:
        return scores.assign(capability_stratum=pd.Series(dtype=int))

    # Average ranks keep identical capability scores together rather than using
    # person identifiers as an outcome-irrelevant but arbitrary tie breaker.
    pct = scores.capability.rank(method="average", pct=True)
    scores["capability_stratum"] = np.ceil(pct * 5).clip(1, 5).astype(int)
    return scores


def build_crossfitted_receiver_panel(
    humans: pd.DataFrame,
    task_ids: list[str],
    min_history: int = 30,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for task in task_ids:
        scores = leave_one_task_capability(humans, task, min_history=min_history)
        held = humans[humans.trial == task][
            ["person_id", "trial", "human_first", "human_final"]
        ].merge(scores, on="person_id", how="inner", validate="many_to_one")
        if not held.empty:
            rows.append(held)
    if not rows:
        return pd.DataFrame(
            columns=[
                "person_id", "trial", "human_first", "human_final",
                "capability", "n_history", "capability_stratum",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def task_stratum_rates(panel: pd.DataFrame, min_support: int = 10) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame(
            columns=["trial", "capability_stratum", "human_first", "human_final", "n_human", "supported"]
        )
    rates = (
        panel.groupby(["trial", "capability_stratum"], as_index=False)
        .agg(
            human_first=("human_first", "mean"),
            human_final=("human_final", "mean"),
            n_human=("person_id", "size"),
            mean_capability=("capability", "mean"),
        )
    )
    rates["supported"] = rates.n_human >= min_support
    return rates


def stratum_profiles(
    rates: pd.DataFrame,
    agent: pd.DataFrame,
    min_support: int = 10,
) -> dict[str, Any]:
    joined = rates.merge(agent, on="trial", how="inner", validate="many_to_one")
    joined = joined[joined.n_human >= min_support].copy()
    profiles: dict[str, Any] = {}
    for q in range(1, 6):
        x = joined[joined.capability_stratum == q].sort_values("trial")
        if x.empty:
            profiles[str(q)] = {"n_supported_tasks": 0, "profile": None}
            continue
        profile = receiver_contract_profile(
            x.agent_correct.to_numpy(),
            x.act.to_numpy(),
            x.human_first.to_numpy(float),
            x.human_final.to_numpy(float),
        )
        profiles[str(q)] = {
            "n_supported_tasks": int(len(x)),
            "mean_receiver_capability": float(x.mean_capability.mean()),
            "min_humans_per_task": int(x.n_human.min()),
            "median_humans_per_task": float(x.n_human.median()),
            "profile": profile,
        }
    return profiles


def trend_summary(profiles: dict[str, Any], contract: str) -> dict[str, Any]:
    xs: list[float] = []
    ys: list[float] = []
    hd: list[float] = []
    rs: list[float] = []
    for q in range(1, 6):
        row = profiles[str(q)]
        if not row.get("profile"):
            continue
        p = row["profile"]
        xs.append(float(q))
        ys.append(float(p[contract]["net_routing_value"]))
        hd.append(float(p[contract]["harmful_displacement_mass"]))
        rs.append(float(p["recovery_suppression_mass"]))
    if len(xs) < 2:
        return {
            "n_strata": len(xs),
            "net_routing_slope": None,
            "harmful_displacement_slope": None,
            "recovery_suppression_slope": None,
        }
    return {
        "n_strata": len(xs),
        "net_routing_slope": float(np.polyfit(xs, ys, 1)[0]),
        "harmful_displacement_slope": float(np.polyfit(xs, hd, 1)[0]),
        "recovery_suppression_slope": float(np.polyfit(xs, rs, 1)[0]),
    }


def analyze(
    humans: pd.DataFrame,
    agent: pd.DataFrame,
    min_history: int = 30,
    min_support: int = 10,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    task_ids = agent.trial.tolist()
    panel = build_crossfitted_receiver_panel(humans, task_ids, min_history=min_history)
    rates = task_stratum_rates(panel, min_support=min_support)
    profiles = stratum_profiles(rates, agent, min_support=min_support)
    report = {
        "n_agent_tasks": int(len(agent)),
        "min_history": int(min_history),
        "min_support": int(min_support),
        "n_crossfitted_person_task_rows": int(len(panel)),
        "profiles": profiles,
        "one_shot_trends": trend_summary(profiles, "one_shot"),
        "retry_enabled_trends": trend_summary(profiles, "retry_enabled"),
        "interpretation_guard": (
            "Capability strata are leave-one-task-out and task-specific. Trend slopes are descriptive; "
            "they are not IQ effects and do not establish causal effects of human intelligence."
        ),
    }
    return report, panel, rates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-rows", type=Path, required=True)
    ap.add_argument("--cogarc-root", type=Path, default=Path("/tmp/CogARC-dataRepository"))
    ap.add_argument("--min-history", type=int, default=30)
    ap.add_argument("--min-support", type=int, default=10)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--panel-out", type=Path, default=None)
    ap.add_argument("--rates-out", type=Path, default=None)
    args = ap.parse_args()

    humans = load_humans(args.cogarc_root)
    agent = load_agent_rows(args.agent_rows)
    report, panel, rates = analyze(
        humans,
        agent,
        min_history=args.min_history,
        min_support=args.min_support,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.panel_out:
        args.panel_out.parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(args.panel_out, index=False)
    if args.rates_out:
        args.rates_out.parent.mkdir(parents=True, exist_ok=True)
        rates.to_csv(args.rates_out, index=False)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
