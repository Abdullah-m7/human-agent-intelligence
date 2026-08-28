# Stage 003 — Human–Agent Capability Twin Foundation

Date: 2026-08-29

## Controller decision

**FOUNDATION / DISCOVERY: PASS**

**Paper 01 publication claim: HOLD** pending replication with a substantially different agent family.

**Paper 04 receiver-competence program: GO** for benchmark development.

**Paper 06 IQ claim: HOLD.** CogARC measures task-specific abstract-reasoning performance, not IQ.

## Why Stage 003 changed direction

Stage 002 showed that short advice-taking datasets can be too noisy to support a stable human-capability construct. Stage 003 therefore stops treating human capability as a weak side variable and builds a task-matched Human–Agent Capability Twin: archived real humans and executable agents are evaluated on the same underlying reasoning items.

The first foundation uses CogARC Experiment 2 and follows its own released `trial_inclusion.csv`. The manuscript analysis sample contains 12,138 analyzed trials from 199 people across 75 ARC tasks.

## Measurement gate

Human capability is unusually stable in this source relative to Stage 002:

- final success split-half mean: `r = 0.8084`;
- final success Spearman–Brown mean: `0.8939`;
- first-attempt success split-half mean: `r = 0.7736`;
- first-attempt Spearman–Brown mean: `0.8721`.

This clears the conceptual measurement failure that undermined CSCW Validation V1. It does not make ARC performance a general-intelligence score.

## Real machine proof-of-concept

A public local symbolic ARC solver (`tanmaybisen31/arc-agi-solver`, revision `e151937...`) was run on the same 75 tasks. Nested detector prefixes produced a machine ladder:

| Detectors | Standalone accuracy | Structural ACT coverage | ACT precision |
|---:|---:|---:|---:|
| 15 | 8.0% | 8.0% | 100% |
| 40 | 12.0% | 12.0% | 100% |
| 80 | 14.7% | 14.7% | 100% |
| 120 | 17.3% | 17.3% | 100% |
| 180 | 22.7% | 22.7% | 100% |
| 240 | 26.7% | 26.7% | 100% |
| 321 | 33.3% | 49.3% | 67.6% |

`ACT coverage` means at least one detector found a transformation reproducing all visible training demonstrations. Under the benchmark's structural policy, the solver ACTs on those tasks and DEFERs otherwise.

## Finding 1 — Human Leverage Curve

Human capability was measured on 37 tasks and joint-system value on the disjoint remaining 38 tasks, repeated over 300 random task splits. Only participants with at least 20 independent capability-estimation trials and 20 evaluation trials entered each split.

For a one-shot human receiver, the mean slope of human leverage against independently measured human ability fell from `0.7656` at the 15-detector machine level to `0.4432` at 321 detectors.

For a retry-enabled receiver, the corresponding slope fell from `0.8033` to `0.4617`.

This is discovery evidence that stronger/more autonomous machine systems can reduce how strongly variation in human capability determines joint performance. It is not yet a universal equalization law and is not an IQ result.

## Finding 2 — Capability–Autonomy Gap

The most important Stage-003 event occurs between the 240- and 321-detector solver configurations.

Standalone machine accuracy improves:

`26.7% → 33.3%`

But autonomous ACT coverage expands much faster:

`26.7% → 49.3%`

and ACT precision falls:

`100% → 67.6%`.

The corresponding **Unsafe Autonomy Mass**, `P(ACT ∧ wrong)`, rises from `0/75` to `12/75 = 16.0%`.

Under the same cross-fitted ACT/DEFER policy, this makes the team worse despite making the machine better:

- one-shot human joint performance: `75.69% → 67.68%`;
- retry-enabled human joint performance: `86.24% → 75.06%`.

Working construct:

**Capability–Autonomy Gap** = a mismatch across agent states in which standalone capability improves but reliability of the additional autonomous region does not keep pace. It should be characterized with separate observables — standalone accuracy, ACT coverage, ACT precision, Unsafe Autonomy Mass, and joint performance — rather than collapsed into `coverage - accuracy`.

The strong claim is not that adding detectors causes this universally. The publishable hypothesis is that **standalone capability and safe autonomous coverage are distinct axes, and optimizing the first can reduce joint-system performance when the second is miscalibrated.**

## Finding 3 — Deferral budget matters

Across every machine level, allowing the archival human receiver to use the experiment's retry process produces a materially stronger joint system than using first-attempt performance only. Deferral therefore has a receiver-effort dimension: a human is not a fixed scalar accuracy endpoint.

This motivates Paper 04's formulation: **Deferral is a contract, not a button.**

## Rejected Stage-003 idea

A candidate claim was that the best human partner might systematically differ from the highest-ability human because of agent-error complementarity. With this first solver, global human ability and human success specifically on agent-failed tasks were extremely highly correlated (`Spearman ρ ≈ 0.98` in dense participant subsets).

Therefore the simple claim **“the best partner is not the smartest human” is rejected as a Stage-003 headline**. More granular task-family specialization may be studied later, but no paper is built on the current rank exceptions.

## Redundancy autonomy gate

Post-hoc on CogARC, requiring `nfit >= 2` instead of `nfit >= 1` reduced the 321-detector ACT coverage from `49.3%` to `24.0%` and removed all 12 wrong autonomous acts in the 75-task discovery set. This was not pre-locked and is not confirmatory.

On ARC-AGI-2 training (1,000 tasks), an external diagnostic showed:

- `nfit >= 1`: coverage `46.9%`, ACT precision `72.3%`, 130 wrong acts;
- `nfit >= 2`: coverage `16.8%`, ACT precision `88.1%`, 20 wrong acts.

The exact rule was then locked in Git commit `a89dc69` before this project ran the ARC-AGI-2 evaluation split.

Locked evaluation result on 120 tasks:

- `nfit == 1`: 14 tasks, precision `7.1%`;
- `nfit >= 2`: 4 tasks, precision `25.0%`;
- one-sided Fisher `p = 0.405`;
- pre-registered verdict: **INCONCLUSIVE_LOW_COVERAGE** because only four evaluation tasks met the redundancy gate.

Thus evidence redundancy remains a promising engineering signal, not a validated general law.

## Novelty boundary

Stage 003 does **not** claim that choosing among multiple human experts is new. Multi-expert learning-to-defer and learning-to-complement already route cases to specific experts and optimize cost/coverage.

Stage 003 also does **not** claim that applying IRT to ARC human data is new; H-ARC has already used a Bayesian Rasch-style model for latent participant ability and task difficulty.

The target novelty is narrower:

1. a dense human–agent reasoning benchmark in which human receiver capability is independently measurable;
2. explicit separation of standalone agent capability from autonomous act coverage and act precision;
3. the Human Leverage Curve across machine capability/autonomy levels;
4. a receiver contract that distinguishes first-pass capability from recovery capability;
5. direct testing of whether a stronger standalone agent can create a weaker joint system through autonomy miscalibration.

## Next gates

1. Replicate the Capability–Autonomy Gap with a fundamentally different agent family; the symbolic detector ladder alone cannot support publication.
2. Add a standardized Agent Adapter so LLM/program-synthesis/interactive agents emit a common task state and confidence/evidence record.
3. Audit ARCTraj and H-ARC as secondary human sources. H-ARC is broad but sparse per participant; CogARC remains the primary psychometric panel unless another dense dataset clears reliability.
4. Use ARC-AGI-3 public human replays as a candidate genuinely interactive agentic validation layer; its structure is closer to autonomous exploration than static ARC grids.
5. Do not reopen Paper 06 until a direct general-cognitive-ability measure is available.
