# Validation Lock V1 — Capability-Dependent Susceptibility

Locked: 2026-08-28
Stage: 002
Status: **LOCKED BEFORE FOCAL RAW-DATA INSPECTION**

## 1. Validation dataset

Primary untouched validation target:

**He, G., Buijsman, S., & Gadiraju, U. (2023). _How Stated Accuracy of an AI System and Analogies to Explain Accuracy Affect Human Reliance on the System_. Proceedings of the ACM on Human-Computer Interaction, 7(CSCW2), Article 276. DOI: 10.1145/3610067.**

Open dataset DOI: `10.4121/F211863D-331B-44E5-A184-C21A18AC831A`.

Published design facts used to formulate this lock:

- main between-subjects study: `N = 281` after the authors' exclusions;
- loan default / approval decision task;
- two training examples followed by **10 trial cases**;
- participants make an initial decision, receive system advice, and make a final decision;
- the AI/system was designed around 75% stated accuracy and is correct in 7 of the 10 main-study cases;
- three conditions: system prediction only, stated accuracy, and stated accuracy + analogy;
- the publication explicitly defines appropriate reliance on initial-disagreement trials and distinguishes positive AI reliance from positive self-reliance.

The raw 4TU dataset has **not** been downloaded, opened, queried, summarized, or modeled for this project before this lock. We have read the publication and public dataset description, including the authors' aggregate published results. Those published results are prior knowledge, not our focal validation result.

## 2. Discovery result being validated

HAIID Stage-001 discovery suggested that independently measured human task capability is associated with **lower susceptibility to AI advice in both directions**:

- less uptake when AI advice is helpful;
- less harmful switching when AI advice is wrong;
- little evidence in that discovery dataset that capability primarily operates through improved selectivity between correct and incorrect advice.

The validation target is the directional two-sided-susceptibility pattern, not the exact HAIID correlation magnitude.

## 3. Construct definitions

### Human task capability

For participant `i` on trial `t`, capability is computed only from that participant's **other initial unaided decisions**:

\[
H_{i,-t}=\frac{1}{T_i-1}\sum_{k\ne t} CorrectInitial_{ik}.
\]

With 10 complete main-study trials, this is a leave-one-trial-out (LOTO) estimate based on the other 9 trials.

This is **task capability**, not IQ, intelligence, numeracy, education, or expertise.

### Disagreement trials

Primary models include only trials where the participant's initial decision differs from the AI advice. For a binary task with known ground truth:

- if AI advice is correct, initial human disagreement necessarily means the initial human decision is wrong;
- if AI advice is wrong, initial human disagreement necessarily means the initial human decision is correct.

### Helpful susceptibility

On initial-disagreement trials where AI advice is correct:

`HelpfulSwitch = 1` if the final decision switches to the correct AI advice, else `0`.

### Harmful susceptibility

On initial-disagreement trials where AI advice is wrong:

`HarmfulSwitch = 1` if the final decision switches to the wrong AI advice, else `0`.

### Selectivity

Selectivity is the contrast between switching toward correct versus incorrect AI advice. It is analyzed through the `Capability × AI_correct` interaction and predicted-probability contrasts. We will not interpret generic advice resistance as verification skill.

## 4. Primary hypotheses

### H1 — Helpful susceptibility

Among initial-disagreement trials where AI advice is correct, higher LOTO task capability predicts a **lower probability of switching to AI**.

Directional expectation:

\[
\beta_{Capability,\;AIcorrect}<0.
\]

### H2 — Harmful susceptibility

Among initial-disagreement trials where AI advice is wrong, higher LOTO task capability predicts a **lower probability of switching to AI**.

Directional expectation:

\[
\beta_{Capability,\;AIwrong}<0.
\]

The substantive replication criterion for the Stage-001 susceptibility hypothesis is that both H1 and H2 have negative point estimates. Inferential strength is reported separately; a non-significant estimate is not converted into evidence of absence.

## 5. Secondary validation question — selectivity

Fit a pooled disagreement-trial model including `Capability × AI_correct`.

The HAIID discovery pattern suggests that capability may alter general susceptibility more strongly than it alters discrimination. However, **no confirmatory null hypothesis is registered for the interaction**. We will report its estimate, uncertainty, and marginal predicted switch probabilities rather than treating `p > .05` as evidence that selectivity is identical across capability levels.

## 6. Statistical models

### M1 — Correct-AI disagreement trials

Binary logistic model:

`SwitchToAI ~ z(Capability_LOTO) + C(condition) + C(item)`

Target: coefficient on `z(Capability_LOTO)`.

### M2 — Wrong-AI disagreement trials

Binary logistic model:

