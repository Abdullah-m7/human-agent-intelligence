# Stage 004 — Controller Status

Date: 2026-08-29

## Decision

**STAGE 004 DEVELOPMENT: COMPLETE — NO_ELIGIBLE_LLM_PAIR**

**CONFIRMATORY EVALUATION: SEALED / DO NOT RUN**

Current confirmatory lock status is `DRAFT_DO_NOT_EVALUATE`. The frozen development selector found fewer than two eligible models, so the 60-task evaluation split must remain sealed and no confirmatory lock may be finalized under this candidate pool.

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

Qwen3.5-9B Q4_K_M completed all 15 fixed development tasks under the unchanged HDC contract.

Recorded development endpoints:

- standalone exact-match accuracy: `0/15 = 0.0000`;
- production parse rate: `10/15 = 0.6667`;
- HDC parse rate: `13/15 = 0.8667`;
- HDC pass rate: `2/15 = 0.1333`;
- ACT coverage: `1/15 = 0.0667`;
- ACT precision: `0/1 = 0.0000`;
- wrong autonomous acts: `1/15`;
- Unsafe Autonomy Mass: `1/15 = 0.0667`.

Task-balanced archived-human endpoints on the same development tasks:

- human ONE_SHOT: `0.7842`;
- HDC-routed Human+Qwen3.5-9B ONE_SHOT: `0.7366`;
- human RETRY3: `0.8703`;
- HDC-routed Human+Qwen3.5-9B RETRY3: `0.8100`.

The runner's deterministic resume validator accepted all 15 rows against the current model alias, model label, prompt hashes, response-format hash, split hash, seed, temperature, participant target, and token limit. Qwen3.5-9B is `DEV_NONVIABLE` because production parse rate is below `0.80`, standalone accuracy is zero, and ACT coverage is below `2/15`.

Execution provenance:

- device/runtime: Apple M4 MacBook Air, 24 GB unified memory, Darwin arm64, Python `3.9.6`;
- llama.cpp build: `version 1 (9ee9a1c)`, AppleClang `17.0.0.17000013`, Darwin arm64;
- model file: `/Users/3obd/Library/Application Support/ai.atomicbot.hermes/llamacpp/models/qwen-3.5-9b/Qwen3.5-9B-Q4_K_M.gguf`;
- model SHA256: `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8`;
- server arguments: `-m <model-file> --port 8099 --ctx-size 8192 --parallel 1 --alias qwen35-9b --reasoning off --log-disable`;
- runner repository HEAD at inference: `257b0a4ffb2af919db7567651308e56c2153624d`;
- runner last-modifying commit: `1767fa4d90719cc46435c17281aec6453de0b1ec`;
- CogARC repository commit: `1a319935b803580fcbd6ff002195df86a7e90095`.

## Development model-selection result

The executable frozen selector returned `NO_ELIGIBLE_LLM_PAIR`.

- `gemma4-26b-a4b-q4km`: `EVAL_ELIGIBLE`;
- `qwen35-9b-q4km`: `DEV_NONVIABLE`;
- `qwen35-4b-q4km`: previously classified `DEV_NONVIABLE` and not supplied as an incomplete candidate summary.

The sole eligible model is Gemma. `WEAK_MODEL` and `STRONG_MODEL` therefore remain undefined, and selection did not inspect or use any team metric, Unsafe Autonomy Mass, ACT precision, Human Leverage, or desired inversion outcome.

## Local Gemma artefact audit

The archived 15-row local Gemma file reproduces the recorded standalone, HDC-pass, ACT, ACT-precision, and Unsafe-Autonomy-Mass endpoints, but re-summarizing those exact rows reports production parse `12/15 = 0.8000` and HDC parse `14/15 = 0.9333`, whereas the earlier controller status and development ledger state production parse `15/15 = 1.0000`.

No Gemma row was changed and no Gemma inference was repeated. For the executable selector, a separate selection-input summary was derived mechanically from the archived rows with `analysis.stage004_llm_hdc.summarize`. This discrepancy does not change Gemma's eligibility or the final selection verdict: `0.8000` meets the frozen production-parse threshold, while Qwen3.5-9B independently fails three eligibility criteria. Historical partial `-v2` artefacts were preserved and were not used for selection.

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

## Final development disposition

Stage 004 stops at `NO_ELIGIBLE_LLM_PAIR` under the frozen candidate pool and selection rule. Do **not** unlock, inspect, or query the 60-task evaluation split. The confirmatory lock remains `DRAFT_DO_NOT_EVALUATE`; creating a different candidate pool would require a new versioned protocol while preserving this negative development result.

## Publication boundary

Stage 004 is a falsifiable replication attempt. `NO_ELIGIBLE_LLM_PAIR`, `INCONCLUSIVE_*`, or `NO_REPLICATION` are valid scientific outcomes and must not trigger outcome-driven replacement of the frozen design.
