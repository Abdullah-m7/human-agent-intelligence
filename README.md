# Human–Agent Intelligence

A research program on a deceptively simple question:

> **Does the capability of the human constrain the effective intelligence of an AI agent?**

The program studies human–agent systems as joint cognitive systems rather than treating model benchmark scores as the whole story. The central object is **effective joint performance** as a function of agent capability, human capability, task structure, autonomy, specification quality, verification ability, calibration, and the contract under which work is handed between human and agent.

## Core shift

The motivating phrase — *Does your IQ affect your agent?* — is intentionally sharper than the scientific construct. We do **not** infer IQ from prompts, writing style, education, ARC performance, or observed AI use. `IQ / general cognitive ability` is used only when a source dataset measured it directly with a defensible instrument. Otherwise we use narrower constructs such as task capability, expertise, cognitive reflection, metacognitive calibration, verification skill, recovery ability, or interaction strategy.

## Program questions

1. **Human bottleneck:** when is final system performance limited by the human rather than the model?
2. **Role migration:** as agents become more autonomous, does the human contribution disappear or move from execution toward specification and verification?
3. **Capability–Autonomy Gap:** can a better standalone agent create a worse joint system because autonomous coverage expands faster than reliability?
4. **Receiver competence:** when an agent defers, which properties of the receiving human actually reduce residual risk?
5. **Collaborative ability:** is working well with AI a distinct capability from solving the task alone?

## Research strategy: non-human-first

The initial program deliberately avoids new participant recruitment. It combines formal models, executable agents, secondary analysis of open human behavior, quantitative evidence synthesis, and counterfactual routing on task-matched human/agent outcomes. Synthetic users or LLM personas are never treated as evidence about real human IQ.

## Paper portfolio

| Paper | Working title | Primary evidence | New participants? |
|---|---|---|---|
| 01 | **The Agentic Bottleneck: Capability, Autonomy, and Joint-System Performance** | formal model + real-agent benchmark + external validation | No |
| 02 | **Capability-Dependent Susceptibility: Decomposing AI Augmentation into Helpful and Harmful Influence** | secondary individual-level datasets + independent validation | No |
| 03 | **The Verification Ceiling** | open interaction datasets + computational model | No |
| 04 | **Deferral Is a Contract: Receiver Competence in AI Agents** | dense human reasoning panels + real-agent routing benchmarks | No |
| 05 | **From Solo Ability to Collaborative Ability** | secondary re-analysis of suitable open datasets | No |
| 06 | **Does Your IQ Affect Your Agent?** | reserved for data with a direct IQ/general-cognitive-ability instrument | Not necessarily |

## Human–Agent Capability Twin

Stage 003 introduces a benchmark architecture in which archival **real human outcomes** and executable **real agent outputs** are aligned on the same reasoning tasks. Human capability is measured on tasks disjoint from those used to evaluate joint-system value. The first foundation uses CogARC and a public symbolic ARC solver.

Key benchmark objects include:

- **Human Leverage:** joint performance minus agent-only performance;
- **Human Leverage Gradient:** how strongly independent human capability changes joint value;
- **Unsafe Autonomy Mass:** `P(ACT ∧ wrong)`, the task mass exposed to incorrect autonomous action;
- **Capability–Autonomy Gap:** a cross-state mismatch where standalone capability improves but the reliability of newly autonomous coverage does not keep pace;
- **Recovery Value:** the extra system value produced by giving a deferred human a retry/recovery budget rather than treating deferral as an instantaneous handoff.

See `benchmarks/capability_twin/README.md`.

## Stage record

- **Stage 001 — Foundation:** novelty boundary, formal Agentic Bottleneck model, open-data discovery. See `reports/STAGE_001.md`.
- **Stage 002 — Robustness + independent validation:** Role Migration survives alternative computational models; the generic capability-susceptibility hypothesis fails locked CSCW Validation V1 and remains HOLD/REFRAME. See `reports/STAGE_002.md`.
- **Stage 003 — Capability Twin foundation:** dense human capability measurement, real-agent capability/autonomy ladder, cross-fitted Human Leverage Curves, and the first observed Capability–Autonomy inversion. Publication-level generalization remains HOLD pending a substantially different agent family. See `reports/STAGE_003_FOUNDATION.md`.

## Repository principles

- Separate measured constructs from proxies.
- Separate standalone agent capability from autonomous act coverage and act precision.
- Separate discovery from locked validation.
- Preserve failed and inconclusive validations; never post-hoc rescue them.
- Measure human capability on data disjoint from the outcomes used to value the human–agent pair whenever possible.
- Treat deferral as a receiver contract, including recovery/effort budget, not merely an `AI → human` switch.
- Track source provenance and reproducibility before interpreting results.
- Treat this repository as the canonical project record.
