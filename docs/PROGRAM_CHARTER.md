# Program Charter

## 1. Central object

This program treats a human–agent pair as a joint decision system. The scientific target is not `human intelligence` or `model intelligence` in isolation, but the mapping

\[
J = f(A, H, S, V, C, \alpha, T)
\]

where:

- `J`: joint system performance;
- `A`: base agent capability on the task;
- `H`: human fallback task competence;
- `S`: human specification quality (goal framing, constraints, decomposition);
- `V`: human verification / error-detection ability;
- `C`: calibration / discrimination between correct and incorrect agent outputs;
- `α`: agent autonomy, from fully human-gated to largely self-executing;
- `T`: task structure and stakes.

The program asks which partial derivative dominates under which regime, rather than assuming a single global answer to whether 'smart users get more from AI'.

## 2. Core theoretical claim to test

**Role Migration Hypothesis**: increasing agent autonomy does not necessarily remove the human bottleneck. It can reduce the importance of human execution/fallback ability while preserving or increasing the relative importance of upstream specification quality and downstream verification.

This differs from a generic equalizer/amplifier claim. The unit of analysis is an **agentic workflow with varying autonomy**, not merely a human receiving one-shot AI advice.

## 3. Construct discipline

### Directly measured constructs
A construct may be called cognitive ability or IQ only when a source dataset includes a defensible direct measure.

### Acceptable narrower proxies
- baseline task performance;
- domain expertise / tenure;
- education (reported only as education, never relabeled as intelligence);
- confidence calibration;
- error-detection rate;
- theory-of-mind / perspective-taking measure;
- interaction strategy;
- prompt/delegation behavior.

### Prohibited inference
Never infer IQ from prompt quality, language fluency, occupation, education, AI usage logs, or LLM-based personality scoring.

## 4. Evidence ladder

1. **Formal derivation** — state assumptions and derive the expected direction of effects.
2. **Computational stress test** — sweep the plausible parameter space and identify phase transitions / counterexamples.
3. **Secondary human data** — reanalyse open datasets with measured baseline ability or calibration.
4. **Meta-regression** — estimate how human baseline capability moderates AI augmentation across studies.
5. **Naturalistic traces** — use public/licensed interaction data only for behavioral constructs that are actually observable.
6. **New human study** — optional later validation, not a prerequisite for the initial papers.

## 5. Falsifiability

The role-migration hypothesis fails if, over broad plausible regimes, increasing autonomy uniformly makes all human-side dimensions irrelevant, or if specification/verification sensitivity does not persist after execution/fallback influence declines.

The empirical capability-gradient hypothesis fails if open human datasets show no reproducible association between pre-AI baseline capability and AI treatment gain after accounting for ceiling effects, task difficulty, and measurement error.

## 6. Novelty boundary as of 2026-08-28

Existing work already establishes several nearby results:

- Vaccaro, Almaatouq & Malone (Nature Human Behaviour, 2024) meta-analysed 106 experiments / 370 effects and showed that average human–AI systems do not automatically outperform the stronger constituent.
- Noy & Zhang (Science, 2023) reported larger ChatGPT benefits for weaker professional writers.
- Brynjolfsson, Li & Raymond (QJE, 2025) found larger gains for novice/lower-skilled customer-support workers.
- Dell'Acqua et al. (Organization Science, 2026) established a jagged AI capability frontier and showed that AI can help on some knowledge tasks while harming performance beyond the frontier.
- Bigoni et al. (arXiv, 2025) explicitly framed AI as an equalizer vs amplifier of cognitive differences.
- Riedl & Weidmann (PsyArXiv, v3 2026) separated individual ability from collaborative ability and found Theory of Mind predictive of AI collaboration.
- Ming (arXiv, 2026) reported a forecasting pilot in which collaborative traits, not raw cognitive ability, distinguished high-performing human–AI modes.

Therefore this repository will **not** claim novelty for the generic proposition that lower-skill users can benefit more from AI, nor for the phrase 'equalizer or amplifier'. The intended contribution is the transition from static assistance to **autonomy-dependent human bottlenecks in agentic systems**, plus a disciplined synthesis of which human capability matters at each autonomy regime.

## 7. Publication architecture

Paper 01 develops and stress-tests the agentic bottleneck model.

Paper 02 performs a secondary-data capability-gradient synthesis, with ceiling-effect correction and construct taxonomy.

Paper 03 isolates verification as a ceiling on safe joint performance.

Paper 04 connects the program to deferral: an agent should not defer merely because a human exists; the receiver's competence must dominate the relevant residual risk.

Paper 05 studies collaborative ability as distinct from solo task ability using suitable open individual-level datasets.

Paper 06 reserves the original provocative question — 'Does Your IQ Affect Your Agent?' — for evidence with direct cognitive measurement.
