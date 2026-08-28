"""Exploratory CRT analysis of open forecasting-advice data.

Source study:
Himmelstein et al. (2023), "Preference for human or algorithmic forecasting
advice does not predict if and how it is used", Journal of Behavioral Decision
Making. The original analysis already includes CRT as a covariate. This script
therefore does NOT claim novelty for a generic CRT/advice-taking association.

Our Stage-001 exploratory question is narrower:
    Conditional on the quality of the person's initial forecast and the quality
    of the algorithmic forecast, does cognitive reflection predict the quality
    of the final combined forecast?

This is hypothesis-generating. It was written after inspecting the dataset and
must not be presented as a preregistered or confirmatory analysis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def clustered_model(formula: str, data: pd.DataFrame):
    return smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["id"]}
    )


def coefficient_row(label: str, model, term: str, note: str = "") -> dict[str, object]:
    ci = model.conf_int().loc[term]
    return {
        "metric": label,
        "estimate": float(model.params[term]),
        "se": float(model.bse[term]),
        "p_value": float(model.pvalues[term]),
        "ci_low": float(ci.iloc[0]),
        "ci_high": float(ci.iloc[1]),
        "note": note,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jas",
        type=Path,
        default=Path("data/external/himmelstein2023/Study_2_JAS_Data.csv"),
    )
    parser.add_argument(
        "--demographics",
        type=Path,
        default=Path("data/external/himmelstein2023/Study_2_demographics_and_scales.csv"),
    )
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("results/himmelstein_crt_exploratory_summary.csv"),
    )
    args = parser.parse_args()

    jas = pd.read_csv(args.jas, low_memory=False)
    demographics = pd.read_csv(args.demographics, low_memory=False)
    required_jas = {
        "id", "item_no", "domain", "advice", "brier1", "brier2", "brier_r",
        "dwoa", "outrange", "agree", "rel_peaks",
    }
    required_dem = {"id", "CRTsc"}
    missing = required_jas - set(jas.columns)
    missing_dem = required_dem - set(demographics.columns)
    if missing or missing_dem:
        raise ValueError(f"missing columns: JAS={sorted(missing)} demographics={sorted(missing_dem)}")

    data = jas.merge(demographics[["id", "CRTsc"]], on="id", how="inner")
    data["CRT_z"] = zscore(data.CRTsc)

    rows: list[dict[str, object]] = []

    # Direct cognitive measure vs unaided forecasting quality.
    participants = data.groupby("id").agg(
        CRT=("CRTsc", "first"), baseline_brier=("brier1", "mean")
    ).reset_index()
    r, p = stats.pearsonr(participants.CRT, participants.baseline_brier)
    rows.append(
        {
            "metric": "participant_CRT_vs_baseline_Brier_r",
            "estimate": float(r), "se": np.nan, "p_value": float(p),
            "ci_low": np.nan, "ci_high": np.nan,
            "note": "Lower Brier is better; this is an unaided task-performance association, not IQ.",
        }
    )

    # Restrict the focal analysis to advice explicitly labeled Algorithm.
    alg = data[data.advice == "Algorithm"].copy()
    if alg.id.nunique() != participants.id.nunique():
        raise ValueError("algorithm subset does not retain all participants")

    focal = clustered_model(
        "brier2 ~ brier1 + brier_r + CRT_z + C(item_no)", alg
    )
    rows.append(
        coefficient_row(
            "algorithm_final_Brier_CRT_z_itemFE",
            focal,
            "CRT_z",
            "Exploratory. Final Brier conditional on initial-human Brier, advice Brier, and item fixed effects; SE clustered by participant.",
        )
    )

    # Robustness variants for the focal coefficient.
    variants = {
        "algorithm_final_Brier_CRT_z_domainFE":
            "brier2 ~ brier1 + brier_r + CRT_z + C(domain)",
        "algorithm_final_Brier_CRT_z_itemFE_agreement":
            "brier2 ~ brier1 + brier_r + CRT_z + C(item_no) + agree + rel_peaks",
    }
    for label, formula in variants.items():
        model = clustered_model(formula, alg)
        rows.append(coefficient_row(label, model, "CRT_z", "Exploratory robustness variant."))

    # Does CRT simply increase advice weight, or sensitivity to advice quality?
    valid_mask = alg.outrange.astype(str).str.lower().isin({"true", "1", "yes"})
    valid = alg[valid_mask].copy()
    valid["advice_advantage"] = valid.brier1 - valid.brier_r
    valid["advantage_z"] = zscore(valid.advice_advantage)
    dwoa_model = clustered_model(
        "dwoa ~ CRT_z * advantage_z + C(item_no) + agree + rel_peaks", valid
    )
    rows.append(
        coefficient_row(
            "algorithm_DWOA_CRT_z",
            dwoa_model,
            "CRT_z",
            "Exploratory mean advice-weight association in valid DWOA cases.",
        )
    )
    rows.append(
        coefficient_row(
            "algorithm_DWOA_CRT_x_advice_advantage",
            dwoa_model,
            "CRT_z:advantage_z",
            "Exploratory test of whether CRT changes sensitivity to relative advice quality.",
        )
    )

    # Leave-one-item-out direction stability of the focal coefficient.
    loo = []
    for item in sorted(alg.item_no.unique()):
        sub = alg[alg.item_no != item]
        model = clustered_model(
            "brier2 ~ brier1 + brier_r + CRT_z + C(item_no)", sub
        )
        loo.append(float(model.params["CRT_z"]))
    rows.append(
        {
            "metric": "algorithm_final_Brier_CRT_z_LOO_min",
            "estimate": min(loo), "se": np.nan, "p_value": np.nan,
            "ci_low": np.nan, "ci_high": np.nan,
            "note": f"Leave-one-item-out coefficient minimum; {sum(x < 0 for x in loo)}/{len(loo)} coefficients negative.",
        }
    )
    rows.append(
        {
            "metric": "algorithm_final_Brier_CRT_z_LOO_max",
            "estimate": max(loo), "se": np.nan, "p_value": np.nan,
            "ci_low": np.nan, "ci_high": np.nan,
            "note": f"Leave-one-item-out coefficient maximum; {sum(x < 0 for x in loo)}/{len(loo)} coefficients negative.",
        }
    )

    # Participant-resampling bootstrap for the focal coefficient.
    rng = np.random.default_rng(args.seed)
    ids = alg.id.unique()
    boot = []
    for _ in range(args.bootstrap):
        sampled = rng.choice(ids, size=len(ids), replace=True)
        pieces = []
        for boot_id, participant_id in enumerate(sampled):
            piece = alg[alg.id == participant_id].copy()
            piece["boot_id"] = boot_id
            pieces.append(piece)
        boot_data = pd.concat(pieces, ignore_index=True)
        model = smf.ols(
            "brier2 ~ brier1 + brier_r + CRT_z + C(item_no)", data=boot_data
        ).fit()
        boot.append(float(model.params["CRT_z"]))
    q_low, q_high = np.quantile(boot, [0.025, 0.975])
    rows.append(
        {
            "metric": "algorithm_final_Brier_CRT_z_participant_bootstrap",
            "estimate": float(np.median(boot)), "se": float(np.std(boot, ddof=1)),
            "p_value": np.nan, "ci_low": float(q_low), "ci_high": float(q_high),
            "note": f"Participant-resampling percentile interval; {args.bootstrap} bootstrap draws.",
        }
    )

    summary = pd.DataFrame(rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(f"rows={len(data)} participants={data.id.nunique()} algorithm_rows={len(alg)}")
    print(summary.to_string(index=False))
    print("WARNING: all CRT results in this file are exploratory/hypothesis-generating.")


if __name__ == "__main__":
    main()
