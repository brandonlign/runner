# OrbitTrace label-free sparse-support multiplicity v6 — development protocol

## Status and question

Frozen before execution on the already-exposed, target-excluded GMN 2022–2023 development panel.

Question: can the surviving sparse-support multiplicity architecture remove its last source-label dependency without losing the sparse-stream proposal/recovery behavior that made multiplicity promising?

This is a narrow successor to v5, not a restart of methodology development. The only scientific change is removal of the **known-SPORADIC calibration threshold** from fixed4 proposal generation. Everything after that threshold is kept at its previously frozen value.

## Blindness

- development years: exactly 2022 and 2023;
- solar longitude 20°–55° inclusive is removed by the frozen parser before label normalization/evaluation;
- no 2024–2026 catalogue;
- no OrbitTrace coordinates, identity, members, activity values, HDBSCAN assignments, or target-recovery artifact;
- shower labels may be consulted only after every family and ranking is frozen, for development evaluation.

## Frozen label-free proposal generator

For each target-excluded year and each 10° solar-longitude bin:

1. Use every quality event in the scan population as a possible anchor. No shower identity enters proposal generation.
2. Use the exact frozen fixed4 physical geometry and local support:
   - 4° angular scale;
   - 10%-speed scale;
   - ±15° candidate pool around the 10° bin centre, matching the frozen support scanner;
   - 64-neighbor first shortlist;
   - 128-neighbor exact audit shortlist.
3. For each anchor, select the exact three nearest events under the frozen fixed4 distance and form one anchored quartet.
4. Consolidate identical quartets within the bin.
5. Require the unchanged minimum anchor multiplicity of **2**.
6. **Do not apply any empirical/null score threshold.** This is the sole scientific change from the frozen fixed4 proposal scanner and is required because an unlabeled external survey cannot supply a known-SPORADIC calibration reservoir.
7. Retain at most the unchanged **top 512** unique quartets in each bin, using the already-frozen order:
   - anchor multiplicity descending;
   - quartet score descending;
   - quartet identifiers ascending.
8. Construct within-year connected components with the unchanged requirements:
   - at least 4 events;
   - at least 2 retained quartets.
9. Link components across years with the unchanged fixed4 family rule:
   - centroid distance ≤1.5 under the same frozen geometry;
   - at least 2 years.

There is no threshold search, cap search, link-radius search, geometry search, or rescue queue.

## Frozen ranking

For each recurrent family/year:

1. Construct the exact deterministic 128-event local episode around the family centroid.
2. Compute the exact frozen multi-anchor v3 energy and independent Brown comparator.
3. Compute the already-promoted scale-free multiplicity term:

`M = (v3 / Brown)^2`

Primary family rank is unchanged from multiplicity v5:

1. worst-year multiplicity descending;
2. two-year geometric-mean multiplicity descending;
3. family id ascending.

Report unchanged comparators:

- Brown minimum-year score;
- total-v3 minimum-year score;
- label-free fixed4 structural persistence ordering returned by the frozen family scorer.

No multiplicity p-value, RRF, weight search, threshold search, or endpoint search is permitted.

## Frozen development evaluation

Labels are first consulted only after all four rankings exist.

Eligible/qualified known-shower definitions are unchanged:

- eligible: ≥8 events total and ≥4 in each development year;
- qualified family match: overlap ≥4 and precision ≥0.50;
- primary endpoint: top 100 families.

Historical reference points are fixed before execution:

- frozen fixed4 calibrated scaffold: 90 qualified matches, 61 recovered@100;
- multiplicity on that scaffold: 60 recovered@100;
- Brown on that scaffold: 54 recovered@100.

## Frozen integrity / continuation gates

All must pass:

1. exact frozen source/self-test and 2022–2023 target-exclusion guards;
2. at least 24 structurally scannable 10° bins per year;
3. first-shortlist vs 128-neighbor audit reconciliation is recorded exactly as in fixed4;
4. every recurrent family spans both years;
5. every local multiplicity episode has exactly 128 events;
6. Brown equivalence difference ≤1e-10 everywhere;
7. at least 100 recurrent families;
8. at least **72 qualified known-shower matches**, i.e. ≥80% of the frozen fixed4 scaffold's 90 qualified matches.

## Frozen scientific gates

All must pass:

1. label-free structural persistence recovered@100 ≥ **55**, i.e. at least 90% of the frozen calibrated fixed4 recovery of 61 after integer rounding down to a fixed predeclared floor;
2. multiplicity recovered@100 ≥ Brown recovered@100 + 1;
3. multiplicity recovered@100 ≥ `ceil(0.90 × label-free persistence recovery@100)`;
4. multiplicity recovered@100 ≥ **54**, preserving at least 90% of its prior 60-shower development recovery;
5. multiplicity top-100 dominant-family precision ≥0.50.

Failure of any scientific gate is a development no-go. No result may be used to alter the cap, proposal order, geometry, family link, multiplicity formula, or gate and rerun this same architecture.

## Interpretation

A pass would establish a fully **source-label-free proposal + independent multiplicity ranking architecture** on the development panel. It would authorize freezing a separate external-survey protocol (currently SAAMER is the strongest available candidate) before any external scientific meteor value is read.

A pass would not reveal OrbitTrace, constitute an external validation by itself, or establish superiority to literature methods.
