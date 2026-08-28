# Paper 03 Protocol V1 — The Capability Measurement Trap

Date: 2026-08-29

## Working title

**How Many Decisions Does It Take to Measure a Human? Reliability Limits in Human–AI Augmentation Research**

Alternative:

**The Capability Measurement Trap: When Noisy Human Baselines Distort AI-Augmentation Heterogeneity**

## Motivation

Many Human–AI studies ask whether AI helps lower-skill, novice, or weaker-baseline users more than stronger users. That question is only interpretable if the human baseline itself is measured with enough reliability to behave like a stable effect modifier rather than task noise.

This program was motivated by an internal failed replication, not by a desire to rescue it:

- in the Stage-002 CSCW validation, capability estimated from roughly 9–10 non-target decisions had extremely poor split-half reliability and failed to predict a held-out human decision;
- HAIID offered a moderately stronger, longer baseline panel;
- CogARC provides a much denser person × item matrix and Stage 003 showed high raw split-half reliability.

The paper turns that contrast into a methods question instead of treating measurement failure as nuisance.

## Claim boundary

This paper does **not** claim novelty for:

- classical attenuation from measurement error;
- regression to the mean;
- mathematical coupling between a baseline score and a change score;
- psychometric reliability or Item Response Theory;
- measurement-error problems in heterogeneous treatment-effect estimation.

General causal/psychometric literature already establishes those phenomena. In particular, item-level HTE/IRT work shows that noisy latent outcomes can distort interaction estimates and that measurement error matters for heterogeneous treatment-effect inference.

The target contribution is Human–AI-specific and empirical:

> quantify how much human behavioral evidence is required before a baseline-capability moderator becomes stable enough for claims such as “AI benefits weaker users more,” and show how the apparent augmentation gradient changes when capability estimation and AI-benefit estimation are forced onto disjoint evidence.

## No-new-human design

No participants are recruited.

Primary sources are archived/open human behavior already used or identified by the research program:

1. **CogARC** — dense abstract-reasoning person × item panel;
2. **HAIID** — repeated pre-advice human judgments plus AI advice and final judgments;
3. **CSCW 2023 loan-decision data** — short baseline panel that failed Stage-002 capability validation.

Datasets enter only when their provenance, license, reconstruction rules, and participant/task identifiers are auditable.

## Core constructs

### Human capability estimate

`C_hat_p(m)` = capability estimate for person `p` built from exactly `m` independent baseline items or as close as the dataset permits under a fixed sampling rule.

### Held-out capability criterion

`C_holdout_p` = task-difficulty-adjusted human performance estimated from items not used in `C_hat_p(m)`.

### Measurement budget

`m` = number of baseline decisions used to characterize a human.

Candidate primary grid for dense panels:

`m ∈ {3, 5, 8, 10, 15, 20, 30, 40, 60}`

Values not supported by a dataset are omitted rather than extrapolated.

## Primary measurement-budget experiment

CogARC is the calibration panel because it is dense enough to simulate short studies without inventing responses.

For each deterministic random split and each measurement budget `m`:

1. select `m` common ARC items as the measurement set;
2. select a disjoint criterion set from remaining items;
3. require a predeclared minimum response coverage on both sets;
4. estimate task-difficulty-adjusted capability on the measurement set;
5. estimate the same construct independently on the criterion set;
6. compute measurement reliability and ranking stability.

Primary outputs by `m`:

- Pearson and Spearman correlation with held-out capability;
- Spearman–Brown reliability where meaningful;
- rank correlation;
- quintile classification agreement;
- top-vs-bottom quintile contamination rate;
- probability a person's estimated direction relative to median is wrong;
- effective number of participants retained after coverage rules.

At least 500 deterministic task resamples are used for the primary curve unless computational diagnostics show convergence earlier; the final count is frozen before inspecting any augmentation-gradient outcome.

## The gain-coupling trap

A common descriptive quantity is:

`Gain = AssistedPerformance - BaselinePerformance`.

Regressing `Gain` on the *same noisy baseline estimate* mechanically reuses baseline error with a negative sign and can create an apparent “lower baseline → larger gain” relationship even when true treatment heterogeneity is absent.

The paper therefore distinguishes:

### Naive estimator

`Gain_same = Assisted - Baseline_same`

and tests its association with `Baseline_same`.

### Cross-fitted estimator

Human capability is estimated on one item subset, while AI gain is estimated on disjoint items/interactions:

`Capability_A ⟂ evidence used in Gain_B`.

The difference between naive and cross-fitted augmentation gradients is a primary diagnostic, not a robustness afterthought.

## Dataset-specific analyses

