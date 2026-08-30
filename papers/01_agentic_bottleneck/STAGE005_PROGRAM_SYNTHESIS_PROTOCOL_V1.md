# Stage 005 — Verifier-Bounded Program Synthesis Protocol V1

Status: frozen by the contract commit recorded in the Stage 005 results provenance. This protocol governs the calibration run only. CogARC is out of scope and remains sealed.

## Question and endpoint

Stage 005 varies inference-time search compute within one fixed program-synthesis agent. It measures capability, verifier-bounded autonomy, unsafe autonomy, and the quality of newly autonomous cases. Calibration is agent-only and cannot establish ATPI or Human+Agent performance.

The agent receives every visible ARC training input/output pair plus `test[0].input`. It never receives `test[0].output`. Gemma-4-26B-A4B Q4_K_M generates `def solve(grid): ...`; hidden output is used only after inference for scoring.

## Data separation

The source is official ARC-AGI-1 `data/training` at commit `399030444e0ab0cc8b4e199870fb20b863846f34`. All 75 task IDs used by the CogARC human panel are an IDs-only blacklist. Eligible IDs are sorted by `SHA256(task_id)` with `task_id` as tie-breaker. The first 20 are engineering; the next 60 are calibration. The lists and source IDs are frozen in `benchmarks/capability_twin/stage005_split.json`.

Engineering may inform prompt and operational settings. After the contract commit and before the first calibration request, the model, prompts, response parser, sandbox policy, sampling, budgets, ranking, and ACT rule are immutable. A genuine implementation bug discovered during calibration invalidates that calibration run; it must be restarted in full under a new contract commit.

## Fixed synthesis contract

- Model: the locally archived Gemma-4-26B-A4B Q4_K_M file identified by SHA256 in machine-readable provenance.
- One system prompt and one user template for every candidate.
- Temperature `0.8`, top-p `0.95`, maximum completion `1536` tokens.
- Calibration llama.cpp context is `16384` tokens. A tokenizer-only audit found a maximum fixed calibration prompt of `11970` tokens; prompt plus the full completion cap is `13506`.
- Candidate index is one-based; seed is `505000 + candidate_index`.
- Candidate budgets are literal prefixes of one sequence: `B1=1`, `B2=2`, `B4=4`, `B8=8`.
- A raw Python response beginning with `def solve(grid):` is accepted; a single Python Markdown fence is tolerated by the parser. No semantic repair is performed.

Exact prompt hashes, response-contract hash, model hash, llama.cpp build identity, server arguments, source-data commit, split hash, and sandbox policy are recorded in each candidate row and the phase provenance.

The first calibration attempt under commit `b6ecbcbe9ca5e37f2ab42d9e4d14711789f4950d` was invalidated after 72 candidate rows because its `--ctx-size 8192` server rejected the next visible prompt before inference (`11970 > 8192`). Those rows are archived as invalidated and are forbidden from the replacement calibration. The replacement run starts at 0/480 under the superseding contract commit.

## Sandbox and candidate validity

Source must define only `solve(grid)` at top level and pass source-length, AST-size, forbidden-node, forbidden-name, call, and attribute checks. Imports, filesystem access, network/process access, `open`, dynamic import, `eval`, `exec`, reflection, and external state are unavailable. Execution uses an isolated Python interpreter, an empty temporary working directory, minimal builtins, resource limits, and a wall timeout. Each returned value must be a non-empty rectangular grid no larger than 30×30 containing integer colors 0–9. Parse failure, rejection, crash, timeout, or invalid output makes the candidate invalid.

## Ranking, prediction, and autonomy

For every valid candidate:

`visible_train_exact_fit = exact visible training outputs solved / visible training examples`.

Within a budget, select the valid candidate with the highest visible-training fit; ties go to the lowest candidate index. Hidden target correctness never enters ranking. If no valid candidate exists, standalone prediction is `INVALID` and is scored wrong. Otherwise standalone prediction is the selected program's target-input output.

`ACT = selected candidate has visible_train_exact_fit == 1.0`.

All other states are `DEFER`. Certification is behavioral consistency with visible demonstrations, not calibrated confidence.

## Calibration measures and selection rule

For each budget report standalone accuracy, ACT coverage, ACT precision, unsafe autonomy mass, certification yield, mean best visible fit, and valid-program rate. For B1→B2, B2→B4, and B4→B8 report changes in capability, ACT coverage, and unsafe autonomy mass plus the count and precision/error rate of DEFER→ACT cases. Also report agreement among all train-perfect candidate target predictions and descriptive selected-program source/AST/branch complexity.

A future CogARC run is viable only if at least one pair `B_low < B_high` has strictly greater standalone accuracy and ACT coverage at the higher budget, with both coverages at least `0.10`, on all 60 calibration tasks. Select the viable pair with greatest numeric budget separation, breaking ties by the lower `B_low`. Unsafe autonomy, marginal precision, desired inversion, and human outcomes are forbidden selection inputs. If no pair qualifies, the verdict is `NO_VIABLE_COMPUTE_LADDER` and CogARC remains sealed. If a pair qualifies, the maximum result of this stage is `READY_FOR_COGARC_CONTROLLER_LOCK`; no CogARC inference is authorized here.
