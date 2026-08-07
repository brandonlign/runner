# OrbitTrace exact-support-contact recurrence v11 — frozen development protocol

## Purpose

Promoted v8 remains the incumbent. Its fixed centroid-link recurrence passed target-excluded GMN 2022/2023 development, but external AMOR 1996/1998 was power-inconclusive because 1,006 and 851 healthy within-year components collapsed to only 19 recurrent families. The first adaptive recurrence successor, v9 support-ball overlap, was too destructive on development: it retained only 821 cross-year edges versus 7,933 fixed-v8 edges, created 445 fragmented families, and multiplicity recovery fell to 36/100. v9 is permanently rejected.

v11 tests one source-grounded middle formulation. It changes **only cross-year adjacency** and preserves v8's multi-component connected-family semantics. Instead of comparing only component centroids (v8) or approximating component support by a maximum-radius ball (v9), it uses the actual observed member support.

## Exact recurrence rule

Let `D` be the exact frozen v6/v8 radiant-speed distance already used for family linkage. Two components from different years are linked iff there exists at least one pair of their actual unique member events `e1`, `e2` such that:

`D(e1, e2) <= 1.5`.

The value 1.5 is the **unchanged v8 family-link radius**. It is not re-estimated or multiplied. The rule contains no support-radius approximation, quantile, percentile, k-nearest setting, overlap fraction, learned covariance, or fitted parameter.

After these exact support-contact edges are formed, recurrent families are ordinary connected components exactly as in v6/v8. Multiple components from the same year may coexist through alternating-year paths. v7, reciprocal-nearest, and complete-link experiments already showed that forcing one component per year destroys useful sparse-stream structure.

## Exact and exhaustive implementation requirement

An implementation may accelerate pair discovery only with mathematically necessary conditions that cannot discard a true contact. The frozen implementation uses a `cKDTree` prefilter on three nonnegative terms of the exact metric:

- wrapped solar-longitude difference / 4;
- ecliptic-latitude difference / 2;
- geocentric-speed difference / 2.

Solar longitude is handled exactly as circular by duplicating one year's scaled coordinate at ±90 (`360/4`). The Sun-centered-longitude term is deliberately omitted from the prefilter. Therefore every event pair with full `D <= 1.5` must lie within radius 1.5 in this reduced 3-D space. Every prefiltered pair is then checked with the exact frozen `centroid_distance` implementation before it can create an edge.

No approximate nearest-neighbor search is allowed. Every accepted component edge must retain at least one exact event-pair witness.

## Everything else remains exact v8

- GMN 2022 and 2023 development years only;
- solar longitude 20°–55° removed before labels;
- exact label-free fixed4 proposals;
- 4° angular / 10% speed proposal geometry;
- shortlist 64 and audit shortlist 128;
- anchor multiplicity >=2;
- top 512 retained quartets per 10° bin;
- within-year components >=4 events and >=2 quartets;
- connected-family closure and minimum 2 represented years;
- exact v8 pooled same-year centroids after topology freezes;
- exact 128-event local episodes;
- exact multi-anchor v3, Brown, and multiplicity `M=(v3/Brown)^2`;
- primary multiplicity ranking: worst represented-year multiplicity then geometric mean then family id (with this two-year development panel, identical semantics to v8);
- Brown, total-v3, and persistence comparators;
- labels first used only after adjacency, families, pooled centroids, scores, and all rankings freeze;
- no OrbitTrace information, target-region event, orbit, or shower label enters the method.

## No-search rule

This protocol authorizes exactly one recurrence rule: actual member-event support contact at the inherited radius 1.5. It does not authorize changing 1.5, using a contact count, requiring reciprocal contacts, using a percentile support, adding a distance margin, combining centroid and contact rules, or trying another support-contact variant after the result.

## Integrity gates

All must pass:

1. exact frozen v6/v8 source and passed-v8 artifact provenance;
2. exact target-excluded GMN 2022/2023 panel;
3. zero label-dependent calibration events and no score threshold;
4. >=24 scannable bins/year;
5. component member ids resolve only to the correct target-excluded year corpus;
6. reduced 3-D prefilter uses only necessary metric terms and circular solar duplication;
7. every accepted event contact passes exact frozen `D <= 1.5`;
8. every component edge has an exact member-pair witness;
9. no same-year direct edge;
10. support-contact adjacency differs non-vacuously from fixed-centroid v8 adjacency;
11. >=100 recurrent families;
12. every recurrent family spans both years;
13. >=72 qualified known showers after rankings freeze;
14. exact v8 pooled-centroid semantics and single-component equivalence;
15. all local episodes exactly 128;
16. Brown equivalence <=1e-10;
17. all four rankings frozen before first shower-label evaluation.

## Scientific promotion gates

All must pass:

1. persistence recovery@100 >=55;
2. multiplicity recovery@100 >= Brown +1;
3. multiplicity recovery@100 >= ceil(0.90 × persistence recovery@100);
4. **multiplicity recovery@100 >=59**, a strict improvement over passed-v8 multiplicity 58 and at least a tie with passed-v8 persistence 59;
5. multiplicity top-100 dominant precision >=0.68;
6. multiplicity MRR >=0.045531138942766655, the exact passed-v8 multiplicity MRR.

Verdict is `PASS_EXACT_SUPPORT_CONTACT_V11_DEVELOPMENT` only if every integrity and scientific gate passes. Otherwise `FAIL_EXACT_SUPPORT_CONTACT_V11_DEVELOPMENT`, and this exact support-contact formulation becomes a permanent no-go.

A pass promotes only a successor for separately frozen independent validation. It does not authorize OrbitTrace reveal or a target-containing discovery scan.
