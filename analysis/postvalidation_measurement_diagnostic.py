"""Post-validation exploratory diagnostic: HAIID vs CSCW capability measurement.

This analysis was defined only after the locked CSCW validation failed. It is
not confirmatory and cannot alter that verdict. It asks whether the two datasets
differ in the reliability / predictive validity of task-capability estimates.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.cscw2023_validation import reconstruct_trials


def corr(x, y):
    z = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(z) < 10 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return np.nan
    return float(z.corr().iloc[0, 1])


def sb(r):
    return float(2 * r / (1 + r)) if np.isfinite(r) and r > -0.999 else np.nan


def haiid_prepare(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, low_memory=False)
    d = d[d.advice_source.astype(str).str.lower().eq("ai")].copy()
    d["initial_correct"] = (pd.to_numeric(d.response_1, errors="coerce") > 0).astype(float)
    d = d.dropna(subset=["participant_id", "task_name", "task_instance_id", "initial_correct"])
    return d


def cscw_prepare(root: Path) -> pd.DataFrame:
    d, _ = reconstruct_trials(
        root / "main_exp" / "anonymous_data",
        root / "loan_data_selection" / "selected_samples.csv",
    )
    return d


def common_item_split_reliability_haiid(d: pd.DataFrame, seeds: int) -> pd.DataFrame:
    out = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        parts = []
        for task, g in d.groupby("task_name"):
            items = np.array(sorted(g.task_instance_id.unique()))
            rng.shuffle(items)
            cut = len(items) // 2
            side = {item: (0 if item in set(items[:cut]) else 1) for item in items}
            q = g.copy()
            q["half"] = q.task_instance_id.map(side)
            agg = q.groupby(["participant_id", "task_name", "half"]).initial_correct.mean().unstack("half")
            if 0 not in agg.columns or 1 not in agg.columns:
                continue
            agg = agg.dropna().reset_index()
            agg["h0c"] = agg[0] - agg.groupby("task_name")[0].transform("mean")
            agg["h1c"] = agg[1] - agg.groupby("task_name")[1].transform("mean")
            parts.append(agg)
        z = pd.concat(parts, ignore_index=True)
        r = corr(z.h0c, z.h1c)
        out.append({"seed": seed, "r_split_half": r, "spearman_brown": sb(r), "n": len(z)})
    return pd.DataFrame(out)


def common_item_split_reliability_cscw(d: pd.DataFrame, seeds: int) -> pd.DataFrame:
    out = []
    items0 = np.array(sorted(d.item.unique()))
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        items = items0.copy(); rng.shuffle(items)
        cut = len(items) // 2
        side = {item: (0 if item in set(items[:cut]) else 1) for item in items}
        q = d.copy(); q["half"] = q.item.map(side)
        agg = q.groupby(["user_id", "condition", "half"]).initial_correct.mean().unstack("half").dropna().reset_index()
        r_raw = corr(agg[0], agg[1])
        h0c = agg[0] - agg.groupby("condition")[0].transform("mean")
        h1c = agg[1] - agg.groupby("condition")[1].transform("mean")
        r_center = corr(h0c, h1c)
        out.append({
            "seed": seed,
            "r_split_half_raw": r_raw,
            "r_split_half_condition_centered": r_center,
            "spearman_brown_raw": sb(r_raw),
            "spearman_brown_condition_centered": sb(r_center),
            "n": len(agg),
        })
    return pd.DataFrame(out)


def cscw_loto_predictive_validity(d: pd.DataFrame) -> dict[str, float]:
    m = smf.glm(
        "initial_correct ~ capability_z + C(condition) + C(item)",
        data=d, family=sm.families.Binomial(),
    ).fit(cov_type="cluster", cov_kwds={"groups": d.user_id})
    ci = m.conf_int().loc["capability_z"]
    return {
        "estimate_logodds_per_1sd": float(m.params["capability_z"]),
        "se": float(m.bse["capability_z"]),
        "p_value": float(m.pvalues["capability_z"]),
        "ci_low": float(ci.iloc[0]),
        "ci_high": float(ci.iloc[1]),
        "n_trials": int(len(d)),
        "n_participants": int(d.user_id.nunique()),
    }


def describe_design(h: pd.DataFrame, c: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "dataset": "HAIID_AI_subset",
            "participants": h.participant_id.nunique(),
            "trials": len(h),
            "median_trials_per_participant": h.groupby("participant_id").size().median(),
            "min_trials_per_participant": h.groupby("participant_id").size().min(),
            "max_trials_per_participant": h.groupby("participant_id").size().max(),
            "tasks": h.task_name.nunique(),
        },
        {
            "dataset": "CSCW2023",
            "participants": c.user_id.nunique(),
            "trials": len(c),
            "median_trials_per_participant": c.groupby("user_id").size().median(),
            "min_trials_per_participant": c.groupby("user_id").size().min(),
            "max_trials_per_participant": c.groupby("user_id").size().max(),
            "tasks": 1,
        },
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--haiid", type=Path, default=Path("data/external/haiid/haiid_dataset.csv"))
    ap.add_argument("--cscw-root", type=Path, default=Path("data/external/cscw2023/data_unpacked"))
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--out", type=Path, default=Path("results/postvalidation_measurement_diagnostic_summary.csv"))
    args = ap.parse_args()
    h = haiid_prepare(args.haiid)
    c = cscw_prepare(args.cscw_root)
    hr = common_item_split_reliability_haiid(h, args.seeds)
    cr = common_item_split_reliability_cscw(c, args.seeds)
    pv = cscw_loto_predictive_validity(c)
    design = describe_design(h, c)

    summary = pd.DataFrame([
        {"metric": "HAIID_split_half_r", "mean": hr.r_split_half.mean(), "p05": hr.r_split_half.quantile(.05), "p95": hr.r_split_half.quantile(.95)},
        {"metric": "HAIID_Spearman_Brown", "mean": hr.spearman_brown.mean(), "p05": hr.spearman_brown.quantile(.05), "p95": hr.spearman_brown.quantile(.95)},
        {"metric": "CSCW_split_half_r_raw", "mean": cr.r_split_half_raw.mean(), "p05": cr.r_split_half_raw.quantile(.05), "p95": cr.r_split_half_raw.quantile(.95)},
        {"metric": "CSCW_Spearman_Brown_raw", "mean": cr.spearman_brown_raw.mean(), "p05": cr.spearman_brown_raw.quantile(.05), "p95": cr.spearman_brown_raw.quantile(.95)},
        {"metric": "CSCW_split_half_r_condition_centered", "mean": cr.r_split_half_condition_centered.mean(), "p05": cr.r_split_half_condition_centered.quantile(.05), "p95": cr.r_split_half_condition_centered.quantile(.95)},
        {"metric": "CSCW_Spearman_Brown_condition_centered", "mean": cr.spearman_brown_condition_centered.mean(), "p05": cr.spearman_brown_condition_centered.quantile(.05), "p95": cr.spearman_brown_condition_centered.quantile(.95)},
    ])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)
    design.to_csv(args.out.with_name("postvalidation_design_comparison_summary.csv"), index=False)
    pd.DataFrame([pv]).to_csv(args.out.with_name("postvalidation_cscw_loto_predictive_validity_summary.csv"), index=False)
    print("DESIGN")
    print(design.to_string(index=False))
    print("\nRELIABILITY")
    print(summary.to_string(index=False))
    print("\nCSCW_LOTO_PREDICTIVE_VALIDITY")
    print(pd.DataFrame([pv]).to_string(index=False))


if __name__ == "__main__":
    main()
