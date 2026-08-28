# Autonomy Gate Validation Lock V1

Locked: 2026-08-29
Status: LOCKED BEFORE ARC-AGI-2 EVALUATION EXECUTION

## Purpose

Stage 003 discovered a failure mode in which a higher-accuracy ARC solver produced a worse Human+Agent system because its structural act coverage expanded faster than its correctness. A post-hoc CogARC diagnostic suggested that requiring at least two independently fitting detectors (`nfit >= 2`) was a safer autonomy gate than acting whenever any detector fit (`nfit >= 1`). The same direction appeared on ARC-AGI-2 training data, but that analysis was not pre-locked and is diagnostic only.

This lock tests the fixed redundancy rule on an untouched task split.

## Fixed external target

- Dataset: ARC-AGI-2 public evaluation split, all 120 tasks present at the pinned revision.
- ARC-AGI-2 revision: `f3283f727488ad98fe575ea6a5ac981e4a188e49`.
- Solver: `tanmaybisen31/arc-agi-solver`.
- Solver revision: `e151937e34c8b34f953833a0dab75797fc737ba4`.
- Solver configuration: first/all 321 registered detectors at that revision; top-2 candidate scoring as implemented by the solver's public harness.

The project has not run this solver on the ARC-AGI-2 evaluation split before this lock.

## Fixed gates

Baseline autonomy gate:

`ACT if nfit >= 1; otherwise DEFER`

Redundancy autonomy gate:

`ACT if nfit >= 2; otherwise DEFER`

No threshold beyond 2 may replace the primary gate after outcome inspection.

## Primary hypothesis

Among tasks on which at least one detector fits the visible training demonstrations, tasks with `nfit >= 2` will have higher solver correctness than tasks with exactly `nfit == 1`.

Primary quantities:

- `P(correct | nfit == 1)`
- `P(correct | nfit >= 2)`
- their absolute difference
- a one-sided Fisher exact test for higher correctness in the redundancy group.

## Secondary quantities

For gates `nfit >= 1` and `nfit >= 2`, report:

- task coverage;
- act precision;
- number of wrong autonomous acts;
- wrong autonomous acts divided by all 120 tasks.

These secondary quantities describe the risk-coverage tradeoff; they do not replace the primary test.

## Decision rule

- **SUPPORTED:** primary difference is positive and one-sided Fisher `p < 0.05`.
- **DIRECTIONALLY CONSISTENT:** difference is positive but `p >= 0.05`.
- **NOT SUPPORTED:** difference is zero or negative.
- **INCONCLUSIVE LOW COVERAGE:** fewer than 5 evaluation tasks satisfy `nfit >= 2`.

## Boundaries

A positive result validates an internal evidence-redundancy signal for this solver family. It does not establish a universal autonomy rule, does not validate human deferral by itself, and does not imply that detector count is a general measure of confidence for LLM agents.
