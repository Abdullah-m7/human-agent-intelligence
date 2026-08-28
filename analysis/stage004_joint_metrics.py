#!/usr/bin/env python3
"""Human+Agent metrics for Stage 004 HDC runs.

This module never queries a model and never reads hidden ARC outputs. It combines
already-scored agent task states with CogARC's archived human outcomes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from analysis.cogarc_capability_twin_poc import load_humans


def load_agent_rows(path: Path) -> pd.DataFrame:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("agent rows are empty")
    d = pd.DataFrame(rows)
    required = {"task_id", "production_correct", "act", "wrong_act", "hdc_correct"}
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f"agent rows missing columns: {sorted(missing)}")
    if d.task_id.duplicated().any():
        raise ValueError("agent rows contain duplicate task_id values")
    return d.rename(columns={"task_id": "trial", "production_correct": "agent_correct"})


def _safe_mean(values: Sequence[float]) -> float | None:
    return float(np.mean(values)) if len(values) else None


def summarize_joint(agent: pd.DataFrame, humans: pd.DataFrame) -> dict[str, Any]:
    a = agent.copy()
    a["agent_correct"] = a.agent_correct.astype(int)
    a["act"] = a.act.astype(int)
    a["wrong_act"] = a.wrong_act.astype(int)
    a["hdc_correct"] = a.hdc_correct.astype(int)

    # Task-balanced receiver: every ARC task receives equal weight; the human
    # endpoint on a task is the empirical success rate among included humans.
    task_h = humans[humans.trial.isin(a.trial)].groupby("trial").agg(
        human_first=("human_first", "mean"),
        human_final=("human_final", "mean"),
        n_human=("person_id", "size"),
    ).reset_index()
    t = a.merge(task_h, on="trial", how="left", validate="one_to_one")
    if t[["human_first", "human_final"]].isna().any().any():
        raise ValueError("some agent tasks have no matching CogARC human outcomes")

    out: dict[str, Any] = {
        "n_tasks": int(len(a)),
        "standalone_accuracy": float(a.agent_correct.mean()),
        "act_coverage": float(a.act.mean()),
        "act_precision": float(a.loc[a.act == 1, "agent_correct"].mean()) if int(a.act.sum()) else None,
        "unsafe_autonomy_mass": float(a.wrong_act.mean()),
        "n_wrong_acts": int(a.wrong_act.sum()),
        "hdc_pass_rate": float(a.hdc_correct.mean()),
        "hdc_prod_correct_rate": float(a.loc[a.agent_correct == 1, "hdc_correct"].mean()) if int(a.agent_correct.sum()) else None,
        "hdc_prod_wrong_rate": float(a.loc[a.agent_correct == 0, "hdc_correct"].mean()) if int((a.agent_correct == 0).sum()) else None,
    }

    for human_col, label in (("human_first", "one_shot"), ("human_final", "retry3")):
        task_joint = np.where(t.act == 1, t.agent_correct, t[human_col])
        out[f"task_balanced_human_{label}"] = float(t[human_col].mean())
        out[f"task_balanced_joint_{label}"] = float(task_joint.mean())
        out[f"task_balanced_leverage_{label}"] = float(task_joint.mean() - t.agent_correct.mean())

    # Participant-trial weighting is reported separately as a robustness view.
    x = humans[humans.trial.isin(a.trial)].merge(
        a[["trial", "agent_correct", "act"]], on="trial", how="inner", validate="many_to_one"
    )
    out["n_participant_trials"] = int(len(x))
    for human_col, label in (("human_first", "one_shot"), ("human_final", "retry3")):
        joint = np.where(x.act == 1, x.agent_correct, x[human_col])
        out[f"participant_weighted_human_{label}"] = float(x[human_col].mean())
        out[f"participant_weighted_joint_{label}"] = float(joint.mean())
        out[f"participant_weighted_agent_{label}"] = float(x.agent_correct.mean())
        out[f"participant_weighted_leverage_{label}"] = float(joint.mean() - x.agent_correct.mean())

    for col in ("production_latency_s", "hdc_latency_s", "production_prompt_tokens", "hdc_prompt_tokens", "production_completion_tokens", "hdc_completion_tokens"):
        if col in a.columns:
            vals = pd.to_numeric(a[col], errors="coerce").dropna().to_numpy()
            out[f"mean_{col}"] = _safe_mean(vals)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--cogarc-root", type=Path, default=Path("/tmp/CogARC-dataRepository"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    agent = load_agent_rows(args.rows)
    humans = load_humans(args.cogarc_root)
    report = summarize_joint(agent, humans)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
