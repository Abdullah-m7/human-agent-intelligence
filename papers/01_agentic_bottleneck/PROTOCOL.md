# Paper 01 Protocol

## Working title

**The Agentic Bottleneck: How Autonomy Repositions the Human Contribution to AI Performance**

## Research question

As an AI system moves from advice to autonomous action, does human capability become less important, or does its influence migrate from task execution toward specification and verification?

## Contribution sought

This paper does not claim that simulated users behave like real humans. It develops a falsifiable **system-level theory** of human–agent performance and identifies regimes that later secondary human data can test.

The novelty target is the autonomy axis. Existing human–AI work commonly studies advice or assistance with fixed interaction structures. We explicitly vary how much of the final action is human-gated versus agent-executed and decompose the human contribution into separate functional capabilities.

## Stylized model

Let:

- `A ∈ [0,1]`: base agent task accuracy;
- `S ∈ [0,1]`: specification quality;
- `H ∈ [0,1]`: human fallback task accuracy;
- `V ∈ [0,1]`: probability that the human detects an agent error when reviewing;
- `Q ∈ [0,1]`: verification specificity, i.e. probability the human does **not** falsely reject a correct agent answer;
- `α ∈ [0,1]`: autonomy, interpreted as the share/probability of decisions executed without human gate;
- `β ≥ 0`: sensitivity of agent task performance to specification quality.

Effective agent capability is

\[
A_{eff}=clip(A + \beta(S-0.5),0,1).
\]

When a decision is human-gated, correctness is

\[
P_{gate}=A_{eff}[Q+(1-Q)H]+(1-A_{eff})VH.
\]

Interpretation:

- if the agent is correct, the reviewer preserves it with probability `Q`; a false rejection falls back to human accuracy `H`;
- if the agent is wrong, the reviewer detects the error with probability `V` and then falls back to `H`;
- undetected agent errors survive.

Joint correctness is

\[
J=\alpha A_{eff}+(1-\alpha)P_{gate}.
\]

This first model is deliberately minimal. Later versions can add correlated errors, asymmetric error costs, multi-step compounding, selective review, and endogenous delegation.

## Primary hypotheses

### H1 — Execution attenuation
Holding the other variables fixed, the sensitivity of `J` to fallback human competence `H` decreases as autonomy `α` increases.

### H2 — Verification attenuation in absolute terms
The sensitivity of `J` to error detection `V` decreases as `α` increases because fewer actions pass through the review gate.

### H3 — Specification persistence
Unlike fallback competence and review sensitivity, the influence of `S` persists at high autonomy because specification changes the effective task that the agent solves before execution begins.

### H4 — Role migration
The **relative** contribution of specification quality to total human-side sensitivity rises with autonomy even when total human intervention falls.

This is the key hypothesis. 'More autonomy' should not be interpreted as 'the human no longer matters'; the locus of human influence may move upstream.

## Secondary hypotheses

### H5 — Verification ceiling
When `A_eff` is high but imperfect, poor `V/Q` can make human gating worse than direct autonomous execution. Human oversight is therefore not monotonically beneficial.

### H6 — Human rescue regime
When `A_eff` is moderate and `H×V` is high, human gating can outperform autonomous execution.

### H7 — Specification dominance at frontier capability
As base agent capability approaches the upper range, marginal gains from better fallback execution shrink, but malformed specification can still materially reduce final performance.

## Computational experiment

### Parameter grid

Initial sweep:

- `A`: 0.55, 0.70, 0.85, 0.95
- `H`: 0.45, 0.60, 0.75, 0.90
- `S`: 0.30, 0.50, 0.70, 0.90
- `V`: 0.30, 0.50, 0.70, 0.90
- `Q`: 0.70, 0.85, 0.95
- `α`: 0.00, 0.25, 0.50, 0.75, 1.00
- `β`: 0.20 in Stage 001 sensitivity demonstration, then sweep 0.05–0.40.

The full initial grid has 4×4×4×4×3×5 = 3,840 cells for each `β`.

### Derived quantities

For every cell compute:

- `A_eff`
- `P_gate`
- `J`
- gain/loss of gating relative to full autonomy;
- finite-difference sensitivity of `J` to `H`, `S`, `V`, and `Q`;
- normalized share of total absolute sensitivity attributable to each human dimension.

## Preregistered decision criteria for the computational claim

Role migration is supported in the stylized model if all of the following hold over a broad non-boundary region (`0.05 < A_eff < 0.95`):

1. median `|∂J/∂H|` is monotonically non-increasing with `α`;
2. median `|∂J/∂V|` is monotonically non-increasing with `α`;
3. median `|∂J/∂S|` at `α=1` remains materially above zero;
4. the median normalized specification share at `α=0.75` exceeds that at `α=0.00`.

We will report the full distribution, not only medians, and explicitly map counterexample regions.

## Robustness extensions

1. **Correlated error model** — human and agent failures share latent task difficulty.
2. **Asymmetric loss** — wrong execution can have larger cost than abstention or deferral.
3. **Multi-step agent** — per-step error compounds across horizon length.
4. **Selective review** — the human reviews only when agent uncertainty crosses a threshold.
5. **Endogenous delegation** — human calibration governs whether the agent is used at all.
6. **Specification ambiguity** — poor `S` shifts both correctness and the probability of optimizing the wrong objective.

## Empirical anchoring plan

The model parameters are not to be chosen to mimic IQ. Plausible ranges will be anchored to published/open human–AI studies where possible:

- baseline human performance → `H`;
- AI-alone performance → `A`;
- correction of wrong advice → `V` proxy;
- unnecessary switching away from correct advice → `1-Q` proxy;
- task framing / collaboration measures → candidate `S` proxies only when measured directly.

## Non-claims

This paper alone cannot establish:

- that IQ causally determines agent performance;
- that LLM-simulated users represent humans of different intelligence;
- that any observed effect generalizes across all tasks;
- that more or less autonomy is globally optimal.

Its job is to expose the structure of the problem, generate exact empirical predictions, and identify which human measurements future secondary analyses need.
