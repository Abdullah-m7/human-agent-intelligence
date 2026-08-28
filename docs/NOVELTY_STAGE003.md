# Stage-003 Novelty Boundary

## Occupied territory

The following are prior art and must not be presented as our novelty:

- learning whether to defer to a human rather than predict automatically;
- routing to one of multiple human experts;
- jointly learning to defer and complement multiple users;
- optimizing deferral under human-consultation cost or coverage constraints;
- using expert predictions to model heterogeneous human expertise;
- applying item-response models to human ARC performance;
- the generic claim that human and AI errors can be complementary.

Representative nearby work includes multi-expert L2D/L2C methods from 2023–2026 and the 2025 Scientific Data benchmark for learning to defer.

## Why the CogARC construction is still interesting

Public multi-expert deferral datasets are typically sparse in repeated predictions per expert and overlap among experts. CogARC was not created for learning-to-defer, but after its official inclusion rules it provides a dense reasoning panel: 199 people, 75 shared abstract-reasoning items, and 12,138 analyzed trials with retry/process data.

The project treats that structure as an opportunity to build a counterfactual human–agent benchmark, not as a claim that CogARC itself is new.

## Candidate contribution

The scientific object is a **psychometrically calibrated Human–Agent Capability Twin**:

- the human is an observed archival person, not an LLM persona;
- capability is estimated from disjoint reasoning items;
- the agent is executable on the same item set;
- ACT/DEFER policies are evaluated against held-out human outcomes;
- autonomy is measured as actual act coverage, separately from standalone task accuracy;
- human recovery/effort budget is part of the deferral contract.

## Candidate theoretical construct

**Capability–Autonomy Gap:** a mismatch between improvements in standalone agent capability and the reliability of the additional region over which the agent takes autonomous action.

A critical consequence to test is an inversion:

`Agent_B standalone > Agent_A standalone`

while

`Human+Agent_B joint < Human+Agent_A joint`.

Stage 003 observes such an inversion in one real solver ladder. It remains a discovery result until replicated across architectures.

## Publication discipline

Do not use the terms `IQ effect`, `intelligence amplifier`, `first dense deferral dataset`, or `first personalized deferral` without a new comprehensive literature check and direct evidence. The working claims should remain about task capability, human leverage, recovery, autonomy calibration, and joint-system performance.
