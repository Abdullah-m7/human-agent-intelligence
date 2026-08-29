"""Stage-003 proof-of-concept: dense archived humans paired with a real ARC solver.

This script never interprets ARC performance as IQ. It uses the official CogARC
Experiment-2 analysis inclusion file, estimates measurement stability from
independent task halves, runs a local third-party symbolic solver on the same 75
ARC tasks, and estimates cross-fitted Human Leverage Curves under a structural
ACT/DEFER policy.

External inputs are deliberately not vendored. Pass --cogarc-root and
--solver-root. The solver adapter expects the public tanmaybisen31/arc-agi-solver
layout (harness.py, registry.py).
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress

LEVELS = (15, 40, 80, 120, 180, 240, 321)


def load_humans(cogarc_root: Path) -> pd.DataFrame:
    b = cogarc_root / "Behavioral data"
    seq = pd.read_csv(b / "subject_task_sequence_measures_mturk.csv")
    inc = pd.read_csv(b / "trial_inclusion.csv")
    ix = inc[(inc.experiment == 2) & (inc.in_analysis == True)].copy()  # noqa: E712
    z = ix.merge(seq, on=["subject", "trial"], how="left", validate="one_to_one")
    if z.final_outcome.isna().any():
        raise ValueError("canonical inclusion rows did not match behavioral measures")
    z["human_final"] = (z.final_outcome == "success").astype(int)
    z["human_first"] = (z.success_try == 1).astype(int)
    return z


def split_half_summary(z: pd.DataFrame, seeds: int = 200) -> pd.DataFrame:
    tasks = np.array(sorted(z.trial.unique()))
    rows = []
    for outcome in ("human_final", "human_first"):
        vals = []
        for seed in range(seeds):
            rng = np.random.default_rng(seed)
            perm = tasks.copy(); rng.shuffle(perm)
            a_tasks = set(perm[: len(perm) // 2]); b_tasks = set(perm[len(perm) // 2 :])
            a = z[z.trial.isin(a_tasks)].groupby("person_id")[outcome].mean()
            b = z[z.trial.isin(b_tasks)].groupby("person_id")[outcome].mean()
            q = pd.concat([a, b], axis=1).dropna()
            r = float(q.corr().iloc[0, 1]); vals.append(r)
        a = np.asarray(vals); sb = 2 * a / (1 + a)
        rows.append({
            "outcome": outcome,
            "n_trials": len(z),
            "n_people": z.person_id.nunique(),
            "n_tasks": z.trial.nunique(),
            "split_half_mean": a.mean(),
            "split_half_p05": np.quantile(a, .05),
            "split_half_p50": np.quantile(a, .50),
            "split_half_p95": np.quantile(a, .95),
            "spearman_brown_mean": sb.mean(),
        })
    return pd.DataFrame(rows)


def load_solver(solver_root: Path):
    sys.path.insert(0, str(solver_root))
    harness = importlib.import_module("harness")
    registry = importlib.import_module("registry")
    return harness, registry


def task_dict(cogarc_root: Path, task_ids: list[str]) -> dict:
    out = {}
    for name in task_ids:
        t = json.loads((cogarc_root / "Task JSONs" / f"{name}.json").read_text())
        # CogARC behavior is scored against the first ARC test query. Two source
        # tasks retain an additional original ARC test query, but their CogARC
        # Success grids and participant submissions correspond to test[0]. Keep
        # machine and human outcomes on the same participant-visible target.
        target = t["test"][0]
        out[name] = {
            "train": [(np.array(p["input"], int), np.array(p["output"], int)) for p in t["train"]],
            "test": [(np.array(target["input"], int), np.array(target["output"], int))],
        }
    return out


def machine_ladder(cogarc_root: Path, solver_root: Path, task_ids: list[str]):
    harness, registry = load_solver(solver_root)
    dets = registry.load_all(); tasks = task_dict(cogarc_root, task_ids)
    if len(dets) < max(LEVELS):
        raise ValueError(f"solver exposes only {len(dets)} detectors")
    states, summary = {}, []
    for k in LEVELS:
        rows = []
        for name, task in tasks.items():
            preds, nfit = harness.solve_task(task, dets[:k])
            ok = True
            for (_, gt), cand in zip(task["test"], preds):
                if gt is None or not any(np.array_equal(c, gt) for c in cand):
                    ok = False; break
            rows.append((name, int(ok), int(nfit)))
        d = pd.DataFrame(rows, columns=["trial", "agent_correct", "nfit"]).set_index("trial")
        states[k] = d
        summary.append({
            "detectors": k,
            "tasks": len(d),
            "standalone_accuracy": d.agent_correct.mean(),
            "act_coverage_nfit_ge_1": (d.nfit >= 1).mean(),
            "act_precision_nfit_ge_1": d.loc[d.nfit >= 1, "agent_correct"].mean(),
            "wrong_autonomous_acts_nfit_ge_1": int(((d.nfit >= 1) & (d.agent_correct == 0)).sum()),
        })
    return states, pd.DataFrame(summary)


def crossfit_leverage(z: pd.DataFrame, states: dict[int, pd.DataFrame], seeds: int = 300) -> pd.DataFrame:
    tasks = np.array(sorted(z.trial.unique())); rows = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed); perm = tasks.copy(); rng.shuffle(perm)
        train = set(perm[:37]); test = set(perm[37:])
        tr = z[z.trial.isin(train)]
        abil = tr.groupby("person_id").agg(
            n_train=("human_final", "size"),
            ability_final=("human_final", "mean"),
            ability_first=("human_first", "mean"),
        )
        te = z[z.trial.isin(test)].merge(abil, left_on="person_id", right_index=True, how="inner")
        te = te[te.n_train >= 20].copy()
        for k, state in states.items():
            x = te.join(state, on="trial")
            x["defer"] = x.nfit == 0
            for human_col, budget, ability_col in (
                ("human_first", "one_shot", "ability_first"),
                ("human_final", "retry3", "ability_final"),
            ):
                x["system"] = np.where(x.defer, x[human_col], x.agent_correct)
                pp = x.groupby("person_id").agg(
                    n_test=("system", "size"),
                    ability=(ability_col, "first"),
                    system=("system", "mean"),
                    agent=("agent_correct", "mean"),
                    defer_rate=("defer", "mean"),
                ).reset_index()
                pp = pp[pp.n_test >= 20].copy(); pp["leverage"] = pp.system - pp.agent
                lr = linregress(pp.ability, pp.leverage)
                rows.append({
                    "seed": seed, "detectors": k, "budget": budget, "n_people": len(pp),
                    "agent_accuracy": state.agent_correct.mean(),
                    "agent_act_coverage": (state.nfit >= 1).mean(),
                    "defer_rate": pp.defer_rate.mean(), "mean_system": pp.system.mean(),
                    "mean_human_leverage": pp.leverage.mean(), "leverage_slope": lr.slope,
                    "leverage_r": lr.rvalue,
                })
    return pd.DataFrame(rows)


def confidence_summary(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in (1, 2, 3, 4, 5, 8, 10):
        act = state.nfit >= threshold
        rows.append({
            "nfit_threshold": threshold,
            "act_coverage": act.mean(),
            "n_acts": int(act.sum()),
            "act_precision": state.loc[act, "agent_correct"].mean() if act.any() else np.nan,
            "wrong_acts": int((act & (state.agent_correct == 0)).sum()),
        })
    return pd.DataFrame(rows)


def summarize_crossfit(per_seed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (k, budget), g in per_seed.groupby(["detectors", "budget"]):
        rows.append({
            "detectors": k, "budget": budget, "n_seeds": g.seed.nunique(),
            "agent_accuracy": g.agent_accuracy.mean(), "agent_act_coverage": g.agent_act_coverage.mean(),
            "defer_rate": g.defer_rate.mean(), "mean_system": g.mean_system.mean(),
            "mean_human_leverage": g.mean_human_leverage.mean(),
            "leverage_slope_mean": g.leverage_slope.mean(),
            "leverage_slope_p05": g.leverage_slope.quantile(.05),
            "leverage_slope_p50": g.leverage_slope.median(),
            "leverage_slope_p95": g.leverage_slope.quantile(.95),
        })
    return pd.DataFrame(rows).sort_values(["budget", "detectors"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cogarc-root", type=Path, required=True)
    ap.add_argument("--solver-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    z = load_humans(args.cogarc_root); task_ids = sorted(z.trial.unique())
    measurement = split_half_summary(z); states, ladder = machine_ladder(args.cogarc_root, args.solver_root, task_ids)
    per_seed = crossfit_leverage(z, states); summary = summarize_crossfit(per_seed)
    conf = confidence_summary(states[321])
    measurement.to_csv(args.out / "cogarc_measurement_summary.csv", index=False)
    ladder.to_csv(args.out / "cogarc_agent_ladder_summary.csv", index=False)
    summary.to_csv(args.out / "cogarc_human_leverage_crossfit_summary.csv", index=False)
    conf.to_csv(args.out / "cogarc_confidence_gate_discovery_summary.csv", index=False)
    print(measurement.to_string(index=False)); print(ladder.to_string(index=False)); print(summary.to_string(index=False)); print(conf.to_string(index=False))

if __name__ == "__main__":
    main()
