# Stage 001 — Agentic Bottleneck Foundation & Open-Data Discovery

Date: 2026-08-28
Branch: `stage-001-agentic-bottleneck-foundation`

## Controller decision

**FOUNDATION: PASS**
**PUBLICATION CLAIMS: HOLD**

Stage 001 successfully turns the motivating question — *Does your IQ affect your agent?* — into a multi-paper research program with explicit construct rules, a falsifiable agentic model, reproducible open-data discovery analyses, and untouched validation candidates. It does **not** yet justify a paper-level causal claim about IQ, human intelligence, or autonomous agents.

## 1. What Stage 001 was required to establish

1. Determine whether the broad idea is already occupied.
2. Replace the provocative IQ wording with measurable constructs where necessary.
3. Identify research questions that can be pursued without recruiting new participants.
4. Build at least one falsifiable computational model.
5. Audit open human–AI datasets rather than relying on narrative literature alone.
6. Separate discovery from validation before results are promoted to claims.

All six foundation requirements were met.

## 2. Novelty audit

The broad territory is **not** empty.

Existing work already establishes that lower-performing or less-experienced users can sometimes receive larger AI gains, that human–AI systems do not automatically outperform their strongest constituent, that individual task ability differs from collaborative ability, that cognitive reflection/metacognition can relate to AI use, and that nominal human oversight can fail in agentic systems.

Accordingly, this repository does **not** claim novelty for:

- `AI as equalizer vs amplifier` as a generic framing;
- `lower-skill people can benefit more from AI`;
- `CRT affects advice taking`;
- `humans can fail to oversee agents`;
- `human-in-the-loop is not automatically safe`.

The strongest remaining program-level gaps identified in Stage 001 are narrower:

1. **Autonomy-dependent role migration:** which human capability matters as AI moves from advice to autonomous action?
2. **Capability-dependent susceptibility:** does lower task capability produce larger AI gains because of more opportunity, greater general susceptibility, better selectivity, or some combination?
3. **Deferral receiver competence:** when an agent defers, is the receiving human actually competent on the residual decision?
4. **Verification ceiling:** when does human review rescue errors, and when does it inject errors into a stronger agent?

See `docs/PROGRAM_CHARTER.md` and `docs/EVIDENCE_REGISTRY.md` for the detailed boundary.

## 3. Paper 01 — Agentic Bottleneck

Working title:

> **The Agentic Bottleneck: How Autonomy Repositions the Human Contribution to AI Performance**

### Model implemented

The Stage 001 stylized model separates:

- base agent capability `A`;
- human fallback capability `H`;
- specification quality `S`;
- error detection `V`;
- review specificity `Q`;
- autonomy `α`.

The full initial grid contains **3,840 cells**, corresponding to **768 unique capability/review configurations × 5 autonomy levels**.

### Stage 001 model-implied pattern

Across the full grid, as autonomy increased from `α=0` to `α=0.75`:

- median `|∂J/∂H|` fell from **0.2710** to **0.06775**;
- median `|∂J/∂V|` fell from **0.1335** to **0.033375**;
- median `|∂J/∂S|` rose from **0.1090** to **0.17725**;
- median specification share of total modeled human-side sensitivity rose from **13.6%** to **50.5%**.

At full autonomy in this stylized formulation, fallback/review sensitivity is zero while specification sensitivity remains because specification acts upstream of execution.

### Human-gating counterexamples

In **267 / 768 = 34.8%** of unique configurations, the human review gate produces lower expected correctness than full autonomous execution in the stylized model.

The fraction of configurations where gating is worse rises with base agent capability:

| Base agent capability | Gating-worse fraction |
|---:|---:|
| 0.55 | 4.2% |
| 0.70 | 15.1% |
| 0.85 | 39.6% |
| 0.95 | 80.2% |

### Scientific interpretation

**This is a structural sanity check, not empirical evidence.** The role-migration pattern partly follows from the model architecture: some human dimensions enter the review gate while specification enters upstream. The current simulation therefore cannot by itself establish that real agents or humans exhibit the same transition.

Paper 01 is **GO for Stage 002**, but its publication claim remains **HOLD** until the pattern survives:

