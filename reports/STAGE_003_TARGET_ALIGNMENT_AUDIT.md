# Stage 003 Target-Alignment Audit

## Controller finding

**PASS — numerical results unchanged after correcting the machine evaluation unit to the CogARC participant-visible target.**

## Why this audit was necessary

The 75 CogARC source task JSONs preserve original ARC task structure. Two tasks contain two test queries:

- `6ea4a07e`
- `d5d6de2d`

CogARC behavioral records, however, contain one submitted grid per participant/task. For both multi-query source tasks, the repository's canonical `Common solutions/<task>_Success.json` grid exactly matches `Task JSONs/<task>.json -> test[0].output` and does **not** match `test[1].output`.

Therefore the comparable Human↔Agent unit is the participant-visible target `test[0]`, not “all original ARC test queries.”

## Correction

`analysis/cogarc_capability_twin_poc.py::task_dict` now exposes only `test[0]` to the machine benchmark. Stage 004 uses the same target definition.

No human outcome, inclusion rule, ACT rule, detector ordering, or cross-fitting rule changed.

## Independent recomputation

The complete Stage-003 machine ladder and 300-seed cross-fit were recomputed using only `test[0]` for all 75 tasks.

The published Stage-003 numbers were **identical**:

| detectors | standalone | ACT coverage | ACT precision | wrong ACTs |
|---:|---:|---:|---:|---:|
| 15 | 0.0800 | 0.0800 | 1.0000 | 0 |
| 40 | 0.1200 | 0.1200 | 1.0000 | 0 |
| 80 | 0.1467 | 0.1467 | 1.0000 | 0 |
| 120 | 0.1733 | 0.1733 | 1.0000 | 0 |
| 180 | 0.2267 | 0.2267 | 1.0000 | 0 |
| 240 | 0.2667 | 0.2667 | 1.0000 | 0 |
| 321 | 0.3333 | 0.4933 | 0.6757 | 12 |

The key 240→321 team inversion also remained identical:

- ONE_SHOT joint performance: `0.756929 -> 0.676805`
- RETRY3 joint performance: `0.862416 -> 0.750599`
- Unsafe autonomous acts: `0 -> 12`

## Interpretation

This audit removes an avoidable unit-of-analysis ambiguity without rescuing or weakening the discovery. The Capability–Autonomy Gap survives the stricter Human↔Agent target alignment exactly.
