# OrbitTrace support-overlap family v9 — frozen development protocol

## Purpose

The passed pooled-year-centroid v8 method generated healthy within-year structure on independent AMOR 1996/1998 (1006 and 851 components) but only 19 recurrent cross-year families, so the external evaluation was power-inconclusive before ranking quality could be tested. The exact source audit shows that v8 inherits a fixed absolute cross-year centroid link radius of 1.5 in the frozen scaled radiant-speed metric.

v9 changes **only the cross-year recurrence-link criterion**. It is a separately named successor and is developed again on target-excluded GMN 2022/2023 before any further external survey is opened.

## Frozen recurrence rule

For every fixed4 component, define an observed support radius

`R(c) = max_e D(c.centroid, e)`

where `e` ranges over the component's unique member events and `D` is the exact frozen centroid-distance geometry already used by the v6/v8 family layer:

- wrapped solar-longitude difference / 4;
- wrapped Sun-centered longitude difference × cos(mean ecliptic latitude) / 2;
- ecliptic-latitude difference / 2;
- geocentric-speed difference / 2;
- Euclidean norm.

Two components from different years are linked iff

`D(c1.centroid, c2.centroid) <= R(c1) + R(c2)`.

This is the standard closed-ball overlap condition in the already-frozen metric. It has **no learned radius, multiplier, quantile, percentile, offset, or tunable parameter**. The maximum member distance is used because it is the complete observed support of the component and introduces no new scale choice.

After edges are formed, recurrent families are the ordinary connected components of this cross-year graph, exactly as in v6/v8. Same-year components may therefore coexist in a family through alternating-year paths; v7 proved that forcing one component per year fragments useful recurrent structure.

## Everything else remains inherited

- GMN development years: 2022 and 2023 only.
- Solar longitude 20°–55° is removed by the already-audited frozen parser before labels.
- Exact label-free fixed4 structural proposal engine from v6.
- Shortlist 64; audit shortlist 128.
- Anchor multiplicity >=2.
- Maximum 512 retained quartets per 10° bin.
- Component gates >=4 events and >=2 quartets.
- Family records, event/component unions, year-strength definition, family IDs, and persistence ranking use the exact frozen v6 semantics; only adjacency changes.
- Per-family-year centroid is then repaired exactly as in passed v8: union of unique same-year family events; circular mean for `sol`/`sun_lon`, median for `ecl_lat`/`vg`.
- Exact 128-event local episodes.
- Multi-anchor v3 and Brown implementations unchanged.
- Primary score remains `M=(v3/Brown)^2`.
- Primary ranking remains worst-year multiplicity, then geometric-mean multiplicity, then family ID.
- Brown, total-v3, and label-free persistence remain comparators.
- No source labels, shower identities, orbital elements, OrbitTrace target information, or target-region events may enter component support radii, links, families, pooled centroids, episodes, scores, or rankings.

## No-search rule

There is no search over support-radius definition, scale multiplier, family-link variant, threshold, shortlist, component gate, quartet cap, episode size, score, ranking fusion, weight, or evaluation endpoint. If this exact support-overlap rule fails, it is a no-go for v9; no max-to-quantile or multiplier rescue is authorized.

## Integrity gates

All must pass:

1. exact frozen v6/v8 source and self-tests;
2. exact target-excluded 2022/2023 development panel;
3. zero label-dependent calibration events and no score threshold;
4. >=24 scannable 10° bins in each year;
5. every component support radius is finite and >=0;
6. every component support radius is computed from all and only that component's unique member events;
7. every v9 edge satisfies the exact closed-ball overlap rule and every non-edge fails it;
8. no same-year direct edge exists;
9. support-overlap adjacency is non-vacuously different from the old fixed-1.5 adjacency;
10. >=100 recurrent families;
11. >=72 qualified known showers after rankings freeze;
12. v8 pooled-centroid repair is non-vacuous where duplicate same-year components occur, with exact single-component equivalence;
13. every local episode size is exactly 128;
14. Brown equivalence difference <=1e-10;
15. no label or target information enters proposal/link/family/pooling/score/ranking generation.

## Scientific gates

Labels are consulted **only after all four rankings are frozen**. All must pass:

1. label-free persistence recovery@100 >=55;
2. multiplicity recovery@100 >= Brown recovery@100 +1;
3. multiplicity recovery@100 >= `ceil(0.90 × persistence recovery@100)`;
4. multiplicity recovery@100 >=54;
5. multiplicity top-100 dominant precision >=0.50;
6. **successor non-regression:** multiplicity recovery@100 >=58, the exact passed-v8 primary recovery on the same development panel.

The sixth gate is preregistered before v9 development access so a new recurrence architecture is not promoted by trading away the current method's primary recovery.

## Decision rule

`PASS_SUPPORT_OVERLAP_FAMILY_V9_DEVELOPMENT` only if every integrity and scientific gate passes. Otherwise `FAIL_SUPPORT_OVERLAP_FAMILY_V9_DEVELOPMENT` and this exact formulation is preserved as a no-go.

A development pass authorizes only a separately frozen structure/parser audit of a still-fresh external survey. CAMSv3 2017/2018 are currently reserved by a prior full-history freshness audit and must remain unopened during v9 development.

No development pass authorizes OrbitTrace reveal or the final target-containing GMN discovery scan by itself.
