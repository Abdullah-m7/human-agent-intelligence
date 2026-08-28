# Stage 004 — Development Ledger V1

Date: 2026-08-29

## Scope

This ledger records only development-stage evidence. The 60-task Stage-004 evaluation split is still sealed and has not been queried under the confirmatory protocol.

## Gemma-4-26B-A4B Q4_K_M

Development run: **COMPLETE — 15/15 fixed development tasks**.

Exact HDC contract: production inference on training pairs + participant-visible `test[0]` input; one hash-selected training demonstration withheld for HDC; `ACT = production_valid AND hdc_correct`.

Observed task-level endpoints:

- standalone exact-match accuracy: `2/15 = 0.1333`;
- production parse rate: `15/15 = 1.0000`;
- HDC pass rate: `6/15 = 0.4000`;
- ACT coverage: `6/15 = 0.4000`;
- ACT precision: `2/6 = 0.3333`;
- wrong autonomous acts: `4/15`;
- Unsafe Autonomy Mass: `4/15 = 0.2667`.

HDC diagnostics:

- HDC pass conditional on correct production: `1.0000`;
- HDC pass conditional on wrong production: `0.3077`.

Task-balanced archived-human endpoints on the same 15 tasks:

- human ONE_SHOT: `0.7842`;
- HDC-routed Human+Gemma ONE_SHOT: `0.5785`;
- human RETRY3: `0.8703`;
- HDC-routed Human+Gemma RETRY3: `0.6292`.

Participant-weighted robustness endpoints:

- human ONE_SHOT: `0.7936`;
- joint ONE_SHOT: `0.5728`;
- human RETRY3: `0.8784`;
- joint RETRY3: `0.6226`.

Development interpretation: the single-demonstration HDC is **not a high-precision autonomy certificate for this model**. It over-authorizes enough wrong production outputs to make the routed system materially worse than the archived human receiver alone on development. This is descriptive development evidence, not a confirmatory Stage-004 replication.

## Qwen3.5-4B Q4_K_M

Development status: **DEV_NONVIABLE — stopped after 6/15 tasks**.

Observed before stopping:

- standalone exact-match accuracy: `0/6`;
- HDC pass: `0/6`;
- ACT: `0/6`;
- production parse rate: `3/6 = 0.5000`.

Reason for stopping: there was no autonomous region to evaluate and substantial output-contract noncompliance. Using this state as the “weak model” would confound interface compliance with capability. It is excluded by the frozen Stage-004 model-selection rule.

## Qwen3.5-9B Q4_K_M

Development execution was launched locally after Qwen3.5-4B was classified nonviable. At the time the pre-evaluation selection rule was committed, **no Qwen3.5-9B development row or aggregate result had been inspected by the controller**.

Status in this ledger: **OUTCOME NOT YET INSPECTED**.

## Target-alignment audit

CogARC behavioral submissions correspond to the first source ARC test query (`test[0]`). Two source task JSONs retain a second original ARC query. Stage 003 was recomputed under the corrected participant-visible target definition and every headline ladder/cross-fit number remained unchanged. See `reports/STAGE_003_TARGET_ALIGNMENT_AUDIT.md`.

## Gate to evaluation

No model may enter the 60 sealed tasks merely because its development team result is interesting. Pair selection is controlled by `papers/01_agentic_bottleneck/STAGE004_MODEL_SELECTION_RULE_V1.md` and uses operational viability plus standalone development accuracy only.
