# Stage 004 — Novelty Boundary Audit

Date: 2026-08-29

## Controller conclusion

The project must **not** claim novelty for separating agent capability from agent autonomy, for observing that human–AI teams can underperform their constituents, for using abstention/deferral to control autonomous coverage, or for the generic statement that an optimal deferral policy depends on the receiving human expert. Those ideas have clear prior art.

The defensible target is narrower: a task-matched, psychometrically grounded empirical test of whether an *improvement in standalone agent capability* can coincide with *an increase in unsafe autonomous task mass* and thereby *decrease human–agent joint performance*, under a precommitted ACT/DEFER rule. A second methodological contribution may be an explicit routing-transition decomposition on a dense real-human panel, but the algebra behind comparing model and expert value is not claimed as new theory.

## Closest prior art that constrains our claims

### 1. Capability and autonomy as separate axes is not new

Kevin Feng, David McDonald, and Amy Zhang, **Levels of Autonomy for AI Agents** (2025), explicitly argue that autonomy is a deliberate design variable that can be varied independently of capability. Their framework describes user roles across escalating autonomy levels and proposes autonomy certificates.

Source: https://knightcolumbia.org/content/levels-of-autonomy-for-ai-agents-1

### 2. A named Capability–Autonomy legal framework now exists

Dawn Kim, **The Capability-Autonomy Framework: A Structure for the Legal Governance of Artificial Intelligence** (SSRN, posted 3 August 2026), explicitly organizes AI governance around capability and autonomy as distinct dimensions and argues that law has more direct purchase on autonomy than raw capability.

Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7139638

This creates a naming collision risk with our Stage-003 working phrase **Capability–Autonomy Gap**. We should not present that phrase as if the capability/autonomy distinction itself were our theoretical invention.

### 3. Capability greater than exercised autonomy already has an “overhang” framing

Anthropic, **Measuring AI agent autonomy in practice** (18 February 2026), compares capability assessments with deployed autonomy and describes a **deployment overhang** in which models appear able to handle more autonomy than they exercise in practice.

Source: https://www.anthropic.com/research/measuring-agent-autonomy

Our empirical concern is potentially the opposite regime: autonomous scope expanding beyond the region supported by reliable task performance. We should distinguish this from Anthropic's deployment-overhang framing rather than reuse “overhang” language loosely.

### 4. Autonomy coverage under safety constraints has direct technical prior art

Kolluri et al., **Optimizing Agent Planning for Security and Autonomy** (ICLR 2026), introduce autonomy metrics measuring the fraction of consequential actions an agent can execute without human approval while preserving security, and evaluate designs that increase autonomy without sacrificing utility.

Source: https://www.microsoft.com/en-us/research/publication/optimizing-agent-planning-for-security-and-autonomy/

Therefore ACT coverage / human-intervention reduction alone is not a novel metric family.

### 5. “Better AI is not sufficient for better teaming” is already a general conclusion

Recent Human–AI teaming reviews explicitly note that stronger individual AI performance does not guarantee superior team performance; interaction protocol, delegation, trust calibration, and coordination can dominate the team outcome.

Examples:

- *From testbeds to high-stakes work: a review of Human-AI teaming domains and teaming factors* (2026): https://pmc.ncbi.nlm.nih.gov/articles/PMC13189778/
- *AI-teaming: Redefining collaboration in the digital era*: https://doi.org/10.1016/j.copsyc.2024.101837

Thus the paper cannot sell the generic statement “a better AI can make a worse team” as an unqualified conceptual first.

### 6. Expert-relative deferral is already central to Learning-to-Defer

Learning-to-Defer (L2D) explicitly routes instances between a model and a human expert based on their relative capabilities. Prior work already models individual expert capability, adapts to changing or unseen experts, and learns to defer to a population of experts.

Examples:

- Hemmer et al., **Learning to Defer with Limited Expert Predictions**, AAAI 2023: https://doi.org/10.1609/aaai.v37i5.25742
- Tailor et al., **Learning to Defer to a Population: A Meta-Learning Approach**, AISTATS 2024: https://proceedings.mlr.press/v238/tailor24a.html
- Wei, Cao & Feng, **Exploiting Human-AI Dependence for Learning to Defer**, ICML 2024: https://proceedings.mlr.press/v235/wei24a.html
- Strong et al., **Expert-Agnostic Learning to Defer** (2025): https://arxiv.org/abs/2502.10533

