# Paper 02 Protocol

## Working title

**Capability-Dependent Susceptibility: Decomposing AI Augmentation into Helpful and Harmful Influence**

## Status

**Discovery protocol, not preregistration.** Stage 001 analyses of HAIID and Himmelstein Study 2 were conducted before this document was finalized. Any directional patterns from those datasets are hypothesis-generating. Confirmatory language is reserved for independent datasets not inspected for the focal outcomes before the validation plan is locked.

## Motivation

A recurring result in human–AI research is that lower-performing or less-experienced people can receive larger average performance gains from AI. That observation alone does not identify the behavioral mechanism.

A larger gain can arise because a lower-capability person:

1. has more errors available for AI to correct (**opportunity / ceiling**);
2. is more likely to accept AI input in general (**susceptibility**);
3. is especially good at distinguishing correct from incorrect AI input (**selectivity / calibration**);
4. receives advice whose relative quality is larger because the human baseline is weaker;
5. some combination of the above.

This paper separates those mechanisms instead of treating `AI gain` as a single outcome.

## Core constructs

### Task capability
Performance measured **independently** from the trials used to estimate advice response, preferably by cross-fitting repeated trials. This is task capability, not IQ.

### Helpful susceptibility
Probability or magnitude of movement toward AI when doing so improves the judgment.

For binary decision data:

\[
S_+ = P(\text{final correct}\mid \text{initial wrong, AI correct}).
\]

### Harmful susceptibility
Probability or magnitude of movement toward AI when doing so harms the judgment.

For binary decision data:

\[
S_- = P(\text{final wrong}\mid \text{initial correct, AI wrong}).
\]

### Selectivity
A simple behavioral discrimination score:

\[
D = S_+ - S_-.
\]

A person can have low susceptibility to both correct and incorrect advice (`S+` and `S-` both low) without having strong selectivity. Resistance is therefore not automatically verification skill.

### Net augmentation

\[
G = Performance_{post-AI} - Performance_{pre-AI}.
\]

Net augmentation is an outcome, not a mechanism.

## Discovery dataset A — HAIID

Source: Vodrahalli et al. AIES 2022 open Human-AI Interactions Dataset.

Stage 001 audited:

- 35,670 total interaction rows;
- 1,125 participants;
- 17,973 rows / 567 participants in the AI-advice subset;
- five tasks: art, census, cities, dermatology, sarcasm;
- repeated pre-advice and post-advice responses with advice correctness.

### Cross-fitting rule

For each random split and participant:

1. estimate task capability from one half of that participant's initial judgments;
2. estimate AI-related outcomes from the other half;
3. reverse the folds;
4. task-center outcomes before pooled correlations;
5. repeat over random seeds.

This prevents the strongest form of mathematical coupling caused by defining both baseline ability and improvement from the same observations.

### Stage 001 discovery pattern

Across 100 repeated cross-fits:

- higher independently estimated task capability predicted lower net AI gain;
- higher capability predicted lower uptake of correct AI advice when initially wrong;
- higher capability also predicted lower harmful switching toward incorrect AI advice when initially correct;
- the capability–selectivity association was small and unstable around zero.

Interpretation to validate: **capability may primarily change susceptibility to AI influence in both directions, while net equalization depends on the AI being more accurate than the lower-capability human.**

This interpretation is not yet a confirmatory claim.

## Discovery dataset B — Himmelstein Study 2

Source: open Study 2 data from Himmelstein et al., *Journal of Behavioral Decision Making* (2023).

- 171 participants;
- 15 probabilistic forecasts each (2,565 trials);
- Human, Algorithm, and Hybrid advice;
- 7-item Cognitive Reflection Test (`CRTsc`, 0–7);
- Brier scores before advice, after advice, and for the advice itself;
- DWOA advice-weight measure.

The original publication already included CRT as a covariate. Therefore **a generic CRT → advice-taking claim is not novel**.

Stage 001 exploratory work instead asks whether CRT predicts *final integration quality conditional on constituent quality*. In the algorithm-only subset (855 trials), a higher standardized CRT score was associated with lower final Brier score after controlling for initial-human Brier, advice Brier, and item fixed effects. The same exploration did not show a clear CRT association with mean advice weight or a clear `CRT × relative advice quality` interaction on DWOA.

Because these analyses were selected after inspecting the data, they are hypothesis-generating only.

## Locked validation questions

The following questions are now fixed for untouched validation datasets:

