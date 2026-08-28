# Stage 002 — Validation V1: Capability-Dependent Susceptibility

Date: 2026-08-28

## Controller decision

**VALIDATION RESULT: TWO-SIDED SUSCEPTIBILITY NOT SUPPORTED**

This is a valid failed replication of the Stage-001 HAIID discovery pattern. The failure is retained as evidence and must not be reclassified using secondary analyses.

## Audit trail

1. `a51913e` — hypotheses, constructs, models, exclusions, multiplicity rule, robustness checks, and failure conditions locked before focal raw-data inspection.
2. `811d375` — executable primary analysis committed before calculation of any focal coefficient.
3. `512a573` — pre-specified robustness analyses implemented before those robustness results were calculated.

Validation dataset: He, Buijsman & Gadiraju (CSCW 2023), DOI `10.1145/3610067`; open data DOI `10.4121/F211863D-331B-44E5-A184-C21A18AC831A`.

## Reconstructed sample

The released data allow complete reconstruction of pre-advice decision, AI advice, post-advice decision, and ground truth.

- participants: 281
- main-study trials: 2,810 (10 per participant)
- conditions: system 87; accuracy 92; analogy 102
- initial-disagreement trials: 1,465
- helpful disagreement trials (AI correct): 1,118
- harmful disagreement trials (AI wrong): 347
- participants represented in helpful disagreements: 281
- participants represented in harmful disagreements: 227

The authors' exclusion procedure reproduced exactly 281 valid participants. No new outcome-dependent exclusion was introduced.

## Primary locked results

Estimator: binomial-logit GLM with participant-clustered robust standard errors. No instability/separation warning triggered the pre-specified GEE fallback.

### H1 — helpful susceptibility

Among initial disagreements where AI advice was correct:

- capability coefficient: `+0.064667`
- SE: `0.070603`
- 95% CI: `[-0.073712, +0.203046]`
- two-sided p: `0.359708`

The point estimate is **positive**, opposite the registered prediction that higher task capability would reduce switching to correct AI advice.

### H2 — harmful susceptibility

Among initial disagreements where AI advice was wrong:

- capability coefficient: `-0.008003`
- SE: `0.126922`
- 95% CI: `[-0.256766, +0.240760]`
- two-sided p: `0.949722`

The point estimate has the registered sign but is approximately zero and highly uncertain.

### M3 — selectivity

Pooled disagreement model:

- capability main effect: `+0.048216`, p `0.675811`
- capability × AI-correct interaction: `-0.007933`, p `0.947697`

Marginal predicted switching increased slightly with capability for both correct and incorrect AI advice; there is no evidence here for capability-dependent discrimination between good and bad advice.

## Registered decision rule

Strict confirmatory support required both co-primary coefficients to be negative and each two-sided p-value `< 0.025`.

Observed:

- H1 negative? **No**
- H2 negative? **Yes, approximately zero**
- both p < 0.025? **No**

Therefore the locked classification is:

**TWO_SIDED_SUSCEPTIBILITY_NOT_SUPPORTED**

## Pre-specified robustness diagnostics

None of these analyses may rescue the failed primary validation.

### Alternative capability scaling

Unstandardized LOTO and the mathematically coupled all-10-trial capability score preserve the primary pattern: helpful coefficient positive; harmful coefficient approximately zero.

### Subjective numeracy

Adding subjective numeracy does not materially change the capability estimates:

- helpful capability: `+0.052084`, p `0.464764`
- harmful capability: `-0.008872`, p `0.943762`

Subjective numeracy itself is not treated as IQ.

### Condition-stratified estimates

Helpful / harmful capability coefficients:

- system: `-0.0317 / -0.2571`
- accuracy: `+0.1008 / +0.0706`
- analogy: `+0.1009 / +0.0779`

This heterogeneity is secondary. It cannot change the primary verdict, but it suggests that presentation of system accuracy/analogies may interact with capability and should be treated as a future hypothesis rather than mined here.

### Leave-one-item-out

Helpful H1 is particularly stable in sign:

- 10/10 omitted-item fits remained positive
- coefficient range: `[+0.0259, +0.1213]`

Harmful H2 is unstable around zero:

- 7/10 omitted-item fits negative
- 3/10 positive
- coefficient range: `[-0.0406, +0.0222]`

Therefore the H1 reversal is not driven by one loan case; H2 supplies little stable directional evidence.

### Participant bootstrap

1,000 participant-resampling replicates:

- helpful: median `+0.0653`; 95% percentile interval `[-0.0734, +0.1974]`; only 18.8% negative
- harmful: median `-0.0024`; 95% percentile interval `[-0.2900, +0.2471]`; 50.8% negative

The bootstrap reinforces the primary interpretation.

## Scientific interpretation

Stage 001 established a discovery association in HAIID: higher cross-fitted task capability was associated with less helpful and less harmful AI susceptibility. CSCW Validation V1 shows that this pattern is **not portable as a generic task-capability law**.

The correct update is therefore not to search for a favorable transformation. Instead:

1. downgrade `capability-dependent general susceptibility` from candidate general mechanism to **context-dependent discovery**;
2. retain the HAIID result as one empirical regime, not a universal relation;
3. treat communication policy / interface framing as a plausible moderator because the system-only stratum differs directionally from the two accuracy-framing strata, but label this observation exploratory;
4. investigate measurement reliability and design differences between HAIID and CSCW as diagnostics before selecting a second independent validation dataset;
5. keep the broader research program alive: the failed susceptibility replication does not test the Paper-01 Agentic Bottleneck / Role Migration hypothesis.

## What this does not say

This failed replication does not establish that capability never affects AI use, that all people rely on AI equally, or that HAIID was invalid. It establishes only that the pre-registered two-sided susceptibility pattern did not replicate in this independent loan decision-support dataset.

It also says nothing about IQ. `Capability_LOTO` is task-specific unaided accuracy.

## Next scientific gate

Before another validation attempt, perform a clearly labeled post-validation diagnostic comparing measurement reliability and experimental structure across HAIID and CSCW. A new independent dataset may be used only after a revised hypothesis is explicitly locked in a new validation protocol.