### CogARC — measurement calibration

No AI advice is needed for the first contribution. The dense human panel estimates how quickly human capability becomes rank-stable as `m` grows.

A secondary analysis may pair the same sampled humans with Stage-003 executable agent states to ask how measurement budget changes estimated Human Leverage gradients. Agent outcomes must remain task-disjoint from capability-estimation items.

### HAIID — augmentation-gradient sensitivity

Use initial human judgments as baseline capability evidence and AI-advice/final judgments as collaboration outcomes.

Primary rule:

- capability items and AI-gain items are disjoint by construction;
- participant must meet a frozen minimum count in each side;
- repeat random splits to estimate the distribution of the capability→AI-gain coefficient as measurement budget changes.

Compare against the naive same-items baseline/gain association, explicitly demonstrating mathematical coupling rather than interpreting it as psychology.

### CSCW — short-panel negative control

Do not treat the Stage-002 failed validation as positive evidence. Use it as a negative-control case:

- quantify the attainable reliability under its 10-item design;
- test held-out predictive validity;
- show whether any capability-stratified AI effect is too measurement-limited to support a strong interpretation.

The conclusion may be that the dataset is insufficient for this moderator question; that is an acceptable result.

## Measurement adequacy gate

The paper does not propose one universal item-count threshold across all domains. Item difficulty/discrimination and response density matter.

Instead define an empirical **Capability Measurement Adequacy** gate for a given dataset/design. A candidate capability moderator is considered adequate for primary heterogeneity interpretation only if all frozen criteria pass, initially:

1. mean held-out rank correlation `>= 0.70`;
2. 5th-percentile held-out rank correlation `>= 0.50` across resamples;
3. median quintile agreement `>= 0.60`;
4. held-out predictive validity is positive and materially above zero;
5. the same participant outcome is never used both to construct the capability predictor and the collaboration/gain response.

Thresholds are methodological working criteria, not psychometric universal laws. Sensitivity to reasonable thresholds is reported.

## Primary research questions

### RQ1 — Measurement budget

How does the reliability and rank stability of behavioral human-capability estimates change with the number of independent baseline decisions?

### RQ2 — Apparent augmentation heterogeneity

How much of the observed relationship between baseline capability and AI gain changes when capability and gain are estimated from disjoint evidence?

### RQ3 — Design sufficiency

Which existing Human–AI datasets contain enough repeated human behavior to support capability-moderated augmentation claims, and which do not?

### RQ4 — Downstream instability

How much do receiver rankings, capability quintiles, and estimated Human–AI interaction gradients change solely because the baseline measurement budget changes?

## Hypotheses

**H1 — Budget–reliability curve.** Held-out capability reliability and rank stability increase with measurement budget, with strong diminishing returns rather than a universal linear rule.

**H2 — Quintile instability at short budgets.** Short baseline panels produce materially higher capability-stratum misclassification than dense panels.

**H3 — Coupling inflation.** Same-item baseline-versus-gain analyses produce more negative augmentation gradients than cross-fitted analyses when baseline measurement error is nontrivial.

**H4 — Dataset sufficiency heterogeneity.** Some published/open Human–AI datasets are structurally unable to support fine-grained capability-moderator claims despite being adequate for average treatment effects.

## Statistical plan

- deterministic task/item resampling with frozen seeds;
- participant-level clustering where outcomes are repeated;
- task-balanced primary summaries where item difficulty is central;
- bootstrap intervals over tasks and participants as appropriate;
- full measurement-budget curves rather than one chosen `m`;
- cross-fitting for all primary capability→AI-outcome associations;
- no outcome-driven selection of the “best” measurement budget;
- no calling task-specific ability IQ.

## Novelty boundary from current search

A current targeted search found:

- extensive psychometric work on Human–AI collaboration scales;
- general literature on measurement error in heterogeneous treatment effects;
- IRT approaches to item-level treatment-effect heterogeneity;
- many AI experiments that stratify or test heterogeneity by baseline skill.

It did **not** surface a paper whose central empirical object is a **behavioral baseline-item budget curve for Human–AI augmentation heterogeneity**, with direct comparison of same-item versus cross-fitted capability/gain estimates across multiple open Human–AI datasets.

This remains a provisional gap and must be re-audited before submission.

## Publication gate

**GO for methods/discovery implementation.**

Strong claims require:

1. exact reproducibility of the source panels;
2. at least one dense dataset where the measurement-budget curve is identifiable;
3. at least one Human–AI advice/augmentation dataset where naive and cross-fitted estimators can both be computed;
4. explicit preservation of negative cases such as CSCW if their capability construct remains unreliable.
