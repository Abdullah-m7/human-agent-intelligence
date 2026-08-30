# Stage 005 — Verifier-Bounded Program Synthesis

Status: **PASS / CALIBRATION COMPLETE**

Controller verdict: **READY_FOR_COGARC_CONTROLLER_LOCK**

Frozen compute pair: **B1 vs B8**

CogARC status: **SEALED — NO COGARC INFERENCE AUTHORIZED BY THIS RESULT**

## Scientific question

Within one fixed Gemma-4-26B-A4B Q4_K_M program-synthesis agent, does additional
inference/search compute improve standalone capability while expanding verifier-bounded
autonomy, and what is the quality of the newly autonomous cases?

This calibration is agent-only. It does not measure Human+Agent performance, does not
establish ATPI, and does not authorize a CogARC confirmatory run.

## Frozen contract and integrity

- Contract commit: `fa9f83c12b8c070e4799636f68ce35ab21118e33`.
- Calibration set: 60 mechanically selected ARC-AGI-1 training tasks.
- All 75 CogARC IDs were excluded before selection; no CogARC payload was used.
- Candidate sequence: eight literal nested candidates per task, yielding 480/480 rows.
- All 480 `(task_id, candidate_index)` keys are unique and carry the same contract commit.
- Model SHA256: `b8707e57f676d8dd1b80f623b45200cc92e6966b0e95275e606f412095a49fde`.
- Split SHA256: `a7ec05d44d72c3c0d07a325f926d4730bf0567b3e67435d3fc87dd0a3cf5d2e8`.
- ARC source commit: `399030444e0ab0cc8b4e199870fb20b863846f34`.
- The invalidated 72-row run under context 8192 was not mixed with this run.
- The runner used context 16384, temperature 0.8, top-p 0.95, 1536 completion
  tokens, the fixed candidate seeds, frozen ranking, and the frozen sandbox.
- The frozen endpoint is `test[0]`. Two calibration tasks contain an additional test
  query, so the primary accuracy below is target-0 accuracy rather than whole-task ARC
  accuracy. This endpoint was not redefined after calibration began.
- 84 project tests under `tests/` pass, including adversarial sandbox, split, nested-budget,
  selection, marginal-autonomy, and ambiguity tests.

## Primary calibration results

| Budget | Standalone accuracy | ACT coverage | ACT precision | Unsafe autonomy mass | Valid candidate rate | Mean best train fit |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 11/60 = 18.33% | 10/60 = 16.67% | 9/10 = 90.00% | 1/60 = 1.67% | 36.67% | 18.61% |
| B2 | 16/60 = 26.67% | 16/60 = 26.67% | 15/16 = 93.75% | 1/60 = 1.67% | 37.50% | 27.74% |
| B4 | 22/60 = 36.67% | 23/60 = 38.33% | 22/23 = 95.65% | 1/60 = 1.67% | 37.50% | 38.99% |
| B8 | 25/60 = 41.67% | 26/60 = 43.33% | 25/26 = 96.15% | 1/60 = 1.67% | 37.29% | 44.08% |

From B1 to B8, capability increased by 23.33 percentage points and ACT coverage
increased by 26.67 points. The paired task transitions contain 14 capability gains and
zero capability losses (exact two-sided McNemar/binomial p = 0.000122, descriptive;
this test was not a selection input). ACT gained 16 tasks and lost none.

The valid-program rate stayed near 37% at every prefix. Search compute therefore did
not make an individual draw more likely to be valid; it accumulated additional chances
to find a train-consistent program.

## Marginal autonomy quality

`NEW_AUTONOMY` is exactly `DEFER -> ACT` at each adjacent transition.

| Transition | New autonomous tasks | New-autonomy precision | Delta capability | Delta ACT coverage | Delta UAM |
|---|---:|---:|---:|---:|---:|
| B1 -> B2 | 6 | 6/6 = 100% | +8.33 pp | +10.00 pp | 0.00 pp |
| B2 -> B4 | 7 | 7/7 = 100% | +10.00 pp | +11.67 pp | 0.00 pp |
| B4 -> B8 | 3 | 3/3 = 100% | +5.00 pp | +5.00 pp | 0.00 pp |

