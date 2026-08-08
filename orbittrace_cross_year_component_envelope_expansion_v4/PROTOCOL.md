# OrbitTrace cross-year component-envelope expansion v4 — frozen development protocol

## Purpose

The target-excluded v1–v3 membership-expansion experiments established a consistent mechanism. Expanding the exact frozen v8 recurrent families greatly improves membership F1, especially for large showers, but treating the inherited v8 family-link radius 1.5 as a binary membership cutoff remains too permissive. Event-level witnesses, two-event witnesses, and one frozen component centroid per source component all preserved the F1 gain while adding roughly 160k–175k events and regressing catalogue recovery/precision.

v4 moves out of the binary-radius expansion lineage. It uses each already-existing source component's own frozen seed spread to define its membership envelope.

## Frozen base and blinding

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Development panel: exact target-excluded GMN 2022/2023 used by v8 and v1–v3.
- Solar longitude 20°–55° remains removed before label access.
- The exact v8 226-family universe, pooled family-year centroids, scores, and multiplicity ranking must reproduce before expansion.
- No OrbitTrace coordinate, member, identity, prior target family, target-region event, Stage A/B output, or reveal may enter this work.
- No external validation panel is designated by this development protocol. Repository history already contains prior SonotaCo 2017 raw/score/label exposure, so it is not represented as pristine here. Any later external validation requires a separate repository-history freshness audit and a separately frozen protocol before scientific-value access.

## Required predecessor

Before any v4 development-data access, verify the exact v3 no-go artifact:

- run `31235669516`;
- artifact `9015567085`;
- artifact digest `sha256:80c5590a5702f3d641315321c5d8ef1387c61a6fcf6a57057b2a7ebe7b7ecfcb`;
- source commit `f3616eed5a14118c5148513b865eb7491e6f346f`;
- verdict `FAIL_CROSS_YEAR_COMPONENT_CENTROID_EXPANSION_V3_DEVELOPMENT`.

This predecessor establishes that reducing witness redundancy is insufficient while the 1.5 link radius itself is still used as the membership boundary.

## Sole v4 change: frozen empirical component envelope

For each target year independently:

1. For each exact frozen v8 family, use only its original components from the other year.
2. For each such source component, retain its already-frozen component centroid; do not refit it.
3. Compute the exact inherited v8 distance from every original seed member of that component to that frozen centroid.
4. Define the source component's empirical envelope radius as the maximum of those original-seed distances, capped at the inherited structural radius 1.5.
5. A non-seed target-year event is eligible for that family only if it lies inside at least one of that family's source-component empirical envelopes.
6. If several families are eligible, retain the inherited exclusive nearest-family assignment by smallest absolute component-centroid distance; stable family ID breaks exact ties.
7. Original v8 seed events are retained. Newly assigned events never become support. There is no recursive growth.

The envelope is therefore the smallest centroid-centered radius that contains the component's own frozen seed members, subject only to the pre-existing v8 structural cap. There is no fitted quantile, scale factor, alpha level, shrinkage coefficient, density threshold, event-witness threshold, component-count threshold, or radius grid.

## Prohibited variants

This run may not test or select:

- any alternate quantile or robust-spread statistic;
- any multiplicative/additive envelope inflation or shrinkage;
- any radius other than the inherited 1.5 cap;
- any minimum/maximum component size rule;
- any recursive reassignment or centroid refit;
- any reranking, score fusion, or family-graph change;
- any literature-benchmark-driven parameter;
- any external-validation scientific value, label, score, or endpoint.

A failure is a permanent no-go for this exact component-envelope rule. It does not authorize a same-panel parameter search.

## Evaluation and promotion gates

Reuse the exact v1–v3 scientific gates without relaxation:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both 2022 and 2023;
- 4–9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one of the 10–24, 25–49, 50–99, or 100+ bins must gain >=0.10 mean F1 in both years;
- every integrity/blindness gate must pass.

Pass only if all gates pass.

## Consequence of a pass

A development pass authorizes only a separate external-panel freshness audit and, if that audit identifies a scientifically usable holdout, preparation of a separately frozen prospective validation/benchmark protocol. The v8 final blind GMN firewall remains untouched, and no OrbitTrace target-containing search is authorized by this experiment.

## Provenance correction note

The initial v4 commit incorrectly described SonotaCo 2017 as untouched. Repository-history inspection performed while the first v4 computation was still in progress—and before any v4 outcome was observed—showed prior SonotaCo 2017 raw/score/label exposure in later validation work. This correction changes only prospective-validation metadata. The v4 membership rule, development panel, scientific gates, blinding boundary, and no-tuning restrictions are unchanged.