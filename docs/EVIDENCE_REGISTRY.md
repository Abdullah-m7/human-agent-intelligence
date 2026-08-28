# Evidence Registry — Stage 001

Last updated: 2026-08-28

This registry separates **what a source actually measures** from what the program would like to infer. It is intentionally conservative about IQ, intelligence, expertise, cognitive reflection, and metacognition.

| Source | Evidence | Human construct actually measured | Open individual data? | Stage 001 use | Decision |
|---|---|---|---|---|---|
| Vaccaro, Almaatouq & Malone, *Nature Human Behaviour* (2024), `10.1038/s41562-024-02024-1` | Meta-analysis: 106 experiments / 370 effects | participant type/expertise at study level; human, AI and human+AI performance | Open OSF data + R code | Downloaded and schema-audited | **Background / meta scaffold.** Strict same-study expert/non-expert matching is too sparse to support Paper 02 alone. |
| Vodrahalli et al., AIES (2022), `10.1145/3514094.3534150` | 35,670 human–advice interactions; 1,125 participants | initial task performance, initial confidence, demographics; expert tenure for dermatologists | Yes, MIT GitHub repo | **Discovery dataset.** AI-advice subset: 17,973 rows / 567 participants | **High value.** Supports cross-fitted task capability and advice-susceptibility analysis. Does **not** measure IQ. |
| Himmelstein et al., *Journal of Behavioral Decision Making* (2023), `10.1002/bdm.2285` | Study 2: 171 people × 15 forecasts = 2,565 judge-advisor trials with Human/Algorithm/Hybrid advice | **7-item Cognitive Reflection Test (CRT)**, forecasting performance, advice revision | Yes, OSF `xuagt`; data, codebooks and R code | Direct-cognitive-measure discovery route; algorithm-only subset = 855 trials | **High value but exploratory.** Original authors already included CRT as a covariate, so generic `CRT → advice use` is not novel. Our narrower candidate is cognitive reflection and *final integration quality conditional on constituent quality*. CRT is not IQ. |
| Soleimanof & Neufeld, *Decision Support Systems* (online 2026-08-22), `10.1016/j.dss.2026.114757` | Behavioral experiment, N=440 | confidence / retrospective confidence / metacognitive sensitivity | Yes, OSF `ybksv`; original `Dataset.xlsx` inspected | Candidate independent validation; raw workbook has 440 rows / 23 fields | **High priority validation candidate.** Task semantics and scoring must be reconstructed from materials before any confirmatory test. |
| Taudien et al., ICIS (2024), *Know Thyself: The Relationship between Metacognition and Human-AI Collaboration* | Exploratory experiment, n=51 | metacognitive efficiency + individual performance | To audit | Novelty competitor | **Must cite.** Already links higher individual performance, metacognition, and collaborative benefit; prevents a broad novelty claim on that interaction. |
| Riedl & Weidmann, PsyArXiv v3 (2026) | Human–AI collaboration study, n=667 | individual ability, collaborative ability, Theory of Mind | To audit | Novelty boundary / candidate replication | **Must cite.** Explicitly separates individual and collaborative ability. |
| Noy & Zhang, *Science* (2023), `10.1126/science.adh2586` | Randomized professional-writing experiment, n=453 | baseline writing performance/skill | Study-level results | Directional precedent | Lower performers benefiting more is **not novel** by itself. |
| Brynjolfsson, Li & Raymond, *QJE* (2025) | Large field study of customer-support AI | experience / baseline worker skill | Access restrictions likely | Directional precedent | Larger gains for novice/lower-skill workers are **not novel** by themselves. |
| Dell'Acqua et al., *Organization Science* (2026) | Randomized knowledge-work experiment, n=758 | task performance / behavior around jagged AI frontier | To audit | Task-frontier precedent | Use to motivate task dependence; do not equate frontier navigation with IQ. |
| Bigoni et al., arXiv (2025) | Review / conceptual synthesis | cognitive differences | N/A | Naming / novelty boundary | Phrase **Equalizer or Amplifier** is occupied; do not claim it as our framing. |
| Mitchell, Ghosh & Passi, arXiv:2608.23642 (2026-08-24) | Position paper on agents and human oversight | cognitive requirements of oversight / skill atrophy | N/A | Closest current conceptual competitor | **Must cite.** Generic claim that agent autonomy can undermine human oversight is occupied. |
| Data & Society, *The Oversight Fallacy* (2026) | Qualitative/field-based analysis of agent oversight | ability to recognize and intervene on agent mistakes | Not a quantitative microdataset | Oversight theory | Supports the need to operationalize receiver/overseer competence; not evidence for IQ effects. |
| Anthropic, *Measuring AI agent autonomy in practice* (2026) | Millions of privacy-preserved real-world agent interactions | user-granted autonomy / interaction duration | Aggregated only | Autonomy construct | Supports treating autonomy as a measurable continuum; raw data not available for our reanalysis. |