- alternative formalizations;
- correlated human/agent errors;
- selective rather than universal review;
- multi-step agent horizons;
- at least one real agentic benchmark where autonomy/specification can be manipulated without simulating human IQ.

## 4. Paper 02 — Capability-Dependent Susceptibility

Working title:

> **Capability-Dependent Susceptibility: Decomposing AI Augmentation into Helpful and Harmful Influence**

The key conceptual decomposition is:

- **helpful susceptibility:** movement toward AI when AI corrects the human;
- **harmful susceptibility:** movement toward AI when AI would make the human worse;
- **selectivity:** discrimination between those two regimes;
- **net augmentation:** the resulting performance change, which is an outcome rather than a mechanism.

### Discovery dataset A — HAIID

Public Human–AI Interactions Dataset audited:

- **35,670** total interaction rows;
- **1,125** participants;
- **17,973** AI-advice rows;
- **567** participants in the AI-advice subset;
- five tasks: art, census, cities, dermatology, sarcasm.

To reduce direct mathematical coupling between baseline performance and improvement, Stage 001 uses **cross-fitting**: task capability is estimated on one disjoint half of each participant's trials and AI-response outcomes on the other half, then folds are reversed. The process is repeated over 100 random seeds and pooled effects are task-centered.

Mean discovery correlations across 100 seeds:

| Outcome | Mean correlation with independently estimated task capability |
|---|---:|
| Net AI gain, task-centered | **-0.1843** |
| Correct-advice uptake | **-0.1277** |
| Resistance to wrong advice | **+0.1599** |
| Harmful switch toward wrong advice | **-0.1599** |
| Selectivity | **+0.0137** |

The 5th–95th percentile range for the selectivity correlation spans zero (`-0.0349` to `+0.0747`).

### Discovery interpretation

A plausible mechanism is therefore **not** that higher-capability people simply verify AI better. In these data, higher task capability is associated with *less susceptibility to AI in both directions*: less uptake of correct advice and less harmful switching to incorrect advice. Net equalization can therefore emerge even without a selectivity advantage if the AI is, on average, better than the lower-capability human.

This is a **discovery result**, not a confirmatory claim.

## 5. Direct cognitive measure discovery — CRT forecasting data

An additional open forecasting dataset from Himmelstein et al. contains:

- **171 participants**;
- **15 forecasts per participant = 2,565 trials**;
- Human, Algorithm, and Hybrid advice;
- a **7-item Cognitive Reflection Test (`CRTsc`, 0–7)**;
- Brier scores for the participant before advice, the advice, and the final forecast after advice.

CRT is a direct measure of **cognitive reflection**, not IQ or general intelligence.

### Baseline relation

At participant level, higher CRT is associated with better unaided forecasting quality:

- `r(CRT, mean baseline Brier) = -0.4144`, `p < 0.001`;
- lower Brier is better.

### Algorithm-only exploratory model

In the **855 algorithm-advice trials** from all 171 participants, the exploratory model

`final Brier ~ initial-human Brier + advice Brier + CRT_z + item fixed effects`

with participant-clustered uncertainty gives:

- `CRT_z coefficient = -0.01306`;
- `SE = 0.00595`;
- `p = 0.0282`;
- 95% CI `[-0.02471, -0.00140]`.

Robustness checks:

- domain fixed effects: `-0.01374`, `p = 0.0213`;
- item effects + agreement/relative-peakedness controls: `-0.01184`, `p = 0.0337`;
- leave-one-item-out: **15 / 15 coefficients remain negative**, range `[-0.01462, -0.00996]`;
- 500 participant-resampling bootstrap median `-0.01273`, percentile 95% interval `[-0.02477, -0.00245]`.

However:

- CRT does not clearly predict mean algorithm-advice weight in the valid DWOA subset (`p = 0.373`);
- `CRT × relative advice quality` on DWOA is also not clear (`p = 0.208`);
- adding a larger demographic/covariate set moved the focal coefficient to borderline significance (`p ≈ 0.051`).

### Decision

This is **exploratory/hypothesis-generating only**. The original study already used CRT as a covariate, and these focal models were selected after inspecting the data. They cannot be presented as preregistered confirmation.

The interesting candidate hypothesis is narrower than `CRT changes advice taking`:

> Cognitive reflection may predict final human–algorithm integration quality even when average advice weight does not materially change.

