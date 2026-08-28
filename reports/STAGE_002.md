# Stage 002 — Robustness and Independent Validation

Date: 2026-08-28

## Controller decision

**STAGE 002: PASS AS A RESEARCH-INTEGRITY / ROBUSTNESS STAGE**

**Paper 01 empirical publication claim: HOLD** — computational role migration is robust to additional model classes, but a real agentic benchmark remains required.

**Paper 02 generic susceptibility claim: HOLD / REFRAME** — Validation V1 failed; HAIID is retained as a context-dependent discovery, not a universal mechanism.

## Paper 01 — Agentic Bottleneck robustness

Stage 002 relaxed two Stage-001 assumptions:

1. human and agent task errors need not be independent;
2. human review can be confidence-selective rather than a random autonomy mixture.

The Role Migration pattern survived both changes: as effective autonomy rises, sensitivity to human fallback / verification declines while the relative contribution of upstream specification persists or increases.

Important correction: the Stage-001 `34.8%` review-harm fraction is **not universal**. Under correlated errors it ranged from roughly `29%` to `46%`; under asymmetric difficulty / selective-review regimes it varied approximately `24%–46%`. The publishable object is therefore a **regime boundary**, not a single prevalence number.

## Paper 02 — Locked independent validation

Validation V1 used the open CSCW 2023 loan-decision dataset after a pre-result lock and pre-result executable analysis commit.

Primary result:

- H1 helpful susceptibility: `β=+0.0647`, p `0.3597` — opposite sign to prediction.
- H2 harmful susceptibility: `β=-0.0080`, p `0.9497` — approximately zero.
- selectivity interaction: `β=-0.0079`, p `0.9477`.

Registered verdict: **TWO_SIDED_SUSCEPTIBILITY_NOT_SUPPORTED**.

The result stayed failed under all pre-specified robustness analyses.

## Post-validation diagnostic

The capability construct itself was much less stable in CSCW than in HAIID:

- HAIID: median 32 AI-advice trials/person; split-half `r≈0.361`; Spearman–Brown `≈0.529`.
- CSCW: 10 trials/person; split-half `r≈0.046`; Spearman–Brown `≈0.080`.
- CSCW LOTO capability did not predict held-out initial correctness (`β≈0.041`, p `≈0.502`).

This cannot revise the locked failed verdict. It changes only the design requirement for Validation V2: stable capability measurement must be established independently before focal AI-reliance outcomes are inspected.

## Stage 002 scientific update

The program has learned two different things:

1. **Agentic role migration is robust within the current family of explicit computational models.**
2. **Capability-dependent advice susceptibility is not yet a general empirical law.** Its discovery signal is context-sensitive and may depend on the stability of the human-capability construct and on interface / communication regime.

This separation is valuable: Paper 01 and Paper 02 should no longer be treated as if they stand or fall together.

## Next gates

### Paper 01
Build a real task benchmark where the same underlying tasks are executed under controlled autonomy / review policies, so Role Migration is tested with actual agent outputs rather than only stylized probabilities.

### Paper 02
Audit untouched candidate datasets for a stable or direct human-capability measure **before** outcome inspection. Lock Validation V2 eligibility and analysis before calculating focal susceptibility effects.

### Paper 06
`Does Your IQ Affect Your Agent?` remains HOLD. Neither task accuracy nor CRT may be relabeled as IQ.
