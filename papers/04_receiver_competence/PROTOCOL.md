# Paper 04 Protocol — Receiver Competence

## Working thesis

**Deferral is a contract, not a button.** Responsible deferral requires specifying not merely `AI → HUMAN`, but which human receiver, what evidence/state is transferred, and what effort or retry budget the receiver receives.

## Central question

What properties must a human receiver have for agent deferral to reduce residual risk on the task being returned?

## Constructs

- `Task capability`: stable unaided performance estimated from disjoint tasks.
- `First-pass capability`: probability of solving on the first submission.
- `Recovery capability`: probability of eventual success conditional on an initial failure.
- `Receiver uncertainty`: uncertainty in the estimate of the human's capability from prior observations.
- `Agent residual`: the region of tasks left after an ACT policy keeps some tasks autonomous.
- `Receiver value`: improvement in joint performance attributable to handing the residual to that receiver.

None of these constructs is labeled IQ unless a direct general-cognitive-ability instrument is available.

## Hypotheses for a future lock

H1. Receiver value depends on the interaction between receiver capability and the agent's residual task distribution, not only on the receiver's global accuracy.

H2. Increasing autonomous coverage reduces the absolute contribution of human capability only when the newly autonomous region is sufficiently reliable.

H3. An autonomy expansion that has lower conditional correctness than the human residual receiver can reduce joint performance even while standalone agent accuracy rises.

H4. A retry-enabled receiver can dominate a one-shot receiver even at the same first-pass capability, making recovery capacity a distinct deferral resource.

## Stage-003 evidence role

CogARC is used as discovery because it provides dense repeated human reasoning outcomes and multiple attempts. A public ARC solver provides a machine capability ladder on the same 75 tasks. All headline causal/general claims remain HOLD until replicated with at least one substantially different agent family and a pre-locked routing policy.

## Intended comparison set

- AI only;
- random eligible receiver;
- highest measured global-capability receiver;
- receiver selected by residual-task fit;
- capability-uncertainty-aware routing;
- oracle complement upper bound.

Specific-expert routing is established prior art; any paper must show a contribution beyond merely selecting among multiple humans.
