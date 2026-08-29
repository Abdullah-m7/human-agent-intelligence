# Stage 004 Development Artefacts

The 60-task evaluation split was not queried. Every row in this directory has `phase = dev`.

## Selection inputs and outputs

- `dev_gemma4-26b-a4b-q4km_selection_summary.json` is a no-inference re-summary of the archived 15-row Gemma file using `analysis.stage004_llm_hdc.summarize`. It supplies the HDC parse rate required by the frozen selector.
- `dev_qwen35-9b-q4km_summary.json` is the runner-generated 15-task Qwen3.5-9B development summary.
- `stage004_model_selection.json` is the output of `analysis/stage004_model_selection.py` on those two summaries. It returns `NO_ELIGIBLE_LLM_PAIR`.
- Qwen3.5-4B was already classified `DEV_NONVIABLE` after six tasks and its incomplete rows were not passed to the selector.

## Primary Qwen3.5-9B artefacts

- `dev_qwen35-9b-q4km_rows.jsonl`: 15 validated development rows.
- `dev_qwen35-9b-q4km_summary.json`: runner summary.
- `dev_qwen35-9b-q4km_joint.json`: archived-human Human+Agent metrics.

## Preserved historical files

The Gemma and Qwen3.5-4B files predate the Qwen3.5-9B recovery in this commit. Files carrying `-v2` are preserved local historical/partial artefacts and were not used for model selection. They are retained rather than deleted or silently merged.

The archived Gemma rows and earlier narrative record disagree on production parse rate; see `reports/STAGE_004_CONTROLLER_STATUS.md` and `reports/STAGE_004_DEV_LEDGER_V1.md`. The discrepancy does not change Gemma eligibility or the selection verdict.
