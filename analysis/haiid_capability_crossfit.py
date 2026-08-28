"""Cross-fitted capability analysis of the public HAIID dataset.

The analysis asks whether task capability measured on one disjoint half of a
participant's trials predicts how that participant responds to AI advice on the
other half. It deliberately does not interpret task accuracy as IQ.

Key conditioned outcomes:
- correct_uptake: initially wrong + AI correct -> final answer correct.
- wrong_resistance: initially correct + AI wrong -> final answer stays correct.
- selectivity: correct_uptake - harmful switching to wrong AI advice.

Cross-fitting avoids the direct mathematical coupling created by defining both
baseline capability and improvement on the same observations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def pearson(x: pd.Series, y: pd.Series) -> float:
    z = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(z) <= 5 or z.x.nunique() <= 1 or z.y.nunique() <= 1:
        return float("nan")
    return float(z.corr().iloc[0, 1])


def prepare(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    required = {"participant_id", "task_name", "advice_source", "advice", "response_1", "response_2"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    df = df[df.advice_source.astype(str).str.lower() == "ai"].copy()
    for col in ("advice", "response_1", "response_2"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["participant_id", "task_name", "advice", "response_1", "response_2"])
    df["initial_correct"] = (df.response_1 > 0).astype(int)
    df["final_correct"] = (df.response_2 > 0).astype(int)
    df["advice_correct"] = (df.advice > 0).astype(int)
    df["gain"] = df.final_correct - df.initial_correct
    return df


def conditional_mean(frame: pd.DataFrame, condition: pd.Series, outcome: str, minimum: int) -> float:
    sub = frame[condition]
    if len(sub) < minimum:
        return float("nan")
    return float(sub[outcome].mean())


def split_records(df: pd.DataFrame, seed: int, minimum: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records: list[dict[str, object]] = []
    for participant_id, group in df.groupby("participant_id", sort=False):
        indices = np.arange(len(group))
        rng.shuffle(indices)
        cut = len(indices) // 2
        halves = (group.iloc[indices[:cut]], group.iloc[indices[cut:]])
        for train, test in ((halves[0], halves[1]), (halves[1], halves[0])):
            correct_advice_opportunity = (test.initial_correct == 0) & (test.advice_correct == 1)
            wrong_advice_threat = (test.initial_correct == 1) & (test.advice_correct == 0)
            correct_uptake = conditional_mean(test, correct_advice_opportunity, "final_correct", minimum)
            wrong_resistance = conditional_mean(test, wrong_advice_threat, "final_correct", minimum)
            bad_switch = 1.0 - wrong_resistance if np.isfinite(wrong_resistance) else float("nan")
            selectivity = (
                correct_uptake - bad_switch
                if np.isfinite(correct_uptake) and np.isfinite(bad_switch)
                else float("nan")
            )
            records.append(
                {
                    "participant_id": participant_id,
                    "task": group.task_name.iloc[0],
                    "baseline_train": float(train.initial_correct.mean()),
                    "gain_test": float(test.gain.mean()),
                    "correct_uptake": correct_uptake,
                    "wrong_resistance": wrong_resistance,
                    "bad_switch": bad_switch,
                    "selectivity": selectivity,
                }
            )
    return pd.DataFrame(records)


def task_center(frame: pd.DataFrame, col: str) -> pd.Series:
    return frame[col] - frame.groupby("task")[col].transform("mean")


def analyze_seed(df: pd.DataFrame, seed: int, minimum: int = 2) -> dict[str, float]:
    z = split_records(df, seed, minimum)
    baseline_r = task_center(z, "baseline_train")
    metrics: dict[str, float] = {
        "seed": float(seed),
        "n_split_records": float(len(z)),
        "n_correct_uptake": float(z.correct_uptake.notna().sum()),
        "n_wrong_resistance": float(z.wrong_resistance.notna().sum()),
        "n_selectivity": float(z.selectivity.notna().sum()),
        "r_baseline_gain_raw": pearson(z.baseline_train, z.gain_test),
        "r_baseline_gain_taskFE": pearson(baseline_r, task_center(z, "gain_test")),
        "r_baseline_correct_uptake_taskFE": pearson(baseline_r, task_center(z, "correct_uptake")),
        "r_baseline_wrong_resistance_taskFE": pearson(baseline_r, task_center(z, "wrong_resistance")),
        "r_baseline_bad_switch_taskFE": pearson(baseline_r, task_center(z, "bad_switch")),
        "r_baseline_selectivity_taskFE": pearson(baseline_r, task_center(z, "selectivity")),
    }
    return metrics


def summarize(per_seed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in per_seed.columns:
        if not col.startswith("r_"):
            continue
        values = pd.to_numeric(per_seed[col], errors="coerce").dropna()
        rows.append(
            {
                "metric": col,
                "mean": values.mean(),
                "sd": values.std(ddof=1),
                "p05": values.quantile(0.05),
                "p50": values.quantile(0.50),
                "p95": values.quantile(0.95),
                "n_seeds": len(values),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/external/haiid/haiid_dataset.csv"))
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--minimum-conditioned-trials", type=int, default=2)
    parser.add_argument("--per-seed", type=Path, default=Path("results/haiid_crossfit_per_seed.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/haiid_crossfit_summary.csv"))
    parser.add_argument("--metadata", type=Path, default=Path("results/haiid_crossfit_metadata.json"))
    args = parser.parse_args()

    df = prepare(args.data)
    results = pd.DataFrame(
        [analyze_seed(df, seed, args.minimum_conditioned_trials) for seed in range(args.seeds)]
    )
    summary = summarize(results)
    args.per_seed.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.per_seed, index=False)
    summary.to_csv(args.summary, index=False)
    args.metadata.write_text(
        json.dumps(
            {
                "source_rows_ai_advice": int(len(df)),
                "participants_ai_advice": int(df.participant_id.nunique()),
                "tasks": sorted(df.task_name.unique().tolist()),
                "seeds": args.seeds,
                "minimum_conditioned_trials": args.minimum_conditioned_trials,
                "construct_warning": "baseline_train is task accuracy, not IQ",
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
