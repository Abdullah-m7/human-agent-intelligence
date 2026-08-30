# Stage 005 CogARC Confirmatory Lock V1

BEGIN_STAGE005_COGARC_LOCK_FIELDS
LOCK_STATUS: DRAFT_DO_NOT_RUN
CONTRACT_COMMIT: PENDING_COMMIT_A
CALIBRATION_HEAD: 0dc1a1678f512f6ed49033551bf55dcff62739c3
CALIBRATION_CONTRACT_COMMIT: fa9f83c12b8c070e4799636f68ce35ab21118e33
MODEL: Gemma-4-26B-A4B Q4_K_M
MODEL_API_NAME: gemma4-26b-a4b
MODEL_LABEL: gemma4-26b-a4b-q4km
MODEL_SHA256: b8707e57f676d8dd1b80f623b45200cc92e6966b0e95275e606f412095a49fde
SYSTEM_PROMPT_SHA256: 1809bdbd08cc62cd29e04c616b6b902c2632cb35e2d74fe374a7a09df42b6cb6
USER_TEMPLATE_SHA256: de6ca3e6128c588ed92dedaa13fba7fea436aa2e26623572bf686948350f4312
RESPONSE_CONTRACT_SHA256: 73037b22da38f0d83e23fd580dea62dc648ee6e85b2794a7fecb124c00fa6472
SANDBOX_CONTRACT_SHA256: e9fb61d36ca818dedf06625a9e31b980350f77a0c85fa718fbccd8808c0dfcef
RANKING_ACT_CONTRACT_SHA256: b673da1d3b60648ee4a17f9bc34a727fa2f4e74ac14ea55e168733aa94959497
TEMPERATURE: 0.8
TOP_P: 0.95
MAX_TOKENS: 1536
BASE_SEED: 505000
CANDIDATE_SEQUENCE: 1,2,3,4,5,6,7,8
LOW_BUDGET: 1
HIGH_BUDGET: 8
CTX_SIZE: 16384
LLAMA_CPP_BUILD: llama.cpp version 1 (9ee9a1c); AppleClang 17.0.0.17000013; Darwin arm64
SERVER_ARGS_SHA256: f1c7942111acce9d18c5071616ba0f1940bb10755d75cca11f6aa4457fa20450
COGARC_SOURCE_COMMIT: 1a319935b803580fcbd6ff002195df86a7e90095
COGARC_EVAL_IDS_COUNT: 60
COGARC_EVAL_IDS_SHA256: b35e99df60502ced57010e2774ceeef515692fbf1cebba1caef6c1301e1bab49
TARGET_INDEX: 0
PRIMARY_RECEIVER: ONE_SHOT
PRIMARY_WEIGHTING: TASK_BALANCED
ROBUSTNESS_RECEIVERS: PARTICIPANT_WEIGHTED_ONE_SHOT,TASK_BALANCED_RETRY3,PARTICIPANT_WEIGHTED_RETRY3
BOOTSTRAP_RESAMPLES: 10000
BOOTSTRAP_LABEL: stage005-cogarc-task-bootstrap-v1
BOOTSTRAP_SEED: 14569489926424524350
HUMAN_LEVERAGE_SPLITS: 300
HUMAN_LEVERAGE_TASKS_PER_HALF: 30
HUMAN_LEVERAGE_MIN_CAPABILITY_TRIALS: 20
HUMAN_LEVERAGE_MIN_EVALUATION_TRIALS: 20
END_STAGE005_COGARC_LOCK_FIELDS

## Scientific question and frozen agent

This lock tests whether increasing synthesis compute from the already-selected
B1 prefix to the B8 prefix improves autonomous decisions or merely expands the
boundary of tasks the agent takes over. The pair was selected mechanically on
calibration before any CogARC confirmatory outcome was observed. It must not be
reselected.

The model, prompt bytes, response contract, sandbox, sampling parameters,
candidate seeds, ranking, and ACT rule are those used in calibration. B1 is
candidate 1. B8 is candidates 1 through 8. Only valid candidates are ranked;
visible-training exact fit is maximized and ties go to the earliest candidate.
ACT occurs exactly when the selected candidate has visible-training exact fit
1.0. Otherwise the system defers. A missing valid prediction is standalone
wrong. Agreement, voting, complexity, later-candidate preference, confidence,
and human-aware routing are forbidden.

The approved calibration background is fixed rather than re-analyzed for pair
selection: B1 standalone 11/60, ACT 10/60, ACT precision 9/10, UAM 1/60; B8
standalone 25/60, ACT 26/60, ACT precision 25/26, UAM 1/60. The 16 calibration
DEFER-to-ACT transitions were correct, 22 tasks had multiple certified
programs, and 3 of those 22 disagreed on target prediction. These observations
do not modify routing.