All 16 newly autonomous tasks were correct. Because these counts are small, the result
must not be described as proof of perfect marginal reliability: the pooled 16/16 Wilson
95% interval is approximately 80.6%–100%, and the B4 -> B8 transition alone has only
three cases (Wilson lower bound approximately 43.9%).

The unsafe autonomous task was already autonomous at B1 and remained selected at every
budget. Under the frozen `train fit, then earliest candidate` ranking, a later
train-perfect program cannot displace an earlier train-perfect program. Thus added
compute expanded the autonomy boundary but could not repair an already certified error.

## Verifier-consistent program ambiguity

- 26/60 tasks had at least one certified program by B8.
- 22/60 had multiple certified programs.
- 3/22 multi-certified tasks had more than one target prediction: 13.64% conditional
  disagreement (`dc1df850`, `694f12f3`, `a79310a0`).
- In all three disagreement cases, the frozen earliest-candidate ranking selected a
  correct target prediction, while at least one later certified program was wrong.
- The sole unsafe autonomous task, `60b61512`, is the stronger warning: five distinct
  certified programs produced one unanimous target prediction, and all five were wrong.

Therefore visible-train consistency can leave target behavior underspecified, but
agreement across independently sampled train-consistent programs is not sufficient
evidence of correctness either. Disagreement is a useful diagnostic, not a complete
autonomy gate. This ambiguity analysis is explicitly post-calibration descriptive and
was not used to select the compute pair or alter ACT.

## Operational behavior

Of 480 model responses, 179 produced valid executable programs (37.29%). The largest
failure categories were invalid output grids (190), syntax errors (49), forbidden
lambdas (27), and response parse failures (24). There were two safe execution timeouts.
The completion endpoint stopped by length for 283/480 responses and by normal stop for
197/480. These failures were scored as wrong standalone predictions as frozen.

## Frozen compute-pair selection

The preregistered selector may use only standalone accuracy and ACT coverage. It found
that B8 is strictly higher than B1 on both:

- standalone accuracy: 18.33% -> 41.67%;
- ACT coverage: 16.67% -> 43.33%;
- both coverages exceed 10%;
- B1 vs B8 has the largest allowed compute separation.

The selector did not use UAM, ACT precision, marginal precision, ambiguity, a desired
inversion, or Human+Agent outcomes. Its machine-readable verdict is `PAIR_SELECTED`.
Accordingly the Stage 005 Controller verdict is:

**READY_FOR_COGARC_CONTROLLER_LOCK — B1 vs B8.**

## Interpretation and boundary of the claim

On this independent calibration set, added search compute improved capability and
expanded autonomy without degrading the observed quality of newly autonomous cases.
This is not an Autonomy–Team Performance Inversion: no human receiver outcome was
observed here. It is evidence that this particular verifier-bounded compute ladder is
operationally viable for a separately locked confirmatory Human+Agent experiment.

The confirmatory lock must preserve the model, prompts, candidate sequence, seeds,
sandbox, ranking, ACT rule, B1/B8 pair, and target endpoint. It must not use the
calibration UAM, marginal precision, ambiguity pattern, or desired ATPI outcome to
change routing or select another pair. CogARC remains sealed pending that separate
Controller lock and review.

## Machine-readable artifacts

- `results/stage005_program_synthesis/calibration/candidates.jsonl`
- `results/stage005_program_synthesis/calibration/rows.jsonl`
- `results/stage005_program_synthesis/calibration/summary.json`
- `results/stage005_program_synthesis/calibration/provenance.json`
- `results/stage005_program_synthesis/calibration/marginal_autonomy.json`
- `results/stage005_program_synthesis/calibration/compute_selection.json`
- `results/stage005_program_synthesis/calibration/program_ambiguity.json`
