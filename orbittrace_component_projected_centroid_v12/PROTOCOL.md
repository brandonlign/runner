# OrbitTrace component-projected centroid v12 — frozen clean-room development protocol

## Purpose

The promoted v8 architecture is retained in full except for the family-year episode anchor used when a connected family contains multiple components from the same year.

A source-only clean-room audit (PR #404; run `31229695771`; artifact `9013581721`; ZIP digest `sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2`) established, without shower-label access, that 118 of the 452 v8 family-years contain multiple same-year components. Their constituent component centroids can be widely separated (median maximum pairwise distance 1.6866; maximum 8.9582), while the v8 pooled centroid remains within 1.5 of at least one constituent component in every duplicate family-year. Thus the pooled all-event statistic is a valid global summary but can be a synthetic local episode anchor between independently detected modes.

This protocol freezes exactly one successor. No alternative medoid, score-maximizing component, weighted average, rank fusion, threshold, or candidate set is permitted.

## Frozen successor rule

1. Build the exact v8 proposal components and exact v8 connected-family topology.
2. For every family-year, compute the exact v8 pooled centroid from the union of all unique same-year family events:
   - `sol`: circular mean;
   - `sun_lon`: circular mean;
   - `ecl_lat`: median;
   - `vg`: median.
3. If the family-year contains exactly one component, its episode centroid remains exactly that component centroid (equivalent to v8 pooling).
4. If the family-year contains multiple components, choose the already-detected component whose frozen `centroid_distance` to the v8 pooled centroid is smallest. Ties are resolved only by stable string `component_id`.
5. Use that selected component's existing centroid as the family-year episode anchor. Family membership, event union, component membership, recurrence adjacency, family ID, and persistence score do not change.

This is a deterministic projection of the v8 all-event summary onto an observed coherent component mode. It is not the v6 overwrite: dictionary iteration order never selects the component, and no shower label or episode score participates in selection.

## Everything else remains exact v8

- Development panel: GMN 2022/2023 only.
- Solar longitude 20°–55° excluded before labels, proposals, family construction, scoring, or evaluation.
- Fixed4 4° / 10% geometry.
- Shortlist 64 / audit 128.
- Minimum anchor multiplicity 2.
- Top 512 quartets per bin.
- Component minimum 4 events / 2 quartets.
- Exact v8 connected multi-component family topology.
- Family link radius 1.5.
- Exact 128-event local episode construction.
- Exact multi-anchor v3 and independent Brown comparator.
- Multiplicity `M=(v3/Brown)^2`.
- Primary order: worst-year multiplicity descending, then geometric-mean multiplicity descending, then stable family ID.
- Label-free persistence remains unchanged as a comparator.
- No label-dependent calibration threshold.

## Pre-label freeze and blindness

The component projection rule, tie-break, all constants, source hashes, promotion gates, and workflow are committed before any shower-label evaluation for v12.

No OrbitTrace/GhostStream coordinate, radiant, speed, orbit, activity center, canonical member ID, historical target family/rank, target-region event, Stage A output, or Stage B output may enter this work. PR #356 Stage A and Stage B remain dormant and must not be executed.

## Required structural reproduction

Before interpreting scientific performance, v12 must reproduce:

- exactly 226 recurrent families;
- exactly 452 family-years;
- exactly 75 families and 118 family-years with duplicate same-year components;
- exact v8 family IDs/component IDs/event IDs and label-free persistence ordering;
- exactly 95 qualified known showers after labels are opened;
- persistence recovery@100 exactly 59;
- exact 128-event local episodes;
- Brown equivalence within `1e-10`;
- all single-component family-years equivalent to v8;
- every projected duplicate-year anchor is an existing constituent component centroid;
- every projection is selected solely by minimum frozen centroid distance to the pooled centroid with stable-ID tie-break.

## Promotion gates

This one candidate is promoted only if every inherited v8 integrity/scientific gate passes and all of the following stricter successor gates pass:

1. multiplicity recovery@100 >= **59**;
2. multiplicity top-100 dominant precision >= **0.68**;
3. multiplicity MRR >= **0.045531138942766655** (exact passed-v8 baseline);
4. persistence recovery@100 == **59**;
5. qualified known showers == **95**;
6. all family/topology/blindness/provenance gates pass;
7. no method change occurs after label evaluation.

Recovery >=60 is preferred but not required. A result of 58 or lower, a meaningful precision regression, or an MRR regression makes v12 a permanent no-go.

## Decision rule

There is no candidate selection stage because exactly one representation rule is frozen. Shower labels are consulted only after all v12 family-year anchors, local episodes, physical scores, and rankings exist.

If v12 fails any promotion gate, no additional tiny v8 representation variant is authorized. v8 is then declared the final OrbitTrace discovery methodology architecture and later work returns to external validation plus separately authorized use of the already-frozen v8 blind firewall.

If v12 passes, it becomes the provisional promoted successor and may proceed unchanged to a separately frozen matched literature benchmark. Neither outcome authorizes the target-containing blind search or OrbitTrace reveal.