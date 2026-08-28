"""Locked Stage-003 validation of a redundancy-based autonomy gate.

The protocol is fixed in papers/01_agentic_bottleneck/AUTONOMY_GATE_VALIDATION_LOCK_V1.md.
This executable compares tasks with exactly one fitting detector against tasks
with two or more fitting detectors on ARC-AGI-2 evaluation.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

LOCK_COMMIT = "a89dc690e5eab6dba1ddbc2985859a71e181650f"
SOLVER_REVISION = "e151937e34c8b34f953833a0dab75797fc737ba4"
ARC2_REVISION = "f3283f727488ad98fe575ea6a5ac981e4a188e49"


def load_task(fp: Path) -> dict:
    t = json.loads(fp.read_text())
    return {
        "train": [(np.array(p["input"], int), np.array(p["output"], int)) for p in t["train"]],
        "test": [(np.array(p["input"], int), np.array(p["output"], int)) for p in t["test"]],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver-root", type=Path, required=True)
    ap.add_argument("--arc2-root", type=Path, required=True)
    ap.add_argument("--summary", type=Path, default=Path("results/arc2_autonomy_gate_validation_summary.csv"))
    args = ap.parse_args()
    sys.path.insert(0, str(args.solver_root))
    harness = importlib.import_module("harness"); registry = importlib.import_module("registry")
    dets = registry.load_all()
    if len(dets) != 321:
        raise ValueError(f"locked solver expected 321 detectors, observed {len(dets)}")
    files = sorted((args.arc2_root / "data" / "evaluation").glob("*.json"))
    if len(files) != 120:
        raise ValueError(f"locked ARC-AGI-2 evaluation expected 120 tasks, observed {len(files)}")
    rows = []
    for fp in files:
        task = load_task(fp); preds, nfit = harness.solve_task(task, dets)
        ok = True
        for (_, gt), cand in zip(task["test"], preds):
            if gt is None or not any(np.array_equal(c, gt) for c in cand):
                ok = False; break
        rows.append({"trial": fp.stem, "correct": int(ok), "nfit": int(nfit)})
    d = pd.DataFrame(rows); one = d[d.nfit == 1]; red = d[d.nfit >= 2]
    diff = red.correct.mean() - one.correct.mean() if len(red) and len(one) else np.nan
    table = [[int(red.correct.sum()), int(len(red) - red.correct.sum())], [int(one.correct.sum()), int(len(one) - one.correct.sum())]]
    odds, p = fisher_exact(table, alternative="greater") if len(red) and len(one) else (np.nan, np.nan)
    if len(red) < 5:
        verdict = "INCONCLUSIVE_LOW_COVERAGE"
    elif diff > 0 and p < .05:
        verdict = "SUPPORTED"
    elif diff > 0:
        verdict = "DIRECTIONALLY_CONSISTENT"
    else:
        verdict = "NOT_SUPPORTED"
    out = []
    out.append({"metric": "locked_metadata", "value": np.nan, "n": len(d), "note": f"lock={LOCK_COMMIT}; solver={SOLVER_REVISION}; arc2={ARC2_REVISION}"})
    out.append({"metric": "standalone_accuracy", "value": d.correct.mean(), "n": len(d), "note": "all evaluation tasks"})
    out.append({"metric": "precision_nfit_eq_1", "value": one.correct.mean() if len(one) else np.nan, "n": len(one), "note": "primary comparator"})
    out.append({"metric": "precision_nfit_ge_2", "value": red.correct.mean() if len(red) else np.nan, "n": len(red), "note": "locked redundancy group"})
    out.append({"metric": "precision_difference", "value": diff, "n": len(red) + len(one), "note": "nfit>=2 minus nfit==1"})
    out.append({"metric": "fisher_one_sided_p", "value": p, "n": len(red) + len(one), "note": f"odds={odds}"})
    for threshold in (1, 2):
        act = d.nfit >= threshold
        out.extend([
            {"metric": f"coverage_nfit_ge_{threshold}", "value": act.mean(), "n": int(act.sum()), "note": "all 120 tasks denominator"},
            {"metric": f"act_precision_nfit_ge_{threshold}", "value": d.loc[act, "correct"].mean() if act.any() else np.nan, "n": int(act.sum()), "note": "conditional on ACT"},
            {"metric": f"wrong_act_rate_all_nfit_ge_{threshold}", "value": float((act & (d.correct == 0)).mean()), "n": int((act & (d.correct == 0)).sum()), "note": "wrong autonomous acts / 120"},
        ])
    out.append({"metric": "verdict", "value": np.nan, "n": len(red), "note": verdict})
    result = pd.DataFrame(out); args.summary.parent.mkdir(parents=True, exist_ok=True); result.to_csv(args.summary, index=False)
    print(result.to_string(index=False))

if __name__ == "__main__":
    main()
