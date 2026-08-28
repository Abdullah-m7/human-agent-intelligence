"""Confirmatory validation locked before CSCW2023 focal raw-data inspection.

Lock: papers/02_capability_susceptibility/VALIDATION_LOCK_V1.md
Lock commit: a51913e1920b5a45aaeea9f3dbb50afb6688a426

Primary questions:
M1 helpful susceptibility: among initial-disagreement trials with correct AI,
   does higher leave-one-trial-out (LOTO) task capability predict less switching?
M2 harmful susceptibility: among initial-disagreement trials with wrong AI,
   does higher LOTO task capability predict less switching?
M3 selectivity: pooled Capability x AI_correct model.

This script reproduces the authors' main-study exclusion rules without using the
focal switching outcome, reconstructs trial-level advice from task order and
reverse flags, and runs the pre-specified models. Task capability is not IQ.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial

TASKS = [
    "LP001030", "LP001806", "LP002534", "LP001882", "LP002068",
    "LP001849", "LP002142", "LP001451", "LP002181", "LP002840",
]
GROUPS = ("system", "accuracy", "analogy")
LOCK_COMMIT = "a51913e1920b5a45aaeea9f3dbb50afb6688a426"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reverse_answer(answer: str) -> str:
    if answer == "accept":
        return "reject"
    if answer == "reject":
        return "accept"
    raise ValueError(f"unexpected answer: {answer!r}")


def load_ground_truth(selected_samples: Path) -> dict[str, str]:
    df = pd.read_csv(selected_samples, usecols=["Loan_ID", "Loan_Status"])
    ans = dict(zip(df.Loan_ID, np.where(df.Loan_Status.eq("Y"), "accept", "reject")))
    missing = set(TASKS) - set(ans)
    if missing:
        raise ValueError(f"ground truth missing locked tasks: {sorted(missing)}")
    return ans


def read_usertask(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    df = pd.read_csv(path, usecols=["user_id", "task_id", "answer_type", "choice"])
    attn: dict[str, int] = {str(u): 0 for u in df.user_id.unique()}
    checks = {
        ("LP001518", "yes"),
        ("LP002723", "no"),
        ("ATI_attention", "6"),
        ("Numeracy Test", "3"),
        ("TiA_attention", "1"),
    }
    for row in df[df.answer_type.eq("attention")].itertuples(index=False):
        if (str(row.task_id), str(row.choice)) in checks:
            attn[str(row.user_id)] = attn.get(str(row.user_id), 0) + 1
    return df, attn


def reproduce_authors_exclusions(data_dir: Path) -> set[str]:
    demo = pd.read_csv(
        data_dir / "prolific_demographic.csv",
        usecols=["participant_id", "started_datetime", "time_taken"],
    )
    demo["participant_id"] = demo.participant_id.astype(str)
    timed = demo[demo.time_taken >= 420].copy()
    round2 = {
        r.participant_id: not str(r.started_datetime).startswith("2021-08-19")
        for r in timed.itertuples(index=False)
    }

    usertask, attn = read_usertask(data_dir / "usertask.csv")
    usertask["user_id"] = usertask.user_id.astype(str)
    valid_attention = {
        user for user in usertask.user_id.unique()
        if user in round2 and attn.get(user, 0) >= (5 if round2[user] else 2)
    }

    userinfo = pd.read_csv(data_dir / "userinfo.csv")
    userinfo["user_id"] = userinfo.user_id.astype(str)
    info = userinfo.set_index("user_id")
    file_users = {}
    for name in ["ATI_PreQ.csv", "PostQ_accuracy.csv", "PostQ_analogy.csv", "TiA_PostQ.csv", "pre_questionnaire.csv"]:
        z = pd.read_csv(data_dir / name, usecols=["user_id"])
        file_users[name] = set(z.user_id.astype(str))
    required = {
        "system": ["ATI_PreQ.csv", "TiA_PostQ.csv", "pre_questionnaire.csv"],
        "accuracy": ["ATI_PreQ.csv", "PostQ_accuracy.csv", "TiA_PostQ.csv", "pre_questionnaire.csv"],
        "analogy": ["ATI_PreQ.csv", "PostQ_analogy.csv", "TiA_PostQ.csv", "pre_questionnaire.csv"],
    }
    non_attention = usertask[~usertask.answer_type.eq("attention")]
    counts = non_attention.groupby("user_id").size()
    valid_complete: set[str] = set()
    for user in non_attention.user_id.unique():
        if user not in info.index or counts.get(user, 0) < 20:
            continue
        group = str(info.loc[user, "user_group"])
        if group not in required:
            continue
        if all(user in file_users[name] for name in required[group]):
            valid_complete.add(user)
    return valid_attention & valid_complete


def reconstruct_trials(data_dir: Path, selected_samples: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    reserved = reproduce_authors_exclusions(data_dir)
    userinfo = pd.read_csv(
        data_dir / "userinfo.csv",
        usecols=["user_id", "task_order_str", "reverse_flag_str", "user_group", "analogy_type"],
    )
    userinfo["user_id"] = userinfo.user_id.astype(str)
    userinfo = userinfo[userinfo.user_id.isin(reserved)].copy()

    usertask = pd.read_csv(
        data_dir / "usertask.csv",
        usecols=["user_id", "task_id", "answer_type", "choice"],
    )
    usertask["user_id"] = usertask.user_id.astype(str)
    usertask = usertask[usertask.user_id.isin(reserved) & ~usertask.answer_type.eq("attention")].copy()

    # Each participant/task/answer_type must identify one response.
    dup = usertask.groupby(["user_id", "task_id", "answer_type"])["choice"].nunique()
    if (dup > 1).any():
        raise ValueError("conflicting duplicate task responses detected")
    response = usertask.drop_duplicates(["user_id", "task_id", "answer_type"]).set_index(
        ["user_id", "task_id", "answer_type"]
    )["choice"].astype(str).to_dict()

    truth = load_ground_truth(selected_samples)
    rows: list[dict[str, object]] = []
    for u in userinfo.itertuples(index=False):
        order = str(u.task_order_str).split("|")
        flags = [bool(ast.literal_eval(x)) for x in str(u.reverse_flag_str).split("|")]
        if len(order) != 10 or len(flags) != 10 or sum(flags) != 3:
            raise ValueError(f"unexpected task/advice structure for user {u.user_id}")
        if set(order) != set(TASKS):
            raise ValueError(f"unexpected task set for user {u.user_id}")
        group = str(u.user_group)
        if group not in GROUPS:
            raise ValueError(f"unexpected condition {group!r}")
        for position, (task_id, wrong_ai) in enumerate(zip(order, flags), start=1):
            correct = truth[task_id]
            advice = reverse_answer(correct) if wrong_ai else correct
            first = response[(u.user_id, task_id, "base")]
            final = response[(u.user_id, task_id, group)]
            if first not in ("accept", "reject") or final not in ("accept", "reject"):
                raise ValueError("unexpected focal choice coding")
            rows.append({
                "user_id": u.user_id,
                "condition": group,
                "item": task_id,
                "position": position,
                "initial": first,
                "final": final,
                "truth": correct,
                "ai_advice": advice,
                "ai_correct": int(advice == correct),
                "initial_correct": int(first == correct),
                "final_correct": int(final == correct),
                "initial_disagreement": int(first != advice),
                "switch_to_ai": int(final == advice),
            })
    df = pd.DataFrame(rows)
    if len(df) != 10 * len(reserved):
        raise ValueError(f"expected 10 rows/user, got {len(df)} rows for {len(reserved)} users")

    # LOTO capability is based only on the other nine initial unaided decisions.
    sums = df.groupby("user_id").initial_correct.transform("sum")
    counts = df.groupby("user_id").initial_correct.transform("count")
    if not (counts == 10).all():
        raise ValueError("LOTO requires 10 complete main-study trials per participant")
    df["capability_loto"] = (sums - df.initial_correct) / (counts - 1)
    mean = float(df.capability_loto.mean())
    sd = float(df.capability_loto.std(ddof=0))
    if not math.isfinite(sd) or sd <= 0:
        raise ValueError("capability LOTO has zero/nonfinite variance")
    df["capability_z"] = (df.capability_loto - mean) / sd
    df["capability_full10"] = sums / counts

    metadata = {
        "lock_commit": LOCK_COMMIT,
        "participants": int(df.user_id.nunique()),
        "trials": int(len(df)),
        "groups": {k: int(v) for k, v in df.drop_duplicates("user_id").condition.value_counts().sort_index().items()},
        "capability_standardization_scope": "all 2810 reconstructed participant-trials before disagreement filtering",
        "capability_loto_mean": mean,
        "capability_loto_sd_population": sd,
    }
    return df, metadata


def fit_clustered_glm(formula: str, data: pd.DataFrame):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = smf.glm(formula, data=data, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": data["user_id"]}
        )
    unstable = (
        not getattr(model, "converged", True)
        or not np.isfinite(model.params).all()
        or not np.isfinite(model.bse).all()
        or np.max(np.abs(model.params.to_numpy())) > 15
        or any("separation" in str(w.message).lower() for w in caught)
    )
    return model, unstable, [str(w.message) for w in caught]


def fit_gee(formula: str, data: pd.DataFrame):
    return smf.gee(
        formula, groups="user_id", data=data,
        family=Binomial(), cov_struct=Exchangeable(),
    ).fit()


def term_row(model_name: str, model, term: str, n: int, estimator: str) -> dict[str, object]:
    ci = model.conf_int().loc[term]
    return {
        "model": model_name,
        "term": term,
        "estimate": float(model.params[term]),
        "se": float(model.bse[term]),
        "p_value": float(model.pvalues[term]),
        "ci_low": float(ci.iloc[0]),
        "ci_high": float(ci.iloc[1]),
        "n_trials": int(n),
        "estimator": estimator,
    }


def run_primary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    dis = df[df.initial_disagreement.eq(1)].copy()
    correct = dis[dis.ai_correct.eq(1)].copy()
    wrong = dis[dis.ai_correct.eq(0)].copy()
    formulas = {
        "M1_helpful": "switch_to_ai ~ capability_z + C(condition) + C(item)",
        "M2_harmful": "switch_to_ai ~ capability_z + C(condition) + C(item)",
        "M3_selectivity": "switch_to_ai ~ capability_z * ai_correct + C(condition) + C(item)",
    }
    frames = {"M1_helpful": correct, "M2_harmful": wrong, "M3_selectivity": dis}

    initial_models = {}
    unstable_any = False
    warnings_by_model = {}
    for name in formulas:
        m, unstable, caught = fit_clustered_glm(formulas[name], frames[name])
        initial_models[name] = m
        unstable_any = unstable_any or unstable
        warnings_by_model[name] = caught
    if unstable_any:
        estimator = "GEE_binomial_logit_exchangeable"
        models = {name: fit_gee(formulas[name], frames[name]) for name in formulas}
    else:
        estimator = "GLM_binomial_logit_participant_clustered_SE"
        models = initial_models

    rows = [
        term_row("M1_helpful", models["M1_helpful"], "capability_z", len(correct), estimator),
        term_row("M2_harmful", models["M2_harmful"], "capability_z", len(wrong), estimator),
        term_row("M3_selectivity", models["M3_selectivity"], "capability_z", len(dis), estimator),
    ]
    interaction_terms = [t for t in models["M3_selectivity"].params.index if "capability_z:ai_correct" in t or "ai_correct:capability_z" in t]
    if len(interaction_terms) != 1:
        raise RuntimeError(f"could not uniquely locate M3 interaction: {interaction_terms}")
    rows.append(term_row("M3_selectivity", models["M3_selectivity"], interaction_terms[0], len(dis), estimator))

    # Marginal predicted switch probabilities: empirical standardization over
    # observed condition/item rows in the pooled disagreement sample.
    pred_rows = []
    m3 = models["M3_selectivity"]
    for zval in (-1.0, 0.0, 1.0):
        for ai_correct in (0, 1):
            new = dis.copy()
            new["capability_z"] = zval
            new["ai_correct"] = ai_correct
            pred = np.asarray(m3.predict(new), dtype=float)
            pred_rows.append({
                "capability_z": zval,
                "ai_correct": ai_correct,
                "marginal_switch_probability": float(np.mean(pred)),
                "n_standardization_rows": int(len(new)),
            })

    meta = {
        "estimator": estimator,
        "glm_instability_detected": bool(unstable_any),
        "glm_warnings": warnings_by_model,
        "disagreement_trials": int(len(dis)),
        "helpful_disagreement_trials": int(len(correct)),
        "harmful_disagreement_trials": int(len(wrong)),
        "participants_with_disagreement": int(dis.user_id.nunique()),
        "participants_helpful": int(correct.user_id.nunique()),
        "participants_harmful": int(wrong.user_id.nunique()),
        "outcome_variation": {
            "helpful_switch_mean": float(correct.switch_to_ai.mean()),
            "harmful_switch_mean": float(wrong.switch_to_ai.mean()),
        },
    }
    return pd.DataFrame(rows), pd.DataFrame(pred_rows), meta


def decision(primary: pd.DataFrame) -> dict[str, object]:
    h1 = primary[(primary.model == "M1_helpful") & (primary.term == "capability_z")].iloc[0]
    h2 = primary[(primary.model == "M2_harmful") & (primary.term == "capability_z")].iloc[0]
    both_negative = bool(h1.estimate < 0 and h2.estimate < 0)
    strict = bool(both_negative and h1.p_value < 0.025 and h2.p_value < 0.025)
    if strict:
        label = "CONFIRMATORY_SUPPORT"
    elif both_negative:
        label = "DIRECTIONALLY_CONSISTENT_NOT_CONFIRMATORY"
    else:
        label = "TWO_SIDED_SUSCEPTIBILITY_NOT_SUPPORTED"
    return {
        "H1_helpful_estimate_negative": bool(h1.estimate < 0),
        "H1_two_sided_p": float(h1.p_value),
        "H2_harmful_estimate_negative": bool(h2.estimate < 0),
        "H2_two_sided_p": float(h2.p_value),
        "bonferroni_alpha_each": 0.025,
        "classification": label,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("data/external/cscw2023/data_unpacked"))
    p.add_argument("--out-dir", type=Path, default=Path("results/cscw2023_validation"))
    args = p.parse_args()
    main_dir = args.root / "main_exp" / "anonymous_data"
    selected = args.root / "loan_data_selection" / "selected_samples.csv"
    df, reconstruction_meta = reconstruct_trials(main_dir, selected)
    primary, predictions, primary_meta = run_primary(df)
    verdict = decision(primary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    primary.to_csv(args.out_dir / "primary_models.csv", index=False)
    predictions.to_csv(args.out_dir / "m3_marginal_predictions.csv", index=False)
    meta = {
        **reconstruction_meta,
        **primary_meta,
        "decision": verdict,
        "input_sha256": {
            "userinfo.csv": sha256(main_dir / "userinfo.csv"),
            "usertask.csv": sha256(main_dir / "usertask.csv"),
            "prolific_demographic.csv": sha256(main_dir / "prolific_demographic.csv"),
            "selected_samples.csv": sha256(selected),
        },
        "construct_warning": "capability_loto is task-specific unaided accuracy, not IQ or general intelligence",
    }
    (args.out_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print("LOCK_COMMIT", LOCK_COMMIT)
    print("ESTIMATOR", primary_meta["estimator"])
    print(primary.to_string(index=False))
    print("\nM3_MARGINAL_PREDICTIONS")
    print(predictions.to_string(index=False))
    print("\nDECISION")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
