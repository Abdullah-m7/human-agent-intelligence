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

Development run: **COMPLETE — 15/15 fixed development tasks**.

Observed task-level endpoints:

- standalone exact-match accuracy: `0/15 = 0.0000`;
- production parse rate: `10/15 = 0.6667`;
- HDC parse rate: `13/15 = 0.8667`;
- HDC pass rate: `2/15 = 0.1333`;
- ACT coverage: `1/15 = 0.0667`;
- ACT precision: `0/1 = 0.0000`;
- wrong autonomous acts: `1/15`;
- Unsafe Autonomy Mass: `1/15 = 0.0667`.

Task-balanced archived-human endpoints on the same 15 tasks:

- human ONE_SHOT: `0.7842`;
- HDC-routed Human+Qwen3.5-9B ONE_SHOT: `0.7366`;
- human RETRY3: `0.8703`;
- HDC-routed Human+Qwen3.5-9B RETRY3: `0.8100`.

Participant-weighted robustness endpoints:

- human ONE_SHOT: `0.7936`;
- joint ONE_SHOT: `0.7446`;
- human RETRY3: `0.8784`;
- joint RETRY3: `0.8164`.

The 15-row file passed the runner's deterministic resume-provenance validation. Qwen3.5-9B is classified **DEV_NONVIABLE** because production parse is below `0.80`, standalone accuracy is zero, and ACT coverage is below `2/15`.

Exact execution provenance is recorded in `reports/STAGE_004_CONTROLLER_STATUS.md`. Primary artefacts are:

- `results/stage004_llm_hdc/dev_qwen35-9b-q4km_rows.jsonl`;
- `results/stage004_llm_hdc/dev_qwen35-9b-q4km_summary.json`;
- `results/stage004_llm_hdc/dev_qwen35-9b-q4km_joint.json`.

## Development selection verdict

The frozen executable selector returned **NO_ELIGIBLE_LLM_PAIR**. Gemma is the only eligible model; Qwen3.5-4B and Qwen3.5-9B are nonviable under the frozen rule. No WEAK/STRONG pair is defined.

The confirmatory lock remains `DRAFT_DO_NOT_EVALUATE`, and the 60 evaluation tasks remain sealed.

## Artefact consistency note

The archived local Gemma rows reproduce the substantive recorded endpoints but re-summarize to production parse `12/15 = 0.8000` and HDC parse `14/15 = 0.9333`, while the earlier ledger recorded production parse `15/15 = 1.0000`. The archived rows were not altered and Gemma inference was not repeated. A separate selector input was mechanically derived from those rows; Gemma remains eligible exactly at the production-parse threshold, so the discrepancy does not change `NO_ELIGIBLE_LLM_PAIR`. Historical partial `-v2` files remain preserved and were not used for selection.

## Target-alignment audit

CogARC behavioral submissions correspond to the first source ARC test query (`test[0]`). Two source task JSONs retain a second original ARC query. Stage 003 was recomputed under the corrected participant-visible target definition and every headline ladder/cross-fit number remained unchanged. See `reports/STAGE_003_TARGET_ALIGNMENT_AUDIT.md`.

## Gate to evaluation

No model may enter the 60 sealed tasks merely because its development team result is interesting. Pair selection is controlled by `papers/01_agentic_bottleneck/STAGE004_MODEL_SELECTION_RULE_V1.md` and uses operational viability plus standalone development accuracy only.

That gate has now closed with `NO_ELIGIBLE_LLM_PAIR`. Evaluation is not authorized under this protocol version.
