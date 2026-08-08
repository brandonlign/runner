# OrbitTrace final methodology decision after v12

## Decision

The final target-free discovery architecture is **v8 pooled-year-centroid label-free sparse-support multiplicity** at commit `c9d6c44704013ba0c9430100e98a29a56b453304`.

No post-v8 successor is promoted. The sole remaining clean representation-layer question identified after v11 has now been resolved by a separately isolated clean-room experiment and failed its preregistered promotion gate. Under the precommitted no-method-shopping rule, the v8 architecture is therefore frozen as final for the pending external-validation and target-free blind-discovery tracks.

This record does not execute a target-containing search or reveal.

## Clean-room representation audit

PR #404 (`Audit v8 family-year representation geometry`) was based directly on promoted v8 and used only target-excluded GMN 2022/2023 geometry, with no shower-label evaluation.

Immutable audit:

- run: `31229695771`;
- artifact: `9013581721`;
- artifact ZIP digest: `sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2`;
- verdict: `PASS_FAMILY_YEAR_REPRESENTATION_SOURCE_ONLY_AUDIT`;
- recurrent families: 226;
- family-years: 452;
- duplicate same-year family-years: 118 across 75 families;
- duplicate family-year component-count median: 3;
- maximum pairwise constituent-component distance: 8.9581889262;
- pooled-to-nearest constituent-component distance median: 0.4314418761, maximum: 1.1857571214;
- pooled centroid outside every constituent 1.5-neighborhood: 0/118.

The audit established that duplicate same-year components can be genuinely multimodal, while the v8 pooled centroid always remains close to at least one constituent component under the already-frozen metric. It justified testing one deterministic component-projection rule without using shower labels or episode scores to choose a component.

## Frozen v12 successor and result

PR #422 froze **v12 component-projected centroid** before label evaluation. Its only scientific change was:

1. compute the exact v8 pooled all-event family-year centroid;
2. for a duplicate same-year family-year, choose the already-detected constituent component centroid nearest to that pooled centroid using the exact inherited centroid metric, ties by stable component ID;
3. use that existing component centroid as the exact 128-event local episode anchor;
4. leave single-component family-years unchanged.

No alternate medoid, maximum-score, weighted, thresholded, or label-selected rule was tested. Proposal generation, components, v8 connected-family topology, radius 1.5, event unions, persistence, v3, Brown, multiplicity `M=(v3/Brown)^2`, and ranking semantics remained fixed.

Immutable v12 result:

- run: `31231580731`;
- artifact: `9014245840`;
- artifact ZIP digest: `sha256:c62abf8001dc5468acb693576ba73a2c54be5878509b2f181a0280ff55ee93da`;
- verdict: `FAIL_COMPONENT_PROJECTED_CENTROID_V12_NO_GO`;
- recurrent families: 226;
- qualified known showers: 95;
- multiplicity recovery@100: **60** versus promoted-v8 **58**;
- multiplicity top-100 dominant precision: **0.7047461025** versus promoted-v8 **0.6884631113**;
- multiplicity MRR: **0.0450546490** versus promoted-v8 **0.0455311389**;
- persistence recovery@100: 59;
- Brown recovery@100: 56;
- v3 recovery@100: 56;
- projected duplicate family-years: 118 across 75 families.

All inherited integrity and scientific gates passed. v12 nevertheless failed the preregistered successor requirement `multiplicity MRR >= 0.0455311389`. The recovery and precision gains therefore cannot be used to relax the frozen promotion rule after label evaluation. v12 is a permanent no-go.

The intermediate file named `pooled_year_centroid_v8_development.json` emitted inside the v12 run is not a new authoritative v8 baseline. It is the inherited v8 development runner operating after the frozen v12 projection has been installed. The authoritative promoted-v8 baseline remains the original passed-v8 artifact and values above.

## Closed successor space

The following paths remain permanent no-gos and are not reopened by v12:

- one-component-per-year matching (v7);
- reciprocal/mutual-nearest recurrence;
- complete-link/seed-complete recurrence;
- support-normalized structural reranking;
- support-radius / closed-ball overlap (v9);
- equal-weight multiplicity/persistence rank consensus (v10);
- exact member-event support-contact recurrence (v11);
- cycle-consistent one-to-one transport;
- v12 component-projected family-year centroids;
- post-hoc fusion weights, thresholds, radius tuning, component-score selection, or alternative pooling-rule searches.

No additional small v8 representation tweak is scientifically authorized from this development chain.

## Final v8 status

The promoted v8 architecture remains:

- target-excluded fixed4 label-free proposal generation;
- 64-event shortlist with 128-event audit;
- minimum anchor multiplicity 2;
- top 512 quartets per bin;
- components with at least 4 events and 2 quartets;
- exact connected multi-component cross-year family topology;
- family link radius 1.5;
- duplicate same-year family representation by the union of unique same-year family events with circular-mean solar/Sun-centered longitude and median latitude/speed;
- exact 128-event local episodes;
- exact multi-anchor v3 and Brown comparator;
- primary multiplicity `M=(v3/Brown)^2`;
- worst-year multiplicity, then geometric-mean multiplicity, then stable family ID ranking;
- no label-dependent calibration threshold.

Authoritative passed target-excluded GMN 2022/2023 development:

- recurrent families: 226;
- qualified known showers: 95;
- multiplicity recovery@100: 58;
- persistence recovery@100: 59;
- Brown recovery@100: 55;
- v3 recovery@100: 55;
- multiplicity top-100 dominant precision: 0.6884631113;
- multiplicity MRR: 0.0455311389.

## Literature claim boundary

The frozen literature benchmark remains unchanged. v8 has **not** established superiority over full 1,000-clone Sugar or catalogue HDBSCAN under the strongest matched comparisons, particularly for moderate/large showers. v12's development-only recovery/precision gains do not alter that benchmark because v12 failed promotion and must not be benchmark-tuned or presented as the final method.

Therefore the final v8 method may be described as a strong sparse recurrent target-free discovery architecture, but not as state-of-the-art or as beating the strongest published methods.

## Blindness and next authorized stages

Throughout PR #404 and v12 development:

- solar longitude 20°–55° was excluded before labels, proposals, scoring, or evaluation;
- no OrbitTrace target coordinates, members, prior target family IDs/ranks, target-region events, Stage A output, or Stage B output were accessed;
- no target-containing blind search was executed.

Because v8 remains final, the already-frozen v8 target-free blind protocol on PR #356 / freeze commit `961f9e5c602679e1620fa20206cda794ca28660a` remains the applicable historical freeze. PR #356 itself remains dormant: Stage A and Stage B are not authorized by this methodology decision.

The methodology-development track is now closed. The next scientific stages are:

1. obtain/complete scientifically defensible external validation of frozen v8 without changing the detector;
2. only if the separately frozen authorization conditions are satisfied, authorize the dormant PR #356 Stage A execution path through its existing firewall;
3. keep Stage B reveal separately gated exactly as frozen.

No final OrbitTrace target reveal is performed or authorized by this document.