# Paper 04 Protocol V2 — Deferral Is a Contract, Not a Button

Date: 2026-08-29

## Working title

**Deferral Is a Contract, Not a Button: Receiver Capability, Recovery Capacity, and AI Autonomy**

Alternative:

**The Human Behind DEFER: Measuring Receiver Capability and Recovery in Human–Agent Systems**

## Scientific claim boundary

This paper does **not** claim that expert-specific deferral is new. Learning-to-Defer already compares model and expert capability, adapts to changing experts, and extends to expert populations. Sequential Learning-to-Defer also studies long-horizon deferral and intervention cost.

The narrower target is empirical and measurement-oriented:

1. treat the human receiver as a measured capability distribution rather than a single scalar expert;
2. distinguish **first-pass capability** from **recovery capability** using real repeated human attempts;
3. measure how a fixed ACT/DEFER policy changes value across receiver-capability strata;
4. quantify how autonomous action can suppress an otherwise available human recovery opportunity.

No construct is called IQ. CogARC provides task-specific abstract-reasoning behavior, not a general-intelligence instrument.

## Why this can be done without new participants

CogARC Experiment 2 contains a dense archived person × ARC-task panel and up to three submissions per participant/task. Under the source release's official inclusion metadata, the Stage-003 analysis sample contains 12,138 trials from 199 people over 75 tasks.

The same tasks can be executed by agent adapters. Therefore the study can compare archived human receiver states and executable agent states without recruiting new humans or generating synthetic human personas.

## Receiver contract

A deferral event is specified as a contract:

`DEFER(task, receiver_state, effort_budget)`

The first paper release uses two effort budgets:

- `ONE_SHOT`: receiver gets the first submitted answer only;
- `RETRY3`: receiver receives the experiment's full recovery opportunity, up to three submissions.

Later work may add time, cost, evidence transfer, or tool access. Those are out of scope for V2.

## Cross-fitted receiver capability

For every evaluation task `t`, each participant's receiver-capability score must be estimated **without using that participant's outcome on t**.

Primary implementation:

1. take the official CogARC analysis sample;
2. for task `t`, compute each participant's first-attempt accuracy on all other observed ARC tasks;
3. require at least 30 non-t capability-estimation tasks for that participant;
4. rank eligible participants by this leave-one-task-out first-pass score;
5. assign five approximately equal receiver-capability strata;
6. only then reveal/use the held-out human outcome on task `t` to estimate stratum-specific `H_first(q,t)` and `H_final(q,t)`.

This makes the human ability estimate task-disjoint from the outcome it is used to explain. A Rasch/IRT sensitivity analysis may be added, but raw cross-fitted first-attempt accuracy is the predeclared primary measure because its meaning is transparent and Stage 003 already established high split-half reliability in CogARC.

## Core accounting

For task-level human success probability `H`, agent correctness `C ∈ {0,1}`, and autonomous-action indicator `A ∈ {0,1}`:

`Joint = E[A*C + (1-A)*H]`

which is exactly:

`Joint = E[H] + BeneficialAutonomyMass - HarmfulDisplacementMass`

with:

`BeneficialAutonomyMass = E[A*C*(1-H)]`

`HarmfulDisplacementMass = E[A*(1-C)*H]`

and:

`NetRoutingValue = BeneficialAutonomyMass - HarmfulDisplacementMass = Joint - HumanBaseline`.

These are accounting identities, not claimed as new Bayes-optimal deferral theory.

Their purpose is diagnostic: a wrong autonomous action matters more to the Human+Agent system when it displaces a receiver who was likely to be correct on that task.

## Recovery accounting

Let:

`R(t) = H_final(t) - H_first(t)`

be the human recovery opportunity on task `t`.

Then:

`HumanRecoveryPotential = E[R]`

`JointRecoveryValue = E[(1-A)*R]`

`RecoverySuppressionMass = E[A*R]`

and therefore:

`HumanRecoveryPotential = JointRecoveryValue + RecoverySuppressionMass`.

When `HumanRecoveryPotential > 0`, define:

`RecoveryCaptureRatio = JointRecoveryValue / HumanRecoveryPotential`.

Interpretation: the ratio is the share of the receiver's empirically available recovery capacity that remains reachable under the agent's ACT/DEFER policy. `RecoverySuppressionMass` is descriptive opportunity displacement, not a causal effect estimate.

## Primary research questions

### RQ1 — Receiver conditionality

How does `NetRoutingValue` change across independently measured receiver-capability strata for the **same** agent state and ACT/DEFER rule?

### RQ2 — Error displacement

Does higher receiver capability increase the team cost of wrong autonomous actions because those actions increasingly displace correct human judgments?

### RQ3 — Recovery capacity

How much human recovery potential is made unreachable by autonomous action, and how does that quantity change across agent states?

### RQ4 — Contract reversal