Therefore we must **not** claim that “the appropriate autonomy level depends on which human receives the deferral” is itself new.

What may be distinctive in this program is the empirical measurement regime: a dense panel of archived real humans solving the *same reasoning items* as executable agents, stable independent estimates of receiver capability, multiple receiver-effort contracts, and a cross-state decomposition showing exactly where a change in autonomous scope displaces human performance. The Stage-004 routing-transition identity is used as an auditable accounting tool, not advertised as a new Bayes-optimal deferral theorem.

## Narrow target contribution

The Stage-004 target is an operational **cross-state inversion**, not a broad framework claim.

For two agent states ordered *before confirmatory evaluation* as WEAK and STRONG, define a replication event only when the sealed evaluation shows:

1. `Accuracy_STRONG > Accuracy_WEAK`;
2. `UnsafeAutonomyMass_STRONG > UnsafeAutonomyMass_WEAK`;
3. `Joint_ONE_SHOT_STRONG < Joint_ONE_SHOT_WEAK`.

where:

`UnsafeAutonomyMass = P(ACT ∧ wrong)`.

The scientific question is whether capability improvement is accompanied by a change in the *quality of the newly autonomous region* large enough to reverse the expected direction of joint-system performance.

This is more specific than confidence miscalibration, selective prediction, or a generic human–AI complementarity claim because the unit of comparison is a preregistered change in agent state on the same task distribution, with an explicit autonomous-action policy and an archived human receiver measured on those same tasks.

## Routing-transition decomposition

For an archived human success rate `H`, agent correctness `C`, and ACT indicator `A`, joint correctness can be written as:

`J = E[H] + E[A(C-H)]`.

Stage 004 decomposes `ΔJ` between WEAK and STRONG into four routing-transition regions:

1. both DEFER;
2. both ACT;
3. WEAK:DEFER → STRONG:ACT (**new strong autonomy**);
4. WEAK:ACT → STRONG:DEFER (**strong retrenchment**).

The contribution from region 3 is called the **autonomy displacement term** internally: on newly autonomous tasks, it measures whether STRONG replaces a human receiver with a better or worse expected outcome. This term is an exact descriptive accounting contribution, not a causal effect estimate and not claimed as an unprecedented theoretical identity.

The value of including it is diagnostic: if an ATPI occurs, the project can state *where the team loss came from* instead of inferring a mechanism from aggregate accuracy alone.

## Naming recommendation

Keep **Capability–Autonomy Gap** as a historical/internal Stage-003 working label only until the replication is complete.

If the effect replicates, the paper should consider the narrower empirical name:

**Autonomy–Team Performance Inversion (ATPI)**

Operational meaning: a transition between ordered agent states in which standalone capability improves while autonomy-associated error mass rises enough that human–agent joint performance falls.

A current exact-phrase search found no obvious established use of “Autonomy–Team Performance Inversion,” but the project should still treat the name as provisional until the final literature search immediately before submission.

If Stage 004 does not replicate the effect, do not promote ATPI as an established phenomenon; report the Stage-003 inversion as architecture-specific discovery evidence.

## What may still be novel even under a negative replication

The **Human–Agent Capability Twin** benchmark design may remain independently valuable because it combines:

- dense archived real-human behavior on the same reasoning items as executable agents;
- independently measurable human receiver capability;
- separate ONE_SHOT and recovery-enabled receiver contracts;
- standalone agent accuracy, ACT coverage, ACT precision, and Unsafe Autonomy Mass;
- task-balanced and participant-weighted joint-system evaluation;
- an outcome-blind executable model-selection rule;
- exact routing-transition accounting for how additional autonomy displaces the human receiver;
- a sealed evaluation protocol that prevents choosing the agent pair from the desired team outcome.

This benchmark contribution should be evaluated separately from whether the Stage-003 inversion generalizes.
