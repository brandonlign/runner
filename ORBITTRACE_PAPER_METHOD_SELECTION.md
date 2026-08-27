# OrbitTrace paper-method selection — temporal-fairness correction

## Selected method

**Recurrent-EOM HDBSCAN v1** remains the preferred OrbitTrace paper/development methodology on the strength of its frozen target-excluded GMN development result and its direct tie with the later density-synchronous refinement on the same pooled SonotaCo benchmark.

Exact recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

## Binding correction to the SonotaCo literature claim

The prior statement that recurrent-EOM had established **4/4 superiority over the frozen Sugar/HDBSCAN literature comparators** on SonotaCo 2013/2014 is withdrawn as a fair-comparison claim.

Reason: the recurrent-EOM benchmark fits one pooled 2013+2014 hierarchy for each route and uses both years to determine recurrent stability, selected clusters, memberships, and ranking before evaluating the 2013 and 2014 panels separately. The frozen literature comparator runner instead executes Sugar or HDBSCAN on one year at a time. Thus recurrent-EOM receives cross-year temporal information that the literature comparators do not receive. Truth remains sealed until after all candidate outputs are frozen, so this is **not truth leakage**, but it is an information-set asymmetry and therefore cannot support a clean apples-to-apples literature-superiority claim.

The numerical SonotaCo results remain valid descriptions of the outputs produced under that asymmetric protocol:

| Panel | recurrent-EOM macro-F1 / recovered | literature macro-F1 / recovered |
|---|---:|---:|
| Sugar 2013 | `0.3752906816276458 / 23` | `0.20372657466522806 / 13` |
| Sugar 2014 | `0.43773122295664196 / 24` | `0.25901527732153334 / 15` |
| HDBSCAN 2013 | `0.1914598192215768 / 11` | `0.16813025050497152 / 10` |
| HDBSCAN 2014 | `0.1685878550176112 / 9` | `0.15689595582646423 / 9` |

These values must be labeled **asymmetric temporal-context benchmark results**, not literature superiority.

## Evidence that remains valid

1. Recurrent-EOM passed its frozen target-excluded GMN 2022+2023 development gate.
2. On the exposed SonotaCo pooled benchmark, recurrent-EOM beat exact v31 on all four panels. This comparison is temporally fair because v31 and recurrent-EOM are compared within the same established pooled benchmark framework.
3. The later density-synchronous refinement #1263 tied recurrent-EOM exactly on all four direct SonotaCo panels and did not justify its added complexity.

## Required fair literature benchmark

Before claiming superiority to Sugar or catalogue HDBSCAN, rerun a preregistered benchmark with **equal temporal information**. Acceptable designs are:

- pooled-vs-pooled: give each comparator the same pooled 2013+2014 label-free event universe before freezing outputs, then score year-specific memberships under the same fixed candidate-budget and Hungarian-F1 evaluator; or
- forward-transfer: fit/freeze every method using only a common development year set and evaluate on an untouched later year, with identical temporal access for every method.

Do not use the existing pooled recurrent-EOM versus single-year comparator run as evidence that recurrent-EOM beats the literature.

## Current paper claim level

Until an equal-temporal-information benchmark is completed, the defensible claim is:

> recurrent-EOM is a positive modification of HDBSCAN under frozen target-excluded GMN development and shows strong portability on exposed SonotaCo, but superiority over the published Sugar/HDBSCAN comparators has not yet been established under a fully symmetric temporal-information benchmark.

Protected solar longitude `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
