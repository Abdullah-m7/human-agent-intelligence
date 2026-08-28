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

## Source-data invariants

Before any receiver analysis, the archived human panel must satisfy:

1. exactly one analysis row per `person_id × trial`;
2. `human_first ∈ {0,1}` and `human_final ∈ {0,1}`;
3. `human_final >= human_first` on every row.

The third invariant is not imposed to make recovery positive. It follows from the behavioral meaning of the variables: a first-attempt success is necessarily an eventual success. Any violation is treated as a source/reconstruction anomaly and blocks analysis rather than being clipped or repaired silently.

## Cross-fitted, task-difficulty-adjusted receiver capability

For every evaluation task `t`, each participant's receiver-capability score must be estimated **without using that participant's outcome on t**.

A raw accuracy score is not sufficient as the primary measure because participants have unequal history coverage; a person who happened to retain easier tasks after source-study exclusions could receive an inflated score. The primary score therefore adjusts for the difficulty of the person's observed history.

For every non-target history row `(p,j)`, define the peer task-success rate excluding person `p`:

`PeerMean(-p,j) = mean_{k != p}(Y_kj)`.

The row residual is:

`Residual_pj = Y_pj - PeerMean(-p,j)`.

The primary receiver-capability score for target task `t` is:

`Capability_p(-t) = mean_{j != t}(Residual_pj)`

over that participant's available non-target first-attempt history.

Primary implementation:

1. take the official CogARC analysis sample;
2. exclude target task `t` entirely from capability construction;
3. compute peer-excluded task difficulty on the remaining history;
4. average person-specific residuals across their observed history;
5. require at least 30 non-target capability-estimation tasks for that participant;
6. rank eligible participants by this difficulty-adjusted leave-one-task-out score;
7. assign five ordered strata using average percentile ranks so exact ties are not broken by identifiers or held-out outcomes;
8. only then use the held-out human outcome on task `t` to estimate stratum-specific `H_first(q,t)` and `H_final(q,t)`.

Raw leave-one-task-out first-attempt accuracy is retained as a sensitivity descriptor, not the primary stratification variable.

The adjustment is intentionally simple and auditable. It is not labeled an IRT estimate. Rasch/IRT can be added as a sensitivity analysis if it is frozen before any prospective second-family receiver analysis.

## Measurement gate

Stage 002 already demonstrated that an unstable human-capability construct can invalidate an otherwise attractive Human–AI result. Paper 04 therefore requires a capability measurement gate before interpreting receiver gradients.

Using only the archived human panel, repeatedly split the ARC tasks into independent halves. Within each half, recompute the same peer-difficulty-adjusted capability score; require at least 12 observations in each half for a participant to enter that split.

Across 200 deterministic random task splits, report:

- mean split-half correlation;
- 5th, 50th and 95th percentile split-half correlations;
- mean Spearman–Brown corrected reliability;
- mean participants contributing per split.

Primary receiver-gradient interpretation requires both:

- mean Spearman–Brown reliability `>= 0.70`;
- 5th-percentile raw split-half correlation `>= 0.50`.

If either condition fails, verdict = **MEASUREMENT_HOLD**. Curves may still be reported diagnostically, but no strong receiver-capability gradient claim is made and raw accuracy is not substituted post hoc as a rescue measure.

## Common-task support gate

A second source of bias would arise if capability strata were evaluated on different subsets of ARC tasks. Because agent correctness and ACT behavior vary sharply by task, a slope across strata could otherwise be a task-composition artifact.

The primary analysis therefore uses a **common-support task panel**:

- each task must have at least 10 held-out human observations in **every one of the five capability strata**;
- only tasks meeting this rule in all five strata enter the primary receiver-gradient curves;
- the same agent rows and the same task set are used for every stratum;
- at least 30 common-support tasks are required for `SUPPORT_PASS`.

If fewer than 30 tasks survive, verdict = **PRIMARY_SUPPORT_HOLD**. Per-stratum available-case estimates may be reported only as robustness/descriptive results and cannot replace the matched primary panel.

The primary receiver analysis is ready only when both `MEASUREMENT_PASS` and `SUPPORT_PASS` hold.

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

How does `NetRoutingValue` change across independently measured receiver-capability strata for the **same** agent state and ACT/DEFER rule on the same matched task panel?

### RQ2 — Error displacement

Does higher receiver capability increase the team cost of wrong autonomous actions because those actions increasingly displace correct human judgments?

### RQ3 — Recovery capacity

How much human recovery potential is made unreachable by autonomous action, and how does that quantity change across agent states?