`SwitchToAI ~ z(Capability_LOTO) + C(condition) + C(item)`

Target: coefficient on `z(Capability_LOTO)`.

### M3 — Pooled selectivity model

`SwitchToAI ~ z(Capability_LOTO) * AI_correct + C(condition) + C(item)`

Targets:

- capability main effect;
- `Capability × AI_correct` interaction;
- marginal switch probabilities at capability `z = -1, 0, +1` separately for correct and incorrect AI advice.

### Uncertainty

Use participant-clustered robust standard errors. If the analysis-ready data structure or separation makes ordinary logistic estimation unstable, use a pre-specified GEE binomial/logit model clustered by participant. The estimator change must be documented and applied to all corresponding models, not selected based on the focal coefficient.

## 7. Multiplicity and decision rule

H1 and H2 are the two co-primary directional tests.

- Report two-sided 95% confidence intervals and p-values for transparency.
- For a strict family-wise confirmatory label, require each co-primary coefficient to be negative and `p < 0.025` (Bonferroni for two tests).
- If both estimates are negative but one or both fail the corrected threshold, classify the result as **directionally consistent but not confirmatory**.
- If either point estimate is positive, the two-sided-susceptibility replication is **not supported** in this dataset.

M3 and all heterogeneity analyses are secondary and do not rescue a failed H1/H2 result.

## 8. Inclusion and exclusion rules

1. Prefer the authors' released analysis-ready main-study sample.
2. If raw records include participants excluded in the publication, reproduce the authors' published/scripted exclusions **without using focal outcome values**.
3. Analyze the main between-subjects study first; the follow-up within-subject study is reserved as a later replication if its data are separable.
4. Require valid participant ID, trial/item ID, initial human decision, final human decision, AI advice, and ground truth.
5. Capability calculation uses initial decisions only.
6. Primary susceptibility models use initial-disagreement trials only.
7. No participant is excluded based on low/high capability or whether their behavior supports the hypothesis.
8. If fewer than two AI-correct or two AI-wrong disagreement opportunities are available for a participant, retain their eligible trial-level observations; do not construct participant-level rates as the primary analysis.

## 9. Treatment variables and covariates

The three published experimental conditions are included as fixed effects because the original experiment manipulates how AI accuracy is communicated.

Item/case fixed effects are included to absorb the deliberately varying task difficulty and AI correctness composition.

Published subjective numeracy is **not** the primary human-capability construct. The original paper already studied numeracy, and it is a subjective scale rather than an IQ/general-ability measure. It may be used only in a clearly labeled robustness/heterogeneity analysis after the primary models are run.

Trust, affinity for technology, analogy familiarity, and other post/pre-task questionnaire variables are not added to the primary model. They may be secondary sensitivity covariates but cannot determine whether the primary result is declared supported.

## 10. Leakage and coupling safeguards

- The focal trial's initial correctness is excluded from its own capability estimate.
- Final decisions never contribute to capability.
- AI correctness never contributes to capability.
- Capability is standardized after LOTO construction.
- The HAIID effect size is not used to tune exclusions, transformations, or subgroup definitions.
- Published aggregate results from He et al. are not treated as our validation outcome.

## 11. Pre-specified robustness analyses

Run only after M1–M3:

1. unstandardized LOTO capability;
2. participant baseline capability computed from all 10 initial trials, labeled as mathematically coupled sensitivity analysis rather than primary evidence;
3. condition-stratified estimates if each stratum has enough outcome variation;
4. subjective numeracy added as a separate moderator to distinguish task capability from self-reported quantitative confidence;
5. leave-one-item-out stability of H1/H2 coefficients;
6. participant bootstrap of the two primary coefficients.

No robustness analysis can replace the primary result; it diagnoses stability.

## 12. Failure conditions

The validation fails to support the Stage-001 mechanism if:

- either co-primary capability coefficient is positive;
- the result depends on an unregistered exclusion or recoding;
- the raw data do not allow reliable reconstruction of pre-advice, post-advice, AI advice, and ground truth;
- the original study's released records aggregate away trial-level initial decisions;
- the apparent effect is driven by one item and does not survive leave-one-item-out inspection.

If the dataset is structurally unsuitable, mark **VALIDATION DATA INELIGIBLE** rather than redesigning the hypothesis after seeing focal outcomes.

## 13. What this validation cannot establish

Even a successful replication would establish a relationship between **task capability and AI-advice susceptibility** in a loan decision-support setting. It would not establish:

- an IQ effect;
- general intelligence causality;
- an effect in autonomous agents;
- a universal rule across domains;
- that more resistance to AI is normatively better.

The autonomy generalization belongs to Paper 01 and later agentic benchmarks.