Are there agent states that improve on a ONE_SHOT receiver but fail to improve on a RETRY3 receiver, demonstrating that the same nominal `DEFER-to-human` endpoint changes value when the receiver's effort budget changes?

## Hypotheses

These are discovery hypotheses on the Stage-003 symbolic family until a second agent family clears the Stage-004 sealed evaluation.

**H1 — Receiver gradient.** For a fixed agent policy, NetRoutingValue decreases as cross-fitted receiver capability rises.

**H2 — Displacement gradient.** HarmfulDisplacementMass increases with receiver capability more strongly than UnsafeAutonomyMass does, because the latter ignores what the human would have done.

**H3 — Recovery suppression.** Any policy with nonzero ACT mass on tasks with positive human recovery potential has positive RecoverySuppressionMass; increasing ACT coverage need not increase team value when it suppresses recovery on human-favorable tasks.

**H4 — Contract sensitivity.** At least one nontrivial agent state/policy has a materially different ranking or sign of NetRoutingValue under ONE_SHOT versus RETRY3 receiver contracts.

H3's first clause is algebraic and is not treated as an empirical discovery. The empirical question is the magnitude and task distribution of suppression.

## Primary estimands

For each agent state `m`, receiver quintile `q`, and receiver budget `b`:

- `HumanBaseline(m,q,b)`;
- `JointPerformance(m,q,b)`;
- `NetRoutingValue(m,q,b)`;
- `BeneficialAutonomyMass(m,q,b)`;
- `HarmfulDisplacementMass(m,q,b)`;
- `RecoverySuppressionMass(m,q)`;
- `RecoveryCaptureRatio(m,q)`.

Report agent-centric `UnsafeAutonomyMass = P(ACT ∧ wrong)` beside the receiver-relative quantities. Do not substitute one for the other.

## Stage-003 discovery analysis

The first empirical pass uses the already-completed symbolic ARC solver ladder:

`15, 40, 80, 120, 180, 240, 321 detectors`.

This is **discovery only** because the ladder and Stage-003 team inversion are already known.

The discovery pass should answer:

1. whether receiver gradients are monotonic across the solver ladder;
2. where ONE_SHOT and RETRY3 contract rankings diverge;
3. how much recovery potential is suppressed at each ACT coverage;
4. whether the 240→321 team inversion is explained more sharply by HarmfulDisplacementMass than by UnsafeAutonomyMass alone.

## Prospective second-family analysis

If Stage 004 produces two eligible LLM agent states and the sealed 60-task evaluation is valid, Paper 04 may use that evaluation as a **pre-specified secondary analysis** after Paper 01's primary verdict is computed.

Rules:

- Paper 04 cannot influence Stage-004 pair selection;
- it cannot alter the HDC gate or evaluation split;
- the primary Paper-01 ATPI verdict is computed first;
- receiver-stratum analysis uses the same agent rows, not new model queries;
- failure or no-pair in Stage 004 is retained as such and does not trigger a substitute model chosen from team outcomes.

If no second family becomes eligible, Paper 04 remains HOLD for strong general claims but the benchmark/recovery methodology may still be reported as a discovery or methods contribution.

## Statistical plan

Primary receiver-gradient summaries are task-balanced.

For each leave-one-task-out human-capability construction:

- report quintile-specific point estimates;
- estimate the linear slope of NetRoutingValue across ordered capability quintiles as a compact trend descriptor;
- use paired task bootstrap intervals for between-contract and between-agent-state differences;
- report the full five-point curve so a linear slope cannot hide non-monotonicity;
- report participant counts contributing to each quintile/task estimate.

Participant-weighted analyses are robustness checks, not replacements for task-balanced primary estimates.

No outcome-driven task deletion is allowed. If a capability quintile has too few human outcomes on a task for stable estimation, report the support deficiency and use a predeclared minimum-support rule before any second-family confirmatory analysis.

## Novelty boundary

Prior art already includes:

- classic and modern Learning-to-Defer;
- expert-specific and population-adaptive deferral;
- human/model dependence in Bayes-optimal deferral;
- sequential L2D and costly human interventions.

The provisional contribution is therefore **not** “AI should know which human it is deferring to.”

The stronger empirical angle is:

> A human receiver is not a scalar endpoint. The value of DEFER depends on independently measured receiver capability **and on recovery opportunity**, while autonomous ACT can make part of that recovery capacity unreachable.

A current targeted literature search did not surface a canonical L2D benchmark that measures multiple attempts by the *same real human receiver* and decomposes the recovery capacity suppressed by autonomous routing. This is a provisional gap, not a priority claim; it must be re-audited immediately before manuscript submission.

## Publication gate

**GO for Stage-003 discovery analysis.**

**HOLD for cross-architecture general claims** until either:

1. a second agent family yields valid prospective receiver-contract results; or
2. another independent executable agent family is evaluated under a separately locked protocol.
