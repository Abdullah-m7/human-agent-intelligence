"""Generate compact Stage-001 summaries for the stylized agentic bottleneck model."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

import pandas as pd

from src.agentic_bottleneck import iter_stage001, row


def median_abs(frame: pd.DataFrame, col: str) -> float:
    return float(frame[col].abs().median())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beta-spec", type=float, default=0.20)
    parser.add_argument(
        "--summary", type=Path, default=Path("results/agentic_stage001_summary.csv")
    )
    args = parser.parse_args()

    df = pd.DataFrame([row(p) for p in iter_stage001(args.beta_spec)])
    records: list[dict[str, object]] = []

    for scope, frame in (
        ("all", df),
        ("interior_Aeff", df[(df.agent_effective > 0.05) & (df.agent_effective < 0.95)]),
    ):
        for autonomy, group in frame.groupby("autonomy"):
            records.append(
                {
                    "section": "role_migration",
                    "scope": scope,
                    "key": f"autonomy={autonomy:.2f}",
                    "n": len(group),
                    "median_abs_dJ_dH": median_abs(group, "dJ_d_human"),
                    "median_abs_dJ_dV": median_abs(group, "dJ_d_verification"),
                    "median_abs_dJ_dS": median_abs(group, "dJ_d_specification"),
                    "median_specification_share": float(group.share_specification.median()),
                    "value": float("nan"),
                }
            )

    # Gating gain does not depend on alpha, so one alpha slice is sufficient.
    unique = df[df.autonomy == 0.0].copy()
    worse = unique.gating_gain_vs_full_autonomy < 0
    records.append(
        {
            "section": "gating",
            "scope": "unique_parameter_configurations",
            "key": "gating_worse_fraction",
            "n": len(unique),
            "median_abs_dJ_dH": float("nan"),
            "median_abs_dJ_dV": float("nan"),
            "median_abs_dJ_dS": float("nan"),
            "median_specification_share": float("nan"),
            "value": float(worse.mean()),
        }
    )
    for agent, group in unique.groupby("agent"):
        records.append(
            {
                "section": "gating_by_agent",
                "scope": "unique_parameter_configurations",
                "key": f"agent={agent:.2f}",
                "n": len(group),
                "median_abs_dJ_dH": float("nan"),
                "median_abs_dJ_dV": float("nan"),
                "median_abs_dJ_dS": float("nan"),
                "median_specification_share": float("nan"),
                "value": float((group.gating_gain_vs_full_autonomy < 0).mean()),
            }
        )

    out = pd.DataFrame(records)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.summary, index=False)
    print(f"grid_rows={len(df)} unique_configs={len(unique)}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
