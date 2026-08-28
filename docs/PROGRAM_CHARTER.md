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

**Role Migration Hypothesis**: increasing agent autonomy need not remove the human bottleneck; it can change *where* human capability enters the system. Routine execution and continuous review may attenuate as autonomy rises, while upstream specification can remain influential because it shapes the objective before autonomous action begins. Verification remains important where review, auditing, escalation, or exception-handling gates still exist.

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

The role-migration hypothesis fails if, across alternative defensible models and real agentic tasks, increasing autonomy makes upstream specification no more consequential than execution/fallback capability or if the apparent migration is only an artifact of the chosen equations.

The empirical capability-gradient hypothesis fails if open human datasets show no reproducible association between independently measured pre-AI task capability and AI treatment gain after accounting for ceiling effects, task difficulty, measurement error, and advice quality.

## 6. Novelty boundary as of 2026-08-28

Existing work already establishes several nearby results:

- Vaccaro, Almaatouq & Malone (Nature Human Behaviour, 2024) meta-analysed 106 experiments / 370 effects and showed that average human–AI systems do not automatically outperform the stronger constituent.
- Noy & Zhang (Science, 2023) reported larger ChatGPT benefits for weaker professional writers.
- Brynjolfsson, Li & Raymond (QJE, 2025) found larger gains for novice/lower-skilled customer-support workers.
- Dell'Acqua et al. (Organization Science, 2026) established a jagged AI capability frontier and showed that AI can help on some knowledge tasks while harming performance beyond the frontier.
- Bigoni et al. (arXiv, 2025) explicitly framed AI as an equalizer vs amplifier of cognitive differences.
- Riedl & Weidmann (PsyArXiv, v3 2026) separated individual ability from collaborative ability and found Theory of Mind predictive of AI collaboration.
- Ming (arXiv, 2026) reported a forecasting pilot in which collaborative traits, not raw cognitive ability, distinguished high-performing human–AI modes.
- Mitchell, Ghosh & Passi (arXiv:2608.23642, 2026) argue that current agent design can undermine the cognitive capacities required for meaningful human oversight.
- Singh et al. / Data & Society (The Oversight Fallacy, 2026) emphasize that a nominal human-in-the-loop is insufficient when people cannot recognize agent mistakes early enough to intervene.
- Anthropic (2026) reports real-world variation in agent autonomy and longer autonomous work intervals, reinforcing the need to treat autonomy as an empirical system dimension rather than a binary label.

Therefore this repository will **not** claim novelty for the generic proposition that lower-skill users can benefit more from AI, for the phrase 'equalizer or amplifier', or for the generic warning that human oversight can fail. The intended contribution is to quantify **autonomy-dependent reweighting of human capabilities** and to connect task capability with both beneficial and harmful susceptibility to AI influence using defensible secondary data.

## 7. Publication architecture

Paper 01 develops the agentic bottleneck model, stress-tests it against alternative assumptions, and then tests its autonomy predictions on real agentic tasks without human recruitment.

Paper 02 uses open individual-level human–AI data to study **capability-dependent susceptibility**: whether higher task capability changes uptake of correct AI advice, harmful switching to incorrect advice, and net performance gain. The Stage 001 HAIID analysis is a feasibility signal, not a final confirmatory result.

Paper 03 isolates the **verification ceiling**: when oversight becomes harmful, when it rescues agent errors, and how those regimes change with agent capability and error correlation.

Paper 04 connects the program to deferral: an agent should not defer merely because a human exists; the receiver's competence must dominate the relevant residual risk.

Paper 05 studies collaborative ability as distinct from solo task ability using suitable open individual-level datasets.

Paper 06 reserves the original provocative question — 'Does Your IQ Affect Your Agent?' — for evidence with direct cognitive measurement.
