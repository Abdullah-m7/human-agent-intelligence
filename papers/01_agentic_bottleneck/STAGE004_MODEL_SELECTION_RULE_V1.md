# Stage 004 — Pre-Evaluation Model-Selection Rule V1

Date: 2026-08-29

## Status

**PRE-EVALUATION SELECTION RULE — FROZEN BEFORE INSPECTION OF ANY QWEN3.5-9B DEVELOPMENT ROW.**

At this point the 60-task evaluation split remains sealed. Gemma-4-26B-A4B development outcomes and a six-task Qwen3.5-4B viability probe have been inspected. Qwen3.5-9B execution had been launched locally, but no Qwen3.5-9B task row or aggregate outcome had been inspected by the controller when this rule was committed.

This document controls which generative-LLM states, if any, may proceed to the confirmatory Stage-004 evaluation. It is intentionally based on operational viability and standalone task capability, not on the desired Capability–Autonomy Gap outcome.

## Fixed development candidates

The candidate pool is limited to the already-declared local Stage-004 models under the exact HDC prompt/parser contract in `analysis/stage004_llm_hdc.py`:

1. Qwen3.5-4B Q4_K_M;
2. Qwen3.5-9B Q4_K_M;
3. Gemma-4-26B-A4B Q4_K_M.

No newly introduced model may be substituted into the Stage-004 confirmatory test under this rule. A new model family requires a new versioned selection protocol while evaluation remains sealed.

## Operational viability gate

A model is **EVAL_ELIGIBLE** only if, on all 15 fixed development tasks:

- the run completes without outcome-dependent task deletion;
- production parse rate is at least `0.80`;
- HDC parse rate is at least `0.80`;
- standalone exact-match accuracy is strictly greater than zero;
- ACT coverage is at least `0.10` (at least 2/15 tasks under the exact HDC rule).

A model failing any criterion is **DEV_NONVIABLE** for the confirmatory comparison. This is an interface/measurement eligibility decision, not an assertion about the model's general intelligence.

## Early nonviability already observed

Qwen3.5-4B was stopped after six development tasks after producing:

- standalone accuracy `0/6`;
- HDC pass `0/6`;
- ACT `0/6`;
- production parse rate `3/6`.

It is therefore classified **DEV_NONVIABLE** and cannot be used as the artificial “weak” endpoint of a capability ladder. Its failures would confound interface compliance with capability.

## Pair-selection rule

After all remaining eligible candidates complete development:

1. discard every `DEV_NONVIABLE` candidate;
2. rank eligible candidates by **development standalone exact-match accuracy only**;
3. if fewer than two eligible candidates remain, Stage 004 does **not** unlock confirmatory evaluation and records `NO_ELIGIBLE_LLM_PAIR`;
4. if exactly two eligible candidates remain, use those two;
5. if more than two remain, select the two adjacent highest-accuracy states whose standalone accuracies are strictly ordered; ties are broken by lower mean production token count, then lexicographic model label.

Crucially, the following development quantities are **forbidden inputs to pair selection**:

- Unsafe Autonomy Mass;
- ACT precision beyond the minimum viability gate;
- ONE_SHOT joint performance;
- RETRY3 joint performance;
- Human Leverage;
- whether the development data exhibit a Capability–Autonomy Gap.

Those quantities may be reported descriptively, but cannot determine which pair receives evaluation.

## Confirmatory ordering

For the selected pair, `WEAK` and `STRONG` are defined solely by development standalone accuracy. The confirmatory evaluation asks whether the same ordering exists on the sealed 60 tasks and, if so, whether the stronger standalone state can nevertheless produce higher Unsafe Autonomy Mass and lower task-balanced ONE_SHOT joint performance.

If the sealed evaluation reverses or ties the standalone ordering, the Capability–Autonomy Gap replication endpoint is **INCONCLUSIVE_CAPABILITY_ORDER**, not silently reordered after seeing evaluation results.

## Minimum evaluation coverage

Before evaluation, the final confirmatory lock must additionally require both selected states to ACT on at least `6/60 = 10%` of sealed tasks. A state below that level yields `INCONCLUSIVE_LOW_AUTONOMY_COVERAGE`; no alternative gate may be substituted after evaluation begins.

## Primary weighting

The primary joint-system endpoint is **task-balanced** ONE_SHOT performance: each ARC task receives equal weight and the human receiver value is the empirical CogARC success rate on that task.

Participant-weighted ONE_SHOT and both RETRY3 versions are robustness endpoints.

## Integrity boundary

This selection rule does not claim that model size causes capability or autonomy. It prevents a more basic threat: selecting the agent pair because its development team outcomes happen to support the desired paper narrative.
