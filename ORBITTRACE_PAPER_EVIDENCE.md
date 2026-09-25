# OrbitTrace recurrent-EOM — paper-facing evidence summary

## Bottom line

**Selected paper method: recurrent-EOM HDBSCAN v1.**

The method modifies only HDBSCAN's EOM cluster-selection objective so that a hierarchy branch is rewarded only to the extent that its normalized excess-of-mass persists in **both** observing years. It uses the same pooled events, GEO6 representation, HDBSCAN parameters, hierarchy and condensation as ordinary HDBSCAN EOM.

For condensed-tree node `C` and year `y`, recurrent-EOM computes normalized annual excess of mass `E_y(C)` and replaces ordinary total stability in the standard EOM parent-versus-children optimization with:

`E_rec(C) = min(E_2022(C), E_2023(C))`.

This is an extraction-objective change inside HDBSCAN, not a post-clustering recurrence filter or tuned reranker.

Exact selected kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

## 🟢 Target-excluded GMN development — PASS

Binding run `31827903547`; artifact `9229646556`; artifact digest `sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6d`; result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`.

Exact verdict:

`PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`

The pooled target-excluded development corpus contained 315,024 GMN 2022 events and 423,658 GMN 2023 events. Ordinary EOM produced 2,131 candidate clusters; recurrent-EOM produced 2,097, with an active extraction mechanism.

| Year | Metric | Ordinary EOM | recurrent-EOM | Direction |
|---|---|---:|---:|---|
| 2022 | recovered @25 | 23 | 22 | reporting-only decrease |
| 2022 | recovered @50 | 45 | 45 | tie |
| 2022 | recovered @100 | 88 | **89** | improvement |
| 2022 | recovered @500 | 184 | **193** | improvement |
| 2022 | top-100 dominant precision | 0.779025 | **0.785649** | improvement |
| 2022 | MRR | 0.022388 | **0.022498** | improvement |
| 2022 | full-catalogue qualified | 238 | 236 | reporting-only decrease |
| 2022 | median top-500 fragmentation | 1.0 | 1.0 | tie |
| 2023 | recovered @25 | 21 | **23** | improvement |
| 2023 | recovered @50 | 44 | **46** | improvement |
| 2023 | recovered @100 | 89 | 89 | tie |
| 2023 | recovered @500 | 190 | **192** | improvement |
| 2023 | top-100 dominant precision | 0.773418 | **0.786768** | improvement |
| 2023 | MRR | 0.021199 | **0.022024** | improvement |
| 2023 | full-catalogue qualified | 247 | 244 | reporting-only decrease |
| 2023 | median top-500 fragmentation | 1.0 | 1.0 | tie |

The preregistered gate required strict @100 improvement in at least one year plus no regression at @50/@100, top-100 precision, MRR or fragmentation. Every binding gate passed.

**Paper interpretation:** recurrent-EOM improves the fixed-budget ranking/recovery behavior the study was designed to prioritize, while not uniformly increasing every catalogue-wide reporting metric. Do not claim universal domination of ordinary HDBSCAN at every cutoff.

## 🟢 Exposed SonotaCo 2013/2014 benchmark — 4/4 v31 and 4/4 literature wins

Binding recurrent-EOM benchmark run `31829200215`; artifact `9230008341`; result SHA-256 `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`.

SonotaCo is **EXPOSED DEVELOPMENT / VALIDATION BENCHMARK**, not pristine external validation.

| Panel | recurrent-EOM F1 / recovered | v31 F1 / recovered | ΔF1 vs v31 | Frozen literature F1 / recovered | ΔF1 vs literature |
|---|---:|---:|---:|---:|---:|
| Sugar 2013 | **0.375291 / 23** | 0.271980 / 16 | **+0.103311 (+38.0%)** | 0.203727 / 13 | **+0.171564 (+84.2%)** |
| Sugar 2014 | **0.437731 / 24** | 0.315290 / 17 | **+0.122441 (+38.8%)** | 0.259015 / 15 | **+0.178716 (+69.0%)** |
| catalogue HDBSCAN 2013 | **0.191460 / 11** | 0.148880 / 9 | **+0.042579 (+28.6%)** | 0.168130 / 10 | **+0.023330 (+13.9%)** |
| catalogue HDBSCAN 2014 | **0.168588 / 9** | 0.151981 / 9 | **+0.016607 (+10.9%)** | 0.156896 / 9 | **+0.011692 (+7.5%)** |

The matched-budget gate is passed on all four v31 panels: macro-F1 is strictly higher and recovered F1>0.5 count is at least equal. The same pairwise superiority condition also holds against the frozen Sugar-style / catalogue-HDBSCAN literature comparator on all four panels.

**Strongest supportable benchmark claim:** on the exposed SonotaCo 2013/2014 benchmark and the study's fixed matched-budget Hungarian evaluator, recurrent-EOM outperformed v31 and the corresponding frozen literature comparator in macro-F1 on all four year/method panels without losing recovered-shower count.

Do **not** rewrite that sentence as pristine cross-survey external validation.

## 🟡 Density-synchronous successor #1263 — no validation gain

Direct benchmark PR #1269 / run `31889652785`; artifact `9248203777`; result SHA-256 `00b9defa3a07fc1396b8d9dcbc3bd62da44dc95e7245ad44d7bdedf375570f5c`.

Exact verdict:

`NEUTRAL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1`

Although #1263 had a small positive full-GMN development result, its strict @100 gain was not robust in the frozen deletion diagnostic (`1761 -> 1761` aggregate). Direct SonotaCo comparison then produced exact ties with recurrent-EOM in both macro-F1 and recovered count on **all four** established panels.

Mechanistically, density-sync was active, but recurrent-EOM and #1263 selected the exact same SonotaCo nodes on both routes; their first full-order difference occurred only at rank 42. The fixed panel budgets therefore saw identical candidate sets.

**Selection implication:** recurrent-EOM is preferred by parsimony. The paper does not need the density-synchronous refinement to obtain its demonstrated benchmark performance.

## 🔴 / 🟡 Important robustness limitations

These belong in the manuscript rather than being hidden:

### GMN 2020/2021 retrospective — 🔴 NEGATIVE gate

The recurrent mechanism was active. In 2021, recovery and MRR improved, but top-100 precision fell; 2020 precision also fell. The conjunctive frozen transfer gate therefore failed. This is retrospective robustness evidence, not independent validation.

### NASA ASFN 2018/2019 — 🔴 NEGATIVE pristine cross-survey gate

Ordinary EOM and recurrent-EOM selected the same 34 candidate nodes; the recurrent mechanism was inactive. Recovery was identical, while recurrent MRR was slightly lower. Thus recurrent-EOM has **not** demonstrated universal cross-survey superiority.

### EFN 2017/2018 — 🟡 NEUTRAL pretruth

Ordinary and recurrent EOM selected the same 8 nodes. Because the recurrence mechanism was inactive before labels, the shower-label stage remained unopened. This is neutral transfer evidence.

## Recommended manuscript claim hierarchy

### Strong claims supported by the current evidence

1. **Methodological contribution:** a recurrence-aware modification of the HDBSCAN EOM extraction objective for repeated-observation physical streams.
2. **GMN development:** the frozen recurrent-EOM method passed a preregistered same-hierarchy comparison against ordinary HDBSCAN EOM on target-excluded GMN 2022/2023.
3. **SonotaCo benchmark:** recurrent-EOM beat v31 and the corresponding frozen literature comparators on all four matched SonotaCo 2013/2014 panels.
4. **Parsimony:** the later density-synchronous refinement did not improve any of those four SonotaCo panels, supporting selection of the simpler recurrent-EOM objective.

### Claims that are **not** supported

- recurrent-EOM is universally superior to HDBSCAN across meteor surveys;
- SonotaCo establishes pristine external validation;
- ASFN validates recurrent-EOM;
- recurrence necessarily changes HDBSCAN extraction on every survey;
- #1263 is demonstrably superior to recurrent-EOM overall.

## Suggested concise Results wording

> Recurrent-EOM altered HDBSCAN flat-cluster extraction while leaving the pooled density hierarchy unchanged. On target-excluded GMN 2022/2023 it passed the preregistered no-regression gate against ordinary EOM, including an increase from 88 to 89 recovered showers at rank 100 in 2022 and from 44 to 46 at rank 50 in 2023, with higher top-100 precision and MRR in both years. On the exposed SonotaCo 2013/2014 benchmark, recurrent-EOM exceeded v31 and the corresponding frozen Sugar-style or catalogue-HDBSCAN comparator in macro-F1 on all four matched panels without reducing the number of recovered showers. A later density-synchronous refinement produced no additional SonotaCo gain, favoring the simpler recurrent-EOM objective for the final methodology.

## Suggested concise limitation wording

> The SonotaCo comparison was an exposed development/validation benchmark rather than pristine external validation. Cross-survey transport was mixed: the recurrent criterion was inactive on EFN and ASFN, and the preregistered ASFN superiority gate failed. We therefore interpret recurrent-EOM as a supported methodology improvement on the study's development and SonotaCo benchmark settings, not as evidence of universal superiority across meteor networks.

## Firewall / scope

Protected solar longitude `[20°,55°]` remains inaccessible. OrbitTrace target information/events, MAARSY and DMS remain scientifically inaccessible. No AMOS request or AMOS scientific data are part of the selected-method evidence package.
