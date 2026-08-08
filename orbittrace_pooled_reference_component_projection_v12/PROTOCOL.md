# OrbitTrace pooled-reference nearest-component projection v12 — frozen development protocol

## Purpose

The promoted v8 method correctly repairs v6's duplicate-year overwrite by recomputing a family-year reference centroid from the union of all unique events in every same-year component. A clean-room source-only audit then established that duplicate family-years are often genuinely multimodal: the pooled reference remains near at least one constituent component, while constituent component centroids can be widely separated.

v12 tests one minimal representation-layer successor. It preserves the exact v8 family universe and the semantically valid pooled family-year reference, but uses the nearest already-detected constituent component centroid as the inherited 128-event scoring anchor.

This is the only successor architecture authorized by this protocol. No alternate representation may be added after execution.

## Frozen representation rule

For each exact v8 connected family and each year:

1. collect all same-year components already belonging to that family;
2. form the union of their unique target-excluded event IDs;
3. recompute the exact v8 pooled reference centroid using:
   - `sol`: circular mean;
   - `sun_lon`: circular mean;
   - `ecl_lat`: median;
   - `vg`: median;
4. compute the exact inherited frozen centroid distance from that pooled reference to every constituent same-year component centroid;
5. select the constituent component with minimum distance to the pooled reference;
6. break an exact distance tie lexicographically by stable component ID;
7. use that selected component centroid only as the family-year center supplied to the unchanged 128-event episode constructor and scoring code.

For a single-component family-year, this rule is exactly identical to v8.

The pooled reference remains the semantic all-component family-year summary used to define the projection. The selected component is not chosen by its quartet score, event count, multiplicity score, Brown score, v3 score, shower label, persistence, known-shower overlap, or benchmark outcome.

## Why this rule and no others

The source-only audit was frozen and executed before this successor was defined. It found, on target-excluded GMN 2022/2023:

- 226 exact v8 families and 452 family-years;
- 118 duplicate same-year family-years across 75 families;
- duplicate component count median 3, p90 21.9, max 100;
- constituent maximum pairwise centroid distance median 1.6866, p90 5.2794, max 8.9582;
- pooled-reference to nearest constituent centroid distance median 0.4314, p90 0.7948, max 1.1858;
- zero duplicate family-years with the pooled reference farther than the inherited 1.5 family-link radius from every constituent component.

Thus the clean minimal correction is a deterministic projection of v8's valid pooled reference onto an observed constituent mode. A max-score component would introduce a component-count-dependent look-elsewhere choice; score averaging would change score semantics and weight fragmentation; a component medoid would discard the pooled event-mass reference. None is tested.

Audit provenance:

- PR #404;
- run `31229695771`;
- artifact `9013581721`;
- artifact digest `sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2`;
- verdict `PASS_FAMILY_YEAR_REPRESENTATION_SOURCE_ONLY_AUDIT`;
- shower-label use: none.

## Everything else remains exact v8

Unless mathematically required by the representation rule above, no scientific behavior changes:

- development panel: GMN 2022/2023;
- solar longitude 20°–55° removed by the frozen parser before labels or method-development access;
- exact fixed4 label-free proposal generation;
- exact 4° / 10% geometry;
- shortlist 64 / audit 128;
- minimum anchor multiplicity 2;
- top 512 quartets per bin;
- component minimum 4 events / 2 quartets;
- exact v8/v6 connected multi-component family topology;
- family link radius 1.5;
- exact family membership, family IDs, component IDs, event unions, persistence ordering, and 226-family universe;
- exact 128-event local episode constructor;
- exact multi-anchor v3;
- exact independent Brown comparator;
- exact multiplicity `M=(v3/Brown)^2`;
- primary family ranking: worst-year multiplicity descending, then geometric-mean multiplicity descending, then stable family ID;
- no label-dependent calibration threshold;
- no threshold, radius, cap, weight, score-fusion, endpoint, or representation search.

## Blindness and evaluation order

No OrbitTrace/GhostStream coordinate, activity value, morphology, canonical member, historical HDBSCAN assignment, prior blind-recovery family/rank, target-region event, legacy target constant, or Stage A/B reveal output may be accessed.

The 20°–55° interval must remain excluded before labels, proposal generation, component construction, family construction, representation, episode construction, scoring, or evaluation.

All families, projected scoring centers, v3/Brown/multiplicity scores, and all rankings are completed before known-shower labels are evaluated. There is exactly one successor architecture, so no label-based candidate selection and no development/validation label split is required.

## Exact predecessor baselines

Promoted v8 target-excluded GMN 2022/2023 baseline:

- families: 226;
- qualified known showers: 95;
- multiplicity recovery@100: 58;
- persistence recovery@100: 59;
- Brown recovery@100: 55;
- v3 recovery@100: 55;
- multiplicity top-100 dominant precision: `0.6884631112636006`;
- multiplicity MRR: `0.045531138942766655`.

## Integrity gates

All must pass:

1. exact target-excluded GMN 2022/2023 panel and 24 monthly sources;
2. exact v8 fixed4 constants and exact 226-family connected-family universe;
3. exact 95 qualified known showers for the unchanged family membership universe;
4. exact persistence baseline recovery@100 = 59;
5. all 334 single-component family-years reproduce their component centroid to <=1e-12;
6. exactly 118 duplicate family-years across 75 families are handled by the projection rule;
7. every selected duplicate-year centroid is an actual constituent component centroid;
8. selection is minimum pooled-reference distance with stable component-ID tie break and no score/label input;
9. non-centroid family structure is unchanged;
10. all local episodes are exactly 128 events;
11. Brown equivalence <=1e-10;
12. zero label-dependent calibration events and no score threshold;
13. source/provenance guards and self-tests pass.

## Promotion gates

v12 is promoted only if every integrity gate passes and all of the following hold on the one frozen target-excluded evaluation:

1. multiplicity recovery@100 >= **59**;
2. multiplicity top-100 dominant precision >= **0.68**;
3. multiplicity MRR >= **0.045531138942766655**;
4. persistence recovery@100 = **59**;
5. Brown recovery@100 >= **55**;
6. v3 recovery@100 >= **55**;
7. multiplicity recovery@100 >= Brown recovery@100 + 1;
8. multiplicity recovery@100 >= ceil(0.90 × persistence recovery@100).

A pass provisionally replaces v8 for later external validation and matched literature benchmarking. It does not authorize a target-containing scan or reveal.

A failure is a permanent no-go for this representation path. No second pooling/projection/selection tweak is authorized. In that case v8 is declared the final OrbitTrace discovery architecture and PR #356 remains the final historical v8 blind protocol pending the separate authorization process.

## Execution firewall

This methodology branch itself does not execute the development evaluation. Execution requires a separate child PR whose only diff is `orbittrace_pooled_reference_component_projection_v12/RUN.md` against the frozen methodology commit. The Actions workflow must verify that one-file child diff and execute the exact base SHA, not child scientific code.
