"""Pre-specified robustness analyses for Validation Lock V1.

These analyses are diagnostic only and cannot rescue a failed primary H1/H2
validation. They implement Section 11 of VALIDATION_LOCK_V1.md.
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


def fit(formula: str, data: pd.DataFrame, cluster_col: str = "user_id"):
    return smf.glm(formula, data=data, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": data[cluster_col]}
    )


def coef_row(label: str, model, term: str, data: pd.DataFrame, note: str = "") -> dict[str, object]:
    ci = model.conf_int().loc[term]
    return {
        "analysis": label,
        "term": term,
        "estimate": float(model.params[term]),
        "se": float(model.bse[term]),
        "p_value": float(model.pvalues[term]),
        "ci_low": float(ci.iloc[0]),
        "ci_high": float(ci.iloc[1]),
        "n_trials": int(len(data)),
        "n_participants": int(data.user_id.nunique()),
        "note": note,
    }


def add_numeracy(df: pd.DataFrame, preq: Path) -> pd.DataFrame:
    q = pd.read_csv(preq)
    q["user_id"] = q.user_id.astype(str)
    items = [f"answer_{i}" for i in range(1, 9)]
    vals = q[items].apply(pd.to_numeric, errors="coerce")
    vals["answer_7"] = 7 - vals["answer_7"]
    q["numeracy"] = vals.mean(axis=1)
    m, s = q.numeracy.mean(), q.numeracy.std(ddof=0)
    q["numeracy_z"] = (q.numeracy - m) / s
    return df.merge(q[["user_id", "numeracy", "numeracy_z"]], on="user_id", how="left", validate="many_to_one")


def two_primary_frames(df: pd.DataFrame):
    dis = df[df.initial_disagreement.eq(1)].copy()
    return dis[dis.ai_correct.eq(1)].copy(), dis[dis.ai_correct.eq(0)].copy(), dis


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("data/external/cscw2023/data_unpacked"))
    ap.add_argument("--out-dir", type=Path, default=Path("results/cscw2023_validation"))
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260828)
    args = ap.parse_args()

    data_dir = args.root / "main_exp" / "anonymous_data"
    selected = args.root / "loan_data_selection" / "selected_samples.csv"
    df, _ = reconstruct_trials(data_dir, selected)
    df = add_numeracy(df, data_dir / "pre_questionnaire.csv")
    if df.numeracy_z.isna().any():
        raise ValueError("missing numeracy after merge")

    # Full-10 coupled capability sensitivity: standardized once over all rows.
    full_m, full_s = df.capability_full10.mean(), df.capability_full10.std(ddof=0)
    df["capability_full10_z"] = (df.capability_full10 - full_m) / full_s
    helpful, harmful, dis = two_primary_frames(df)
    rows: list[dict[str, object]] = []

    # 1. Unstandardized LOTO capability.
    for label, frame in [("H1_helpful_unstandardized_LOTO", helpful), ("H2_harmful_unstandardized_LOTO", harmful)]:
        m = fit("switch_to_ai ~ capability_loto + C(condition) + C(item)", frame)
        rows.append(coef_row(label, m, "capability_loto", frame, "pre-specified robustness; not primary"))

    # 2. Full-10 mathematically coupled capability sensitivity.
    for label, frame in [("H1_helpful_full10_coupled", helpful), ("H2_harmful_full10_coupled", harmful)]:
        m = fit("switch_to_ai ~ capability_full10_z + C(condition) + C(item)", frame)
        rows.append(coef_row(label, m, "capability_full10_z", frame, "mathematically coupled sensitivity analysis"))

    # 3. Condition-stratified estimates, only when the binary outcome varies.
    strata_rows = []
    for condition in sorted(dis.condition.unique()):
        for target_name, target_ai in [("helpful", 1), ("harmful", 0)]:
            z = dis[(dis.condition == condition) & (dis.ai_correct == target_ai)].copy()
            if len(z) < 20 or z.switch_to_ai.nunique() < 2 or z.capability_z.nunique() < 2:
                strata_rows.append({"condition": condition, "target": target_name, "eligible": False, "n_trials": len(z)})
                continue
            m = fit("switch_to_ai ~ capability_z + C(item)", z)
            r = coef_row(f"condition_{condition}_{target_name}", m, "capability_z", z, "condition-stratified robustness")
            r.update({"condition": condition, "target": target_name, "eligible": True})
            strata_rows.append(r)

    # 4. Subjective numeracy as a separate moderator/covariate.
    for label, frame in [("H1_helpful_plus_numeracy", helpful), ("H2_harmful_plus_numeracy", harmful)]:
        m = fit("switch_to_ai ~ capability_z + numeracy_z + C(condition) + C(item)", frame)
        rows.append(coef_row(label, m, "capability_z", frame, "capability coefficient after adding subjective numeracy"))
        rows.append(coef_row(label, m, "numeracy_z", frame, "subjective numeracy coefficient; not IQ"))
    mnum = fit("switch_to_ai ~ capability_z * ai_correct + numeracy_z * ai_correct + C(condition) + C(item)", dis)
    for term in ["capability_z", "capability_z:ai_correct", "numeracy_z", "numeracy_z:ai_correct"]:
        rows.append(coef_row("M3_selectivity_plus_numeracy", mnum, term, dis, "secondary moderator model"))

    # 5. Leave-one-item-out stability of H1/H2.
    loo_rows = []
    for omitted in sorted(df.item.unique()):
        for target_name, target_ai in [("helpful", 1), ("harmful", 0)]:
            z = dis[(dis.item != omitted) & (dis.ai_correct == target_ai)].copy()
            if z.switch_to_ai.nunique() < 2:
                loo_rows.append({"omitted_item": omitted, "target": target_name, "estimate": np.nan, "fit_ok": False})
                continue
            try:
                m = fit("switch_to_ai ~ capability_z + C(condition) + C(item)", z)
                loo_rows.append({
                    "omitted_item": omitted,
                    "target": target_name,
                    "estimate": float(m.params["capability_z"]),
                    "se": float(m.bse["capability_z"]),
                    "p_value": float(m.pvalues["capability_z"]),
                    "n_trials": int(len(z)),
                    "fit_ok": True,
                })
            except Exception as exc:
                loo_rows.append({"omitted_item": omitted, "target": target_name, "estimate": np.nan, "fit_ok": False, "error": type(exc).__name__})

    # 6. Participant bootstrap of primary coefficients. Resampling the cluster is
    # the uncertainty mechanism, so coefficient fits inside each replicate use
    # ordinary binomial GLM covariance.
    rng = np.random.default_rng(args.seed)
    users = np.array(sorted(df.user_id.unique()))
    boot = {"helpful": [], "harmful": []}
    for b in range(args.bootstrap):
        sampled = rng.choice(users, size=len(users), replace=True)
        parts = []
        for j, user in enumerate(sampled):
            q = df[df.user_id == user].copy()
            q["boot_id"] = f"b{b}_copy{j}"
            parts.append(q)
        bd = pd.concat(parts, ignore_index=True)
        bd = bd[bd.initial_disagreement.eq(1)]
        for target_name, target_ai in [("helpful", 1), ("harmful", 0)]:
            z = bd[bd.ai_correct.eq(target_ai)]
            try:
                m = smf.glm(
                    "switch_to_ai ~ capability_z + C(condition) + C(item)",
                    data=z, family=sm.families.Binomial(),
                ).fit()
                boot[target_name].append(float(m.params["capability_z"]))
            except Exception:
                boot[target_name].append(np.nan)

    boot_rows = []
    for target, vals in boot.items():
        x = np.asarray(vals, dtype=float)
        x = x[np.isfinite(x)]
        boot_rows.append({
            "target": target,
            "requested_replicates": int(args.bootstrap),
            "successful_replicates": int(len(x)),
            "median": float(np.median(x)),
            "mean": float(np.mean(x)),
            "ci025": float(np.quantile(x, 0.025)),
            "ci975": float(np.quantile(x, 0.975)),
            "fraction_negative": float(np.mean(x < 0)),
        })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(rows)
    strata = pd.DataFrame(strata_rows)
    loo = pd.DataFrame(loo_rows)
    boots = pd.DataFrame(boot_rows)
    summary.to_csv(args.out_dir / "robustness_models.csv", index=False)
    strata.to_csv(args.out_dir / "condition_stratified.csv", index=False)
    loo.to_csv(args.out_dir / "leave_one_item_out.csv", index=False)
    boots.to_csv(args.out_dir / "participant_bootstrap_summary.csv", index=False)

    print("ROBUSTNESS_MODELS")
    print(summary.to_string(index=False))
    print("\nCONDITION_STRATIFIED")
    print(strata.to_string(index=False))
    print("\nLOO_STABILITY")
    print(loo.groupby("target").estimate.agg(["min", "max", "mean"]).to_string())
    print("sign_counts")
    print(loo.assign(sign=np.sign(loo.estimate)).groupby(["target", "sign"]).size().to_string())
    print("\nPARTICIPANT_BOOTSTRAP")
    print(boots.to_string(index=False))


if __name__ == "__main__":
    main()