### VQ1 — Susceptibility
Does independently measured task capability predict lower movement toward AI advice in **both** helpful and harmful advice regimes?

### VQ2 — Selectivity
After separating general susceptibility, does task capability materially improve discrimination between helpful and harmful AI advice?

### VQ3 — Opportunity decomposition
How much of the observed capability gradient in net AI gain is explained by:

- baseline opportunity to improve;
- relative AI-vs-human quality;
- general advice susceptibility;
- selective reliance?

### VQ4 — Metacognitive validation
Do direct metacognitive measures predict selectivity after controlling for task capability and general susceptibility?

### VQ5 — Cognitive reflection extension
Where an independent dataset contains a direct CRT or comparable cognitive-reflection measure, does reflection predict final integration quality conditional on the quality of the human and AI constituent judgments?

## Candidate untouched validation assets

1. **Soleimanof & Neufeld (Decision Support Systems, 2026)** — N=440; open OSF data; direct metacognitive-sensitivity focus. Raw workbook has been schema-inspected, but the focal outcome coding has not been analyzed in Stage 001.
2. **He, Buijsman & Gadiraju / CSCW** — open loan-decision interaction dataset with decisions before and after AI advice and manipulated stated AI accuracy. Focal capability/susceptibility analyses have not been run.
3. Additional open judge-advisor datasets will be audited before the validation set is frozen.

A dataset becomes ineligible for confirmatory status once its focal capability/susceptibility result has been inspected.

## Statistical plan for validation

Where repeated binary decisions are available, fit trial-level multilevel or cluster-robust models on trials where human and AI initially disagree:

\[
SwitchToAI \sim Capability + AdviceQuality + Capability\times AdviceQuality + Task + design\ controls.
\]

The main targets are:

- general capability effect on susceptibility;
- capability × advice-quality interaction (selectivity);
- predicted helpful and harmful switch probabilities;
- task-level heterogeneity.

Where continuous forecasts are available, model movement toward advice and final proper-scoring-rule loss while conditioning on both initial-human and advice quality.

### Required robustness

- participant-clustered uncertainty;
- task/item effects where possible;
- cross-fitted capability estimates when capability is computed from repeated task performance;
- separate direct cognitive measures from performance-derived capability;
- report ceiling/opportunity decomposition;
- leave-one-task/dataset-out sensitivity;
- avoid dichotomizing continuous capability except for visualization.

## Claims this paper will not make

- `task capability = IQ`;
- `CRT = IQ`;
- resistance to AI advice = good verification;
- lower average AI gain among high-capability users means AI is useless to them;
- a post-hoc p-value in a discovery dataset is confirmatory evidence;
- results from advice-taking automatically generalize to autonomous agents.

The last boundary is important: Paper 02 studies static/sequential AI advice. Paper 01 separately tests whether these human-side effects migrate when systems become genuinely agentic and autonomous.

## Stage 002 update — Validation V1 outcome

The first locked independent validation used He, Buijsman & Gadiraju (CSCW 2023). The complete lock and audit trail are in `VALIDATION_LOCK_V1.md` and `reports/STAGE_002_VALIDATION_V1.md`.

**Result: TWO_SIDED_SUSCEPTIBILITY_NOT_SUPPORTED.**

The registered helpful-susceptibility coefficient was positive rather than negative (`+0.0647`, p `0.360`), while the harmful-susceptibility coefficient was approximately zero (`-0.0080`, p `0.950`). Leave-one-item-out and participant-bootstrap diagnostics did not rescue the pattern.

A post-validation reliability diagnostic found that the 10-item CSCW unaided-accuracy construct had very low split-half stability (mean Spearman–Brown ≈ `0.08`) and the LOTO capability score did not predict focal initial correctness. This does **not** change the failed validation verdict. It does impose a stronger eligibility requirement for Validation V2.

### Validation V2 eligibility rule

Before focal AI-reliance outcomes are inspected, the candidate dataset must provide at least one of:

1. a direct, defensible cognitive / psychometric measure relevant to the hypothesized construct; or
2. a repeated unaided task battery with enough observations to establish stable between-person capability independently of AI-use outcomes.

For performance-derived capability, measurement reliability / predictive validity must be audited before the focal susceptibility model is run. The exact acceptance threshold will be locked for V2 before the candidate's focal outcome is inspected.

The HAIID pattern is therefore retained as a **context-dependent discovery**, not a generic law.