That hypothesis requires untouched validation.

## 6. Meta-analysis feasibility audit

The open Vaccaro et al. meta-analysis dataset contains:

- **370 effects**;
- **73 papers**;
- **106 experiments**;
- human-alone, AI-alone and human+AI performance variables;
- participant/expertise descriptors.

However, strict automated matching of explicit expert vs non-expert groups within the same paper/task/condition/metric yielded only one clearly encoded paper with paired groups in the initial audit. Therefore the existing extraction **cannot by itself carry a strong within-study expertise-gradient paper**.

Decision: **do not force the meta-analysis to answer a question its coding does not support.** Use it as a scaffold and bibliography, not as proof of the focal capability mechanism.

## 7. Untouched validation assets

Two validation routes are preserved:

1. **Soleimanof & Neufeld, Decision Support Systems (2026)** — N=440, open OSF dataset, direct metacognition focus. The workbook schema has been inspected, but the focal capability/susceptibility outcome analysis has not been run.
2. **Open CSCW / judge-advisor datasets** with pre-AI and post-AI decisions and manipulated AI reliability. Candidate datasets must remain untouched on the focal outcome until the validation specification is frozen.

Once a candidate's focal result is inspected, it loses confirmatory status and becomes another discovery dataset.

## 8. Construct integrity decisions

Stage 001 permanently adopts these rules:

- task performance ≠ IQ;
- education ≠ intelligence;
- tenure ≠ general cognitive ability;
- confidence ≠ metacognitive sensitivity;
- CRT ≠ IQ;
- rejecting AI ≠ good verification unless correct and incorrect advice are discriminated;
- LLM personas cannot stand in for people of different IQ levels.

**Paper 06, `Does Your IQ Affect Your Agent?`, remains HOLD** until a defensible open dataset with a direct IQ/general-cognitive-ability instrument and human–AI interaction outcomes is identified.

## 9. Reproducibility status

Implemented:

- hash-pinned external-data fetcher;
- HAIID cross-fitted analysis script;
- CRT forecasting exploratory analysis script;
- stylized agentic bottleneck model;
- Stage 001 summary generator;
- five unit tests for core model invariants.

Latest local QA on 2026-08-28:

- external source hashes verified;
- HAIID analysis reproduced;
- CRT exploratory analysis reproduced;
- **5 / 5 model tests PASS**.

Raw third-party datasets and large regenerable result grids are not committed; compact summaries and source hashes are retained.

## 10. Stage 002 admission

### Paper 01 — GO

Next requirement: break the circularity risk of the stylized model by testing role migration under **alternative models and real agentic tasks**.

### Paper 02 — GO

Next requirement: freeze an untouched validation specification and test whether the HAIID susceptibility pattern replicates across independent datasets and task types.

### Paper 03 — PROVISIONAL GO

The 34.8% modeled gating-harm region justifies a dedicated verification-ceiling analysis, but it should be developed after Paper 01 alternative-model checks so the result is not inherited from one model architecture.

### Paper 04 — PROVISIONAL GO

Deferral receiver competence remains theoretically promising and connects directly to the larger program, but no empirical Stage 001 result yet supports a paper-level claim.

### Paper 05 — HOLD FOR DATA AUDIT

Collaborative ability is scientifically occupied enough that a new paper needs a sharper identifiable mechanism or a strong secondary-data replication.

### Paper 06 — HOLD

No direct IQ/general-intelligence dataset has yet cleared the construct threshold.

## 11. Immediate Stage 002 work order

1. Build at least two alternative Paper 01 models: correlated-error and selective-review versions.
2. Select an open agentic benchmark and operationalize autonomy/specification without pretending synthetic personas are human intelligence levels.
3. Reconstruct the Soleimanof & Neufeld task/scoring semantics without inspecting the focal validation result.
4. Freeze Paper 02 validation outcomes, exclusions, models, and failure criteria before running them.
5. Audit additional open datasets for a direct IQ/general-cognitive-ability measure; if none is defensible, keep the provocative IQ paper shelved rather than weakening the construct.

Stage 001 therefore ends with **two active paper tracks, two provisional tracks, and two held tracks**. The program is scientifically viable without new participant recruitment, but the strongest claims now require independent validation rather than additional post-hoc mining.
