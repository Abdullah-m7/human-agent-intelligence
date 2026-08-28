#!/usr/bin/env python3
"""Cross-fitted receiver-contract analysis for Paper 04.

Human receiver capability on task t is estimated only from that participant's
other CogARC tasks. The primary score adjusts for the difficulty of the task
mix each person observed. The held-out t outcome is used only after capability
strata are constructed. Agent rows are fixed inputs; this script never queries
an agent.
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

from analysis.cogarc_capability_twin_poc import load_humans
from src.receiver_contract import receiver_contract_profile

PRIMARY_STRATA = (1, 2, 3, 4, 5)
MIN_RELIABILITY_SB = 0.70
MIN_RELIABILITY_SPLIT_P05 = 0.50


def validate_human_panel(humans: pd.DataFrame) -> None:
    required = {"person_id", "trial", "human_first", "human_final"}
    missing = required - set(humans.columns)
    if missing:
        raise ValueError(f"human panel missing columns: {sorted(missing)}")
    if humans[["person_id", "trial"]].duplicated().any():
        raise ValueError("human panel contains duplicate person_id/trial rows")
    for col in ("human_first", "human_final"):
        vals = pd.to_numeric(humans[col], errors="raise")
        if not set(vals.unique()) <= {0, 1}:
            raise ValueError(f"{col} must be binary")
    if (humans.human_final.astype(int) < humans.human_first.astype(int)).any():
        raise ValueError("source anomaly: final human success cannot be below first-attempt success")


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


def difficulty_adjusted_scores(history: pd.DataFrame, min_history: int) -> pd.DataFrame:
    """Estimate person capability relative to peer success on attempted items.

    For each person-item row, task difficulty is represented by the success rate
    of *other* people on that task. The person's score is the mean residual
    `y_pj - peer_mean_-p,j`. This prevents a person who happened to encounter an
    easier history set from being ranked highly merely because of task mix.
    """
    if history.empty:
        return pd.DataFrame(columns=["person_id", "capability", "raw_capability", "n_history"])
    h = history[["person_id", "trial", "human_first"]].copy()
    h["human_first"] = pd.to_numeric(h.human_first, errors="raise").astype(float)
    item_sum = h.groupby("trial")["human_first"].transform("sum")
    item_n = h.groupby("trial")["human_first"].transform("size")
    if (item_n <= 1).any():
        bad = sorted(h.loc[item_n <= 1, "trial"].unique().tolist())
        raise ValueError(f"cannot estimate peer difficulty for singleton tasks: {bad}")
    peer_mean = (item_sum - h.human_first) / (item_n - 1)
    h["difficulty_adjusted_residual"] = h.human_first - peer_mean
    scores = (
        h.groupby("person_id", as_index=False)
        .agg(
            capability=("difficulty_adjusted_residual", "mean"),
            raw_capability=("human_first", "mean"),
            n_history=("human_first", "size"),
        )
    )
    return scores[scores.n_history >= min_history].copy()


def assign_capability_strata(scores: pd.DataFrame) -> pd.DataFrame:
    scores = scores.copy()
    if scores.empty:
        return scores.assign(capability_stratum=pd.Series(dtype=int))
    # Average ranks keep identical adjusted scores together rather than using
    # identifiers or held-out outcomes as arbitrary tie breakers.
    pct = scores.capability.rank(method="average", pct=True)
    scores["capability_stratum"] = np.ceil(pct * 5).clip(1, 5).astype(int)
    return scores


def leave_one_task_capability(
    humans: pd.DataFrame,
    target_task: str,
    min_history: int = 30,
) -> pd.DataFrame:
    """Difficulty-adjusted receiver capability estimated without target_task."""
    validate_human_panel(humans)
    hist = humans[humans.trial != target_task]
    return assign_capability_strata(difficulty_adjusted_scores(hist, min_history=min_history))


def _split_score(humans: pd.DataFrame, tasks: Iterable[str], min_history: int) -> pd.Series:
    d = humans[humans.trial.isin(set(tasks))]
    s = difficulty_adjusted_scores(d, min_history=min_history)
    return s.set_index("person_id").capability


def measurement_reliability(
    humans: pd.DataFrame,
    seeds: int = 200,
    min_half_history: int = 12,
) -> dict[str, Any]:
    """Repeated task-split reliability of the difficulty-adjusted score."""
    validate_human_panel(humans)
    tasks = np.array(sorted(humans.trial.unique()))
    vals: list[float] = []
    n_people: list[int] = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        perm = tasks.copy()
        rng.shuffle(perm)
        cut = len(perm) // 2
        a = _split_score(humans, perm[:cut], min_history=min_half_history)
        b = _split_score(humans, perm[cut:], min_history=min_half_history)
        q = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        if len(q) < 3:
            continue
        r = float(q.corr().iloc[0, 1])
        if np.isfinite(r):
            vals.append(r)
            n_people.append(len(q))
    if not vals:
        return {
            "n_valid_splits": 0,
            "split_half_mean": None,
            "split_half_p05": None,
            "split_half_p50": None,
            "split_half_p95": None,
            "spearman_brown_mean": None,
            "mean_people_per_split": None,
            "gate": "MEASUREMENT_HOLD",
        }
    arr = np.asarray(vals)
    sb = 2 * arr / (1 + arr)
    sb_mean = float(np.mean(sb))
    p05 = float(np.quantile(arr, 0.05))
    gate = (
        "MEASUREMENT_PASS"
        if sb_mean >= MIN_RELIABILITY_SB and p05 >= MIN_RELIABILITY_SPLIT_P05
        else "MEASUREMENT_HOLD"
    )
    return {
        "n_valid_splits": int(len(arr)),
        "split_half_mean": float(arr.mean()),
        "split_half_p05": p05,
        "split_half_p50": float(np.quantile(arr, 0.50)),
        "split_half_p95": float(np.quantile(arr, 0.95)),
        "spearman_brown_mean": sb_mean,
        "mean_people_per_split": float(np.mean(n_people)),
        "gate": gate,
        "gate_thresholds": {
            "spearman_brown_mean_min": MIN_RELIABILITY_SB,
            "split_half_p05_min": MIN_RELIABILITY_SPLIT_P05,
        },
    }


def build_crossfitted_receiver_panel(
    humans: pd.DataFrame,
    task_ids: list[str],
    min_history: int = 30,
) -> pd.DataFrame:
    validate_human_panel(humans)
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
                "capability", "raw_capability", "n_history", "capability_stratum",
            ]
        )
    out = pd.concat(rows, ignore_index=True)
    if out[["person_id", "trial"]].duplicated().any():
        raise ValueError("cross-fitted panel contains duplicate person/task rows")
    return out


def task_stratum_rates(panel: pd.DataFrame, min_support: int = 10) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame(
            columns=[
                "trial", "capability_stratum", "human_first", "human_final",
                "n_human", "mean_capability", "mean_raw_capability", "supported",
            ]
        )
    rates = (
        panel.groupby(["trial", "capability_stratum"], as_index=False)
        .agg(
            human_first=("human_first", "mean"),
            human_final=("human_final", "mean"),
            n_human=("person_id", "size"),
            mean_capability=("capability", "mean"),
            mean_raw_capability=("raw_capability", "mean"),
        )
    )
    rates["supported"] = rates.n_human >= min_support
    if (rates.human_final + 1e-12 < rates.human_first).any():
        raise AssertionError("aggregated final success fell below first-attempt success")
    return rates


def common_support_tasks(
    rates: pd.DataFrame,
    min_support: int = 10,
    strata: tuple[int, ...] = PRIMARY_STRATA,
) -> list[str]:
    """Tasks with adequate support in every primary capability stratum."""
    if rates.empty:
        return []
    good = rates[rates.n_human >= min_support]
    out: list[str] = []
    needed = set(strata)
    for trial, g in good.groupby("trial"):
        if needed <= set(g.capability_stratum.astype(int)):
            out.append(str(trial))
    return sorted(out)


def stratum_profiles(
    rates: pd.DataFrame,
    agent: pd.DataFrame,
    min_support: int = 10,
    task_ids: list[str] | None = None,
) -> dict[str, Any]:
    joined = rates.merge(agent, on="trial", how="inner", validate="many_to_one")
    joined = joined[joined.n_human >= min_support].copy()
    if task_ids is not None:
        joined = joined[joined.trial.isin(set(task_ids))].copy()
    profiles: dict[str, Any] = {}
    expected_tasks = set(task_ids) if task_ids is not None else None
    for q in PRIMARY_STRATA:
        x = joined[joined.capability_stratum == q].sort_values("trial")
        if expected_tasks is not None and set(x.trial) != expected_tasks:
            raise ValueError(f"stratum {q} does not cover the full common task set")
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
            "mean_raw_receiver_capability": float(x.mean_raw_capability.mean()),
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
    for q in PRIMARY_STRATA:
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
    min_common_tasks: int = 30,
    reliability_seeds: int = 200,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    validate_human_panel(humans)
    task_ids = agent.trial.tolist()
    panel = build_crossfitted_receiver_panel(humans, task_ids, min_history=min_history)
    rates = task_stratum_rates(panel, min_support=min_support)
    common = common_support_tasks(rates, min_support=min_support)
    profiles = stratum_profiles(rates, agent, min_support=min_support, task_ids=common)
    reliability = measurement_reliability(humans, seeds=reliability_seeds)
    support_gate = "SUPPORT_PASS" if len(common) >= min_common_tasks else "PRIMARY_SUPPORT_HOLD"
    primary_gate = (
        "PRIMARY_ANALYSIS_READY"
        if reliability["gate"] == "MEASUREMENT_PASS" and support_gate == "SUPPORT_PASS"
        else "PRIMARY_ANALYSIS_HOLD"
    )
    report = {
        "n_agent_tasks": int(len(agent)),
        "min_history": int(min_history),
        "min_support_per_stratum_task": int(min_support),
        "min_common_tasks": int(min_common_tasks),
        "n_crossfitted_person_task_rows": int(len(panel)),
        "n_common_support_tasks": int(len(common)),
        "common_support_tasks": common,
        "n_tasks_dropped_from_primary_for_support": int(len(set(task_ids) - set(common))),
        "measurement_reliability": reliability,
        "support_gate": support_gate,
        "primary_gate": primary_gate,
        "primary_profiles_common_tasks": profiles,
        "one_shot_trends": trend_summary(profiles, "one_shot"),
        "retry_enabled_trends": trend_summary(profiles, "retry_enabled"),
        "interpretation_guard": (
            "Primary capability is task-difficulty-adjusted and leave-one-task-out. "
            "All primary strata are evaluated on the same supported task set. Trend slopes are descriptive; "
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
    ap.add_argument("--min-common-tasks", type=int, default=30)
    ap.add_argument("--reliability-seeds", type=int, default=200)
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
        min_common_tasks=args.min_common_tasks,
        reliability_seeds=args.reliability_seeds,
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
