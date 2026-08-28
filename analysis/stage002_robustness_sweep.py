"""Stage-002 robustness sweeps for Paper 01.

Two alternative models are evaluated:

1. correlated human/agent correctness, with infeasible requested correlations
   projected to valid Bernoulli Fréchet bounds and projection rates reported;
2. confidence-selective review over latent task difficulty, including matched
   and asymmetric human/agent difficulty-response regimes.

The purpose is to test whether Stage-001 role migration survives relaxed
assumptions. Results remain computational, not empirical human prevalence.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agentic_bottleneck import effective_agent, iter_stage001
from src.robustness_models import (
    SelectiveReviewParams,
    bernoulli_joint,
    correlated_gated_accuracy,
    correlated_sensitivity,
    selective_profile,
    selective_sensitivity,
    selective_sensitivity_shares,
)


def correlated_rows() -> pd.DataFrame:
    records: list[dict[str, float]] = []
    for requested_corr in (-0.40, 0.00, 0.40):
        for p in iter_stage001(beta_spec=0.20):
            a = effective_agent(p)
            _, _, _, _, realized_corr = bernoulli_joint(a, p.human, requested_corr)
            gate = correlated_gated_accuracy(p, requested_corr)
            sens = {
                field: correlated_sensitivity(p, requested_corr, field)
                for field in ("human", "specification", "verification", "specificity")
            }
            abs_sens = {field: abs(value) for field, value in sens.items()}
            total = sum(abs_sens.values())
            records.append(
                {
                    "requested_corr": requested_corr,
                    "realized_corr": realized_corr,
                    "corr_projected": float(abs(realized_corr - requested_corr) > 1e-8),
                    "agent": p.agent,
                    "human": p.human,
                    "specification": p.specification,
                    "verification": p.verification,
                    "specificity": p.specificity,
                    "autonomy": p.autonomy,
                    "agent_effective": a,
                    "gating_gain_vs_autonomous": gate - a,
                    "dJ_d_human": sens["human"],
                    "dJ_d_specification": sens["specification"],
                    "dJ_d_verification": sens["verification"],
                    "dJ_d_specificity": sens["specificity"],
                    "share_specification": abs_sens["specification"] / total if total else 0.0,
                }
            )
    return pd.DataFrame(records)


def selective_rows() -> pd.DataFrame:
    grid = {
        "agent": [0.55, 0.70, 0.85, 0.95],
        "human": [0.45, 0.60, 0.75, 0.90],
        "specification": [0.30, 0.50, 0.70, 0.90],
        "verification": [0.30, 0.50, 0.70, 0.90],
        "specificity": [0.70, 0.85, 0.95],
        "review_threshold": [0.55, 0.65, 0.75, 0.85, 0.95],
    }
    regimes = {
        "matched": (1.20, 1.20),
        "agent_steeper": (1.60, 0.80),
        "human_steeper": (0.80, 1.60),
    }
    keys = list(grid)
    records: list[dict[str, object]] = []
    for regime, (agent_scale, human_scale) in regimes.items():
        for values in itertools.product(*(grid[key] for key in keys)):
            base = dict(zip(keys, values))
            p = SelectiveReviewParams(
                **base,
                agent_difficulty_scale=agent_scale,
                human_difficulty_scale=human_scale,
            )
            profile = selective_profile(p)
            sens = {
                field: selective_sensitivity(p, field)
                for field in ("human", "specification", "verification", "specificity")
            }
            shares = selective_sensitivity_shares(p)
            records.append(
                {
                    **base,
                    "difficulty_regime": regime,
                    "agent_difficulty_scale": agent_scale,
                    "human_difficulty_scale": human_scale,
                    **profile,
                    "review_gain_vs_no_review": profile["joint_accuracy"] - profile["mean_agent_accuracy"],
                    "dJ_d_human": sens["human"],
                    "dJ_d_specification": sens["specification"],
                    "dJ_d_verification": sens["verification"],
                    "dJ_d_specificity": sens["specificity"],
                    "share_specification": shares["specification"],
                }
            )
    return pd.DataFrame(records)


def _base_summary_row() -> dict[str, float]:
    return {
        "median_realized_corr": float("nan"),
        "corr_projection_fraction": float("nan"),
        "review_harm_fraction": float("nan"),
        "review_sign_change_fraction": float("nan"),
    }


def summarize_correlated(df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for corr, corr_frame in df.groupby("requested_corr"):
        projection_fraction = float(corr_frame.corr_projected.mean())
        for autonomy, group in corr_frame.groupby("autonomy"):
            rows.append(
                {
                    **_base_summary_row(),
                    "model": "correlated_errors",
                    "setting": f"corr={corr:+.2f};autonomy={autonomy:.2f}",
                    "n": len(group),
                    "median_effective_autonomy": autonomy,
                    "median_realized_corr": float(group.realized_corr.median()),
                    "corr_projection_fraction": projection_fraction,
                    "median_abs_dJ_dH": float(group.dJ_d_human.abs().median()),
                    "median_abs_dJ_dV": float(group.dJ_d_verification.abs().median()),
                    "median_abs_dJ_dS": float(group.dJ_d_specification.abs().median()),
                    "median_specification_share": float(group.share_specification.median()),
                }
            )
        unique = corr_frame[corr_frame.autonomy == 0.0]
        rows.append(
            {
                **_base_summary_row(),
                "model": "correlated_errors",
                "setting": f"corr={corr:+.2f};gating_harm",
                "n": len(unique),
                "median_effective_autonomy": float("nan"),
                "median_realized_corr": float(unique.realized_corr.median()),
                "corr_projection_fraction": float(unique.corr_projected.mean()),
                "median_abs_dJ_dH": float("nan"),
                "median_abs_dJ_dV": float("nan"),
                "median_abs_dJ_dS": float("nan"),
                "median_specification_share": float("nan"),
                "review_harm_fraction": float((unique.gating_gain_vs_autonomous < 0).mean()),
            }
        )
    return rows


def summarize_selective(df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    config_keys = ["agent", "human", "specification", "verification", "specificity"]
    for regime, regime_frame in df.groupby("difficulty_regime"):
        pivot = regime_frame.pivot_table(
            index=config_keys,
            columns="review_threshold",
            values="review_gain_vs_no_review",
        )
        signs = np.sign(pivot)
        sign_change_fraction = float(
            ((signs.max(axis=1) > 0) & (signs.min(axis=1) < 0)).mean()
        )
        for threshold, group in regime_frame.groupby("review_threshold"):
            rows.append(
                {
                    **_base_summary_row(),
                    "model": "selective_review",
                    "setting": f"regime={regime};threshold={threshold:.2f}",
                    "n": len(group),
                    "median_effective_autonomy": float(group.effective_autonomy.median()),
                    "median_abs_dJ_dH": float(group.dJ_d_human.abs().median()),
                    "median_abs_dJ_dV": float(group.dJ_d_verification.abs().median()),
                    "median_abs_dJ_dS": float(group.dJ_d_specification.abs().median()),
                    "median_specification_share": float(group.share_specification.median()),
                    "review_harm_fraction": float((group.review_gain_vs_no_review < 0).mean()),
                    "review_sign_change_fraction": sign_change_fraction,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary", type=Path, default=Path("results/stage002_robustness_summary.csv")
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=Path("results/stage002_raw")
    )
    args = parser.parse_args()

    corr = correlated_rows()
    selective = selective_rows()
    summary = pd.DataFrame(summarize_correlated(corr) + summarize_selective(selective))
    summary = summary.sort_values(["model", "setting"]).reset_index(drop=True)

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    corr.to_csv(args.raw_dir / "correlated_errors.csv", index=False)
    selective.to_csv(args.raw_dir / "selective_review.csv", index=False)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)

    print(f"correlated_rows={len(corr)} selective_rows={len(selective)}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
