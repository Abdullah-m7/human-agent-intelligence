# Human–Agent Intelligence

A research program on a deceptively simple question:

> **Does the capability of the human constrain the effective intelligence of an AI agent?**

The program studies human–agent systems as joint cognitive systems rather than treating model benchmark scores as the whole story. The central object is **effective joint performance** as a function of agent capability, human capability, task structure, autonomy, specification quality, verification ability, and calibration.

## Core shift

The motivating phrase — *Does your IQ affect your agent?* — is intentionally sharper than the scientific construct. We do **not** infer IQ from prompts, writing style, education, or observed AI use. `IQ / cognitive ability` is used only when a source dataset measured it directly with a defensible instrument. Otherwise we use narrower constructs such as baseline task ability, expertise, metacognitive calibration, verification skill, or interaction strategy.

## Program questions

1. **Human bottleneck:** when is final system performance limited by the human rather than the model?
2. **Role migration:** as agents become more autonomous, does the human contribution disappear or move from execution toward specification and verification?
3. **Equalization vs compounding:** when does AI compress pre-existing capability gaps, and when does it widen them?
4. **Deferral receiver competence:** when an agent defers, is the receiving human actually more competent for the decision being returned?
5. **Collaborative ability:** is working well with AI a distinct capability from solving the task alone?

## Research strategy: non-human-first

The initial program deliberately avoids new participant recruitment. It combines:

- formal models and computational stress tests;
- secondary analysis of open human–AI datasets;
- quantitative evidence synthesis / meta-regression;
- public interaction traces where licensing and construct validity permit;
- later human studies only if a specific hypothesis survives the earlier stages.

Synthetic users or LLM personas are never treated as evidence about real human IQ. They may be used only as explicit computational policies in system-level simulations.

## Paper portfolio

| Paper | Working title | Primary evidence | New participants? |
|---|---|---|---|
| 01 | **The Agentic Bottleneck: How Autonomy Repositions the Human Contribution** | formal model + computational experiment | No |
| 02 | **Capability Gradients in Human–AI Augmentation** | secondary-data meta-analysis | No |
| 03 | **The Verification Ceiling** | open interaction datasets + computational model | No |
| 04 | **Who Should Receive the Deferral?** | formal decision model + public benchmarks | No |
| 05 | **From Solo Ability to Collaborative Ability** | secondary re-analysis of suitable open datasets | No |
| 06 | **Does Your IQ Affect Your Agent?** | reserved for datasets with direct cognitive measurement | Not necessarily |

## Stage 001

Stage 001 establishes the novelty boundary, formalizes Paper 01, creates an evidence registry, and implements the first falsifiable simulation. See `reports/STAGE_001.md` and `papers/01_agentic_bottleneck/PROTOCOL.md`.

## Repository principles

- Separate measured constructs from proxies.
- Separate computational demonstrations from claims about human psychology.
- Prefer preregisterable hypotheses and reproducible code.
- Track source licensing and data availability before analysis.
- Treat the repository as the canonical record of project state.