## Open-data assets pinned in Stage 001

### HAIID

- Source: `https://github.com/kailas-v/human-ai-interactions`
- File: `haiid_dataset.csv`
- Observed SHA-256: `be9223b6bf34f996cdace9b1c0d43876df0e480bcb9322e6a7f774de0f2f0eed`
- License: MIT repository license at inspection time.
- Reproducible fetch: `python scripts/fetch_external_data.py haiid`

### Vaccaro et al. meta-analysis

- OSF project: `https://osf.io/wrq7c/?view_only=b9e1e86079c048b4bfb03bee6966e560`
- `Data_Extraction.csv` SHA-256: `9584f9a27a32c567f4763f94ec2fce0434ea3bf2233f74d49a1b0d3f26674b0b`
- `AnalysisScript_Final.Rmd` SHA-256: `e66ec93f15af34b27383f75e3ba58419b206e21dc3f2613ee53730cbc089697e`
- Reproducible fetch: `python scripts/fetch_external_data.py vaccaro_data vaccaro_code`

### Himmelstein et al. forecasting Study 2

- OSF project: `https://osf.io/xuagt/`
- `Study 2 JAS Data.csv` SHA-256: `1162176e18c8414d9b51f71cfd3b61fd4755c321d7d82725c050c3cad3abf77f`
- `Study 2 demographics and scales.csv` SHA-256: `0e8bb7336c8f8252c04806f2ab745428202e0a6841d94746ec77d3e99814ede2`
- `Study 2 Codebook.xlsx` SHA-256: `c81c329baa9dcb83588ea47bfbf8c4730dcb1f65d009e9afa9ec166caa4d82ea`
- Structure verified: `171` participants, `15` forecasts each, `CRTsc` ranges `0–7`.
- Reproducible fetch: `python scripts/fetch_external_data.py himmelstein_study2_jas himmelstein_study2_demographics himmelstein_study2_codebook`

### Soleimanof & Neufeld 2026 candidate validation dataset

- OSF project: `https://osf.io/ybksv/?view_only=0c9d07bac94d4a1089588f647db735a0`
- File: `Dataset.xlsx`
- Observed rows/columns: `440 × 23`
- Observed SHA-256: `660e35ae12c39823838ca2729b43362244cc9c8271aa543baa9ae9dc90d69388`
- Reproducible fetch: `python scripts/fetch_external_data.py soleimanof_neufeld_2026`
- Status: schema inspected only; **no result claim yet** because task coding must be reconstructed from study materials.

## Construct rules arising from the audit

1. `baseline task accuracy` is a measure of **task capability**, not IQ.
2. `education` is education, not an intelligence proxy.
3. `years of experience` is expertise/tenure, not general cognitive ability.
4. `confidence` is not metacognitive sensitivity; sensitivity requires a relation between confidence and correctness across judgments.
5. Advice resistance is not automatically verification skill. A person who rejects both correct and incorrect advice can show high resistance without high discrimination.
6. A CRT score is a direct measure of **cognitive reflection**, not an IQ score and not a general-intelligence estimate.
7. The label `IQ` is reserved for data containing a defensible IQ/general-cognitive-ability instrument; no Stage 001 dataset currently satisfies that requirement.

## Stage 002 additions

### He, Buijsman & Gadiraju — CSCW 2023

- Paper DOI: `10.1145/3610067`
- Open-data DOI: `10.4121/F211863D-331B-44E5-A184-C21A18AC831A`
- Main-study sample reconstructed using authors' released exclusion logic: `281` participants × `10` trials = `2,810` trials.
- Conditions: system `87`, accuracy `92`, analogy `102`.
- Locked validation commit: `a51913e1920b5a45aaeea9f3dbb50afb6688a426`.
- Analysis-plan executable committed before focal coefficients: `811d3755a02c2aa561bc4af74ec8c15559c62d86`.
- Validation verdict: **TWO_SIDED_SUSCEPTIBILITY_NOT_SUPPORTED**.
- H1 helpful capability coefficient: `+0.0647`, p `0.3597`.
- H2 harmful capability coefficient: `-0.0080`, p `0.9497`.
- Post-validation measurement diagnostic: mean split-half Spearman–Brown reliability of the 10-item capability construct ≈ `0.08`; LOTO capability did not predict focal initial correctness (`p≈0.50`).
- Interpretive rule: failed validation remains failed; low reliability is a diagnostic and a design requirement for V2, not a retroactive exclusion.
