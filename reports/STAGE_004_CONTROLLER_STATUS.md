# Stage 004 — Controller Status

Date: 2026-08-29

## Decision

**STAGE 004: IN PROGRESS**

**CONFIRMATORY EVALUATION: SEALED / DO NOT RUN**

Current confirmatory lock status is `DRAFT_DO_NOT_EVALUATE`. No controller-approved query to the 60-task evaluation split is permitted until development selection is complete and the lock is finalized in a later commit.

## Durable evidence already established

### Stage 003 target alignment

A target-alignment audit found that CogARC participant behavior corresponds to source ARC `test[0]`. The two source tasks retaining an extra ARC test query were corrected to the participant-visible target. Full Stage-003 recomputation left all headline machine-ladder and Human Leverage results unchanged.

### Gemma development

Gemma-4-26B-A4B Q4_K_M completed all 15 fixed development tasks under the HDC contract.

Recorded development endpoints:

- standalone exact-match accuracy: `2/15 = 0.1333`;
- production parse rate: `15/15 = 1.0000`;
- HDC pass / ACT coverage: `6/15 = 0.4000`;
- ACT precision: `2/6 = 0.3333`;
- wrong autonomous acts: `4/15`;
- Unsafe Autonomy Mass: `4/15 = 0.2667`;
- task-balanced human ONE_SHOT: `0.7842`;
- task-balanced HDC-routed Human+Gemma ONE_SHOT: `0.5785`;
- task-balanced human RETRY3: `0.8703`;
- task-balanced HDC-routed Human+Gemma RETRY3: `0.6292`.

Interpretation is development-only: single-demonstration HDC over-authorizes Gemma often enough to make the routed team substantially worse than the archived human receiver on these development tasks. This is not a confirmatory replication.

### Qwen3.5-4B development

Qwen3.5-4B Q4_K_M was classified `DEV_NONVIABLE` after 6 development tasks:

- standalone accuracy `0/6`;
- HDC pass `0/6`;
- ACT `0/6`;
- production parse rate `3/6 = 0.50`.

Under the earlier frozen pre-evaluation selection rule, this state cannot be used as an artificial weak endpoint.

### Qwen3.5-9B

A local development execution had been launched, but no controller-inspected aggregate result is durably recorded in GitHub yet. **Do not infer its outcome from process state or stale local files.** Development selection remains incomplete until its 15-task result is recovered/re-run under matching provenance and inspected.

## Authoritative selection governance

The authoritative pre-evaluation model-selection rule is:

`papers/01_agentic_bottleneck/STAGE004_MODEL_SELECTION_RULE_V1.md`

Frozen in commit:

`cc3be19c67eb88b9a1d053939a01690423e04463`

It predates inspection of Qwen3.5-9B development outcomes. It chooses among eligible states using operational viability and standalone development accuracy only. Team outcomes, Unsafe Autonomy Mass, Human Leverage, and the desired inversion are forbidden selection inputs.

## Governance correction recorded on 2026-08-29

A later file, `STAGE004_DEV_SELECTION_POLICY_V1.md`, was briefly added from a stale controller view and conflicted with the already-frozen pre-evaluation selection rule by fixing Qwen4B→Qwen9B despite Qwen4B already being classified nonviable.

The conflict was corrected immediately:

- the late conflicting policy was deleted in commit `ab7e3855f4c1325ecdceeb79f025b97372c92cd7`;
- the Stage-004 protocol was restored to the authoritative earlier rule in commit `072888beb4958b82b879064b5b7f40c7015e5259`.

Git history intentionally preserves both the mistaken late commit and its correction. The late policy has **no scientific authority**.

## Current blocker

The authorized local computer is currently disconnected from the remote execution tool. Therefore Qwen3.5-9B inference cannot be completed or recovered in this controller session.

This is an execution blocker only. It does not justify changing the candidate pool, selection rule, HDC gate, split, or confirmatory criteria.

## Next executable gate after device reconnection

1. Synchronize local `stage-004-second-agent-family` with the remote branch before any further run.
2. Recover the Qwen3.5-9B development rows only if their stored row provenance passes the runner's resume validation; otherwise restart that development state from the fixed 15-task split.
3. Complete all 15 development tasks.
4. Run `analysis/stage004_model_selection.py` on the eligible complete development summaries.
5. If fewer than two eligible states remain, record `NO_ELIGIBLE_LLM_PAIR` and do **not** unlock evaluation.
6. If a pair is selected, fill every pending provenance field in `STAGE004_CONFIRMATORY_LOCK_V1.md`, change the status to `LOCKED` in a dedicated commit, and only then permit the full 60-task evaluation.

## Publication boundary

Stage 004 is a falsifiable replication attempt. `NO_ELIGIBLE_LLM_PAIR`, `INCONCLUSIVE_*`, or `NO_REPLICATION` are valid scientific outcomes and must not trigger outcome-driven replacement of the frozen design.