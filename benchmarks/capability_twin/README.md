# Human–Agent Capability Twin Benchmark

## Thesis

The benchmark asks a stronger question than whether a human or an AI is more accurate:

> **How does the value of a human receiver change as an agent becomes more capable and more willing to act?**

A human–agent system is represented on the *same underlying reasoning tasks*. Human outcomes are archival real behavior, not LLM personas. Agent outputs come from executable solvers. Human capability is estimated only from task behavior that is disjoint from the tasks on which joint-system value is evaluated.

## Why CogARC is the foundation

CogARC Experiment 2 provides a dense person × item matrix after its official inclusion rules: 12,138 analyzed trials, 199 people, and 75 ARC tasks. Most participants solve many shared items, which allows human capability to be measured with much greater stability than the short advice-taking datasets used in Stage 002.

The benchmark does **not** call this capability IQ. ARC accuracy is task-specific abstract-reasoning performance.

## Human receiver states

The first benchmark release distinguishes at least two receiver contracts:

- `ONE_SHOT`: the human gets one submission opportunity;
- `RETRY3`: the human can recover over the experiment's allowed attempts.

Later versions may add effort/time cost, error-family profiles, and trajectory-derived recovery state.

## Agent states

An agent adapter must emit, per task:

- final correctness under the benchmark's scoring rule;
- whether the agent elects to ACT or has no usable solution;
- an internal evidence/confidence descriptor that was available before ground-truth inspection;
- provenance: solver version, taskset version, configuration and cost if relevant.

The Stage-003 proof-of-concept uses a public deterministic ARC solver with nested detector prefixes as a capability ladder. This is a discovery instrument, not a claim that detector count is a general model-scaling law.

## Core policies

### AI_ONLY
The agent always owns the decision; inability to produce a valid candidate counts as failure.

### STRUCTURAL_ACT_DEFER
The agent ACTs when its internal solver finds at least one fitting transformation and otherwise DEFERs to the specified human receiver.

### REDUNDANCY_GATE
An experimental policy that requires multiple independent fitting paths before ACT. The exact `nfit >= 2` rule was post-hoc on CogARC and therefore receives separate external validation.

### ORACLE_COMPLEMENT
Choose a correct constituent whenever either the human or agent is correct. This is not deployable; it measures the maximum complementarity available in the pair.

## Primary quantities

### Human Leverage

`L = JointPerformance - AgentPerformance`

### Human Leverage Gradient

The slope of held-out human leverage against human capability measured on disjoint tasks. A falling gradient across agent capability levels means differences among human receivers matter less to the resulting system as the agent becomes more capable/autonomous.

### Unsafe Autonomy Mass

`U = P(ACT ∧ wrong)`

This is the fraction of the task distribution exposed to an incorrect autonomous action. It is reported together with ACT coverage and conditional ACT precision. It is not computed as `coverage - global accuracy`, because an agent may be correct on a task it would nevertheless choose to defer.

### Capability–Autonomy Gap

Raw agent capability and autonomous act coverage are separate axes. **Capability–Autonomy Gap** names a system-level mismatch in which standalone capability improves while the newly autonomous region is insufficiently reliable — observable, for example, as rising Unsafe Autonomy Mass and falling joint performance. It is a phenomenon across agent states, not a universal one-number score.

### Recovery Value

`RecoveryValue = Joint_RETRY3 - Joint_ONE_SHOT`

This measures the value of giving the human receiver a recovery budget rather than treating deferral as an instantaneous binary handoff.

## Leakage controls

1. Human capability is estimated from a task split disjoint from joint-system evaluation tasks.
2. Agent correctness on held-out tasks cannot enter the human capability estimate.
3. Post-hoc routing rules are labeled discovery and must be locked before external validation.
4. Task exclusions follow the source dataset's published inclusion metadata rather than outcome-driven project exclusions.
5. Results from one solver architecture are not generalized to LLM agents without replication.

## Novelty boundary

Multi-expert learning-to-defer already exists and includes methods that choose specific experts. This project therefore does **not** claim novelty for “routing to the best human.” The target contribution is a dense, psychometrically calibrated human–agent reasoning benchmark that separates human capability, recovery budget, agent capability, autonomous coverage, and calibration.

## Stage-003 discovery status

The initial CogARC + symbolic-solver run finds a large difference in human-measurement reliability relative to Stage-002 CSCW data and a cross-fitted attenuation of the Human Leverage Gradient as the machine ladder improves. It also produces a concrete capability–autonomy inversion at the highest solver prefix. These are discovery findings and require replication with additional agent families.