## Confirmatory data firewall and endpoint

The confirmatory set is exactly `evaluation_tasks` in
`benchmarks/capability_twin/stage004_split.json`: 60 unique IDs. The 15
development IDs are forbidden. Lock construction may inspect the IDs and their
canonical list hash only. It must not open any task JSON, target grid, agent
outcome, or human task outcome.

Future execution is all 60 tasks, never a limit, manual subset, outcome-based
skip, or alternative ordering. Crash recovery is permitted only by deterministic
resume after every existing candidate row matches the complete lock provenance.
The endpoint is the participant-visible `test[0]`: visible training input/output
pairs plus `test[0].input`. `test[0].output` is never serialized into a model
request. Additional test queries do not change the endpoint.

## Human receiver and joint outcome

The human source is CogARC Experiment 2 at the recorded source commit, using the
official `Behavioral data/trial_inclusion.csv` rows with the Stage003 inclusion
definition. ONE_SHOT is the first-attempt outcome and RETRY3 is the final,
retry-enabled outcome. The primary receiver is ONE_SHOT with task-balanced
weighting:

`H_first(t) = mean first-attempt success among included archived humans on t`

`J_b(t) = AgentCorrect_b(t)` when budget b ACTs, and `H_first(t)` when it defers.

`J_b` is the mean over the 60 tasks. The primary contrast is
`DeltaJ = J_B8 - J_B1`; a negative value means the higher-compute Human+Agent
system was weaker. Participant-weighted ONE_SHOT, task-balanced RETRY3, and
participant-weighted RETRY3 are robustness results and cannot alter the primary
verdict.

## Frozen verdict tree

The primary strict result is `INCONCLUSIVE_CAPABILITY_ORDER` if standalone B8
does not exceed standalone B1; labels are never swapped. Conditional on the
capability order, it is `INCONCLUSIVE_LOW_AUTONOMY_COVERAGE` if either budget
ACTs on fewer than 6 of 60 tasks. Otherwise `STRICT_ATPI_REPLICATION` requires
all four conditions:

1. standalone accuracy B8 > B1;
2. ACT coverage B8 > B1;
3. unsafe autonomy mass B8 > B1; and
4. task-balanced ONE_SHOT joint performance B8 < B1.

If the capability order and coverage floor hold but all strict conditions do
not, the result is `NO_STRICT_ATPI_REPLICATION`. Separately,
`AUTONOMY_TEAM_INVERSION` may be recorded descriptively when capability and ACT
coverage rise while primary joint performance falls, even without rising UAM.
It cannot overwrite or substitute for the strict verdict. Statistical
significance is not a verdict condition.

## Autonomy displacement and uncertainty

Nested candidates and earliest-train-perfect ranking imply `ACT_B1` is a subset
of `ACT_B8`. Let `N` contain tasks that change from B1 DEFER to B8 ACT. The
pre-specified marginal quantities are N, correct count, precision, error rate,
Wilson 95% precision interval, mean ONE_SHOT human performance on N, and:

`MarginalAgentAdvantage = mean_N(AgentCorrect_B8(t) - H_first(t))`

`AutonomyDisplacementTerm = (1/60) * sum_N(AgentCorrect_B8(t) - H_first(t))`

The routing identity `DeltaJ == AutonomyDisplacementTerm` must hold within
absolute tolerance 1e-12. This is exact routing accounting, not a causal proof.
The primary DeltaJ interval is a paired task percentile bootstrap with 10,000
resamples. Its integer seed is the unsigned big-endian value of the first eight
bytes of `SHA256("stage005-cogarc-task-bootstrap-v1")`, frozen above. Standalone changes
also receive a paired gain/loss table and a descriptive exact discordant
McNemar/binomial statistic. ACT and UAM are reported as counts, rates, and
differences.

## Secondary analyses

Human Leverage reuses the Stage003 ARC task-capability construct; it is not IQ.
It uses 300 deterministic task-level cross-fits, adapted before execution from
the Stage003 75-task 37/38 split to the required 60-task 30/30 split. Capability
is estimated on one half and joint/leverage outcomes on the other. Included
participants need at least 20 capability-estimation and 20 evaluation trials.
Slopes/associations at B1 and B8 and their paired difference are secondary and
cannot affect the strict verdict. If this definition is not estimable it is
reported as secondary unavailable, not replaced by a new construct.

After execution only, program-ambiguity diagnostics report tasks with any and
multiple certified programs, prediction disagreement, unique certified target
predictions, and unanimous-wrong multiple-certified cases. They are descriptive
and cannot affect candidate ranking, ACT, routing, pair choice, or verdict.

Commit A freezes all executable code and this document in draft form. Commit B
may replace only the pending contract SHA and draft status in this file. No
CogARC execution is authorized until an independent Controller reviews Commit B.
