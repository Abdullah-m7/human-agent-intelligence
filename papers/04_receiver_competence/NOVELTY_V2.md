# Paper 04 — Receiver Recovery Novelty Audit V2

Date: 2026-08-29

## Controller conclusion

Do **not** claim novelty for any of the following:

- choosing whether to defer to a human expert;
- conditioning deferral on which expert receives the case;
- modeling expert accuracy or expert populations;
- sequential or costly deferral;
- choosing additional information, retrieved evidence, tool outputs, or escalation context for an expert after the expert is selected;
- multi-stage collaboration when both human and AI are uncertain.

The provisional gap is narrower: **empirically measured recovery capacity of the same real human receiver across repeated attempts, and the portion of that recovery opportunity rendered unreachable because the agent autonomously ACTs instead of handing off the task.**

## Closest adjacent work

### Learning-to-Defer with Expert-Conditioned Advice (2026)

Montreuil et al. explicitly relax the assumption that an expert's information is fixed at decision time. After routing to an expert, the system can also choose additional information/advice for that expert, including retrieved documents, tool outputs, or escalation context. The method optimizes the joint expert × advice action space.

Source: https://arxiv.org/abs/2603.14324

Implication for Paper 04: we cannot claim that “deferral is a contract because resources after deferral matter” is a theoretical first. Information acquisition after routing is already formalized.

### Beyond Augmented-Action Surrogates for Multi-Expert Learning-to-Defer (2026)

A closely related 2026 treatment studies the composite expert–advice decision and consistency of L2D surrogates.

Source: https://arxiv.org/abs/2604.09414

### Sequential Learning-to-Defer

Sequential L2D models the long-term consequences and timing/cost of human intervention rather than independent one-shot routing.

Source: https://arxiv.org/abs/2109.06312

Implication: temporal or costly human intervention is not new by itself.

### A²C multi-stage Human–AI collaboration

A²C distinguishes automated decisions, augmented deferral, and collaborative exploration for cases in which both human and AI may be uncertain.

Source: https://www.sciencedirect.com/science/article/pii/S0957417425009406

Implication: multi-stage collaboration after uncertainty is also adjacent prior art.

### OpenL2D / FiFAR benchmark (Scientific Data, 2025)

OpenL2D explicitly argues that expert diversity and work-capacity constraints matter for L2D benchmarking. Its benchmark uses synthetic experts calibrated to real expert-like behavior.

Source: https://www.nature.com/articles/s41597-025-04664-y

Implication: Paper 04 cannot claim novelty for saying expert work capacity matters. The distinction is that our receiver recovery is observed from repeated behavior of the same archived humans on the same reasoning tasks, rather than assigned to synthetic experts as a capacity parameter.

## Narrow empirical construct

Paper 04 uses CogARC's repeated submissions to distinguish:

- `H_first(t)`: first-pass success probability;
- `H_final(t)`: eventual success probability under the source experiment's retry opportunity;
- `R(t) = H_final(t) - H_first(t)`: empirically observed recovery opportunity.

For an agent ACT indicator `A(t)`:

`RecoverySuppressionMass = E[A(t) * R(t)]`.

This is an **accounting quantity**, not claimed as a new causal estimand or a new optimal-routing theorem. It asks a concrete benchmark question:

> How much recovery capacity demonstrated by real human receivers becomes unavailable under a particular autonomous-routing policy?

## What a publishable contribution would require

A defensible paper should contribute the combination, not one isolated phrase:

1. dense real-human person × task data;
2. repeated attempts by the same receiver, enabling first-pass vs recovery measurement;
3. task-difficulty-adjusted, leave-one-task-out receiver capability;
4. a reliability gate before interpreting capability gradients;
5. a common-support task panel so receiver strata face identical agent outcomes;
6. executable agent states on the same tasks;
7. matched accounting of Beneficial Autonomy, Harmful Displacement, Net Routing Value, and Recovery Suppression;
8. paired task-bootstrap uncertainty;
9. prospective reuse on a second agent family without changing receiver definitions.

## Current search result

A targeted current search found substantial prior art for expert-specific routing, sequential intervention, capacity constraints, post-routing advice, and multi-stage Human–AI collaboration. It did **not** surface a canonical L2D benchmark whose central empirical variable is the same real human's measured ability to recover over repeated attempts and the share of that observed recovery capacity suppressed by autonomous routing.

This is **not** a priority claim. It is a provisional literature gap and must be re-audited before submission using broader scholarly databases and citation chaining.