### RQ4 — Contract reversal

Are there agent states that improve on a ONE_SHOT receiver but fail to improve on a RETRY3 receiver, demonstrating that the same nominal `DEFER-to-human` endpoint changes value when the receiver's effort budget changes?

## Hypotheses

These are discovery hypotheses on the Stage-003 symbolic family until a second agent family clears the Stage-004 sealed evaluation.

**H1 — Receiver gradient.** For a fixed agent policy, NetRoutingValue decreases as cross-fitted, task-adjusted receiver capability rises.

**H2 — Displacement gradient.** HarmfulDisplacementMass increases with receiver capability more strongly than UnsafeAutonomyMass does, because the latter ignores what the human would have done.

**H3 — Recovery suppression.** Any policy with nonzero ACT mass on tasks with positive human recovery potential has positive RecoverySuppressionMass; increasing ACT coverage need not increase team value when it suppresses recovery on human-favorable tasks.

**H4 — Contract sensitivity.** At least one nontrivial agent state/policy has a materially different ranking or sign of NetRoutingValue under ONE_SHOT versus RETRY3 receiver contracts.

H3's first clause is algebraic and is not treated as an empirical discovery. The empirical question is the magnitude and task distribution of suppression.

## Primary estimands

For each agent state `m`, receiver stratum `q`, and receiver budget `b` on the common task panel:

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

1. whether the adjusted receiver measurement clears its reliability gate;
2. how many of 75 tasks clear five-stratum common support;
3. whether receiver gradients are monotonic across the solver ladder on that identical task set;
4. where ONE_SHOT and RETRY3 contract rankings diverge;
5. how much recovery potential is suppressed at each ACT coverage;
6. whether the 240→321 team inversion is explained more sharply by HarmfulDisplacementMass than by UnsafeAutonomyMass alone.

## Prospective second-family analysis

If Stage 004 produces two eligible LLM agent states and the sealed 60-task evaluation is valid, Paper 04 may use that evaluation as a **pre-specified secondary analysis** after Paper 01's primary verdict is computed.

Rules:

- Paper 04 cannot influence Stage-004 pair selection;
- it cannot alter the HDC gate or evaluation split;
- the primary Paper-01 ATPI verdict is computed first;
- receiver-stratum analysis uses the same agent rows, not new model queries;
- the same measurement and common-support gates apply;
- failure or no-pair in Stage 004 is retained as such and does not trigger a substitute model chosen from team outcomes.

If no second family becomes eligible, Paper 04 remains HOLD for strong general claims but the benchmark/recovery methodology may still be reported as a discovery or methods contribution.

## Statistical plan

Primary receiver-gradient summaries are task-balanced and matched on the common-support task set.

For each agent state:

- report five stratum-specific point estimates;
- estimate the linear slope of NetRoutingValue across ordered capability strata as a compact trend descriptor;
- estimate analogous slopes for HarmfulDisplacementMass and RecoverySuppressionMass;
- use paired task bootstrap intervals for between-contract and between-agent-state differences;
- report the full five-point curves so a linear slope cannot hide non-monotonicity;
- report participant support for every stratum/task and the number of tasks excluded by the common-support rule;
- report raw-accuracy stratification only as a frozen sensitivity analysis, not an outcome-driven rescue.

Participant-weighted analyses are robustness checks, not replacements for task-balanced primary estimates.

No outcome-driven task deletion is allowed. Measurement or support failure produces an explicit HOLD rather than a post-hoc alternative threshold.

## Novelty boundary

Prior art already includes:

- classic and modern Learning-to-Defer;
- expert-specific and population-adaptive deferral;
- human/model dependence in Bayes-optimal deferral;
- sequential L2D and costly human interventions.

The provisional contribution is therefore **not** “AI should know which human it is deferring to.”

The stronger empirical angle is:

> A human receiver is not a scalar endpoint. The value of DEFER depends on independently measured, task-adjusted receiver capability **and on recovery opportunity**, while autonomous ACT can make part of that recovery capacity unreachable.

A current targeted literature search did not surface a canonical L2D benchmark that measures multiple attempts by the *same real human receiver* and decomposes the recovery capacity suppressed by autonomous routing. This is a provisional gap, not a priority claim; it must be re-audited immediately before manuscript submission.

## Publication gate

**GO for Stage-003 discovery analysis only if the measurement and common-support gates pass.**

**HOLD for cross-architecture general claims** until either:

1. a second agent family yields valid prospective receiver-contract results under the same frozen gates; or
2. another independent executable agent family is evaluated under a separately locked protocol.
