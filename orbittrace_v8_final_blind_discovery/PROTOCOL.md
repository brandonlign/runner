# OrbitTrace v8 final target-free GMN blind discovery protocol

## Status and scientific boundary

This document freezes the final catalogue-wide discovery application of the already-promoted **v8 pooled-year-centroid label-free sparse-support multiplicity** method. It is a preregistration and firewall specification only. It does **not** authorize or execute the target-containing GMN scan and it does **not** load, inspect, identify, or reveal the withheld OrbitTrace reference.

The scientific parent is exactly commit `c9d6c44704013ba0c9430100e98a29a56b453304` (PR #321). The passed v8 development artifact is `9009728299`, ZIP digest `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`, verdict `PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT`.

The final branch is forked directly from that v8 commit. The v9 support-overlap successor is excluded. The older `orbittrace-wavelet-catalogue-v3-postpass` preparation branch is also excluded because it diverged from an older lineage and does not define v8. The old fixed4 blind-catalogue/reveal implementation is not reused as a detector or ranking implementation. Only two procedural choices that were frozen before its old reveal are inherited unchanged: the GMN month coverage and the top-25/full, top-100/partial reveal depths. No old target match, target family, target rank, target coordinate, target member, or old reveal artifact may be read by Stage A.

## 1. Exact GMN input universe

Stage A uses exactly **55 official GMN monthly trajectory files** in chronological order:

- every month `2022-01` through `2022-12`;
- every month `2023-01` through `2023-12`;
- every month `2024-01` through `2024-12`;
- every month `2025-01` through `2025-12`;
- `2026-01` through `2026-07` only.

No later 2026 month may be added even if available at execution time. No 2019-2021 month may be added. The exact raw byte count, SHA-256, raw row count, selected geometry-valid row count, duplicate count, and resolved source-column names are written for every month before family evaluation.

Stage A is intentionally target-containing. Therefore the development-only solar-longitude exclusion is **not applied** during Stage A. This is the sole intended catalogue-access difference from target-excluded development; it is fixed here before external-validation authorization.

## 2. Exact quality cuts and duplicate handling

Only the geometry fields required by the frozen method are used. Stage A does not normalize, read, filter, or rank by shower identity.

For each row, resolve the same GMN columns as the audited v6/v8 support source:

- trajectory ID: shortest column matching `unique + trajectory + identifier`, else `trajectory + identifier`;
- solar longitude: `sol + lon + deg`, else `solar + longitude`;
- geocentric ecliptic longitude: `lamgeo + deg`, else `geocentric + ecliptic + longitude`;
- geocentric ecliptic latitude: `betgeo + deg`, else `geocentric + ecliptic + latitude`;
- geocentric speed: `vgeo + km + s`, else `geocentric + velocity`.

After numeric coercion, retain a row iff all four numeric quantities are finite and all of the following hold inclusively:

- `0 <= sol <= 360` degrees;
- `0 <= lam_geo <= 360` degrees;
- `-90 <= beta_geo <= 90` degrees;
- `5 <= Vg <= 75` km/s.

There is no convergence-angle cut, uncertainty cut, orbital-element cut, shower-label cut, SPORADIC-only cut, activity-region cut, or target-specific cut in the final label-free scan.

Trajectory IDs are deduplicated in the frozen monthly chronological order. The first geometry-valid occurrence is retained and every later occurrence is removed.

## 3. Event coordinate transformation and frozen geometry

For every retained event:

- `sol` is the GMN solar longitude in degrees;
- `sun_lon = wrap180(lam_geo - sol)` in degrees;
- `ecl_lat = beta_geo` in degrees;
- `vg = Vg` in km/s.

The exact fixed4 distance between event/centroid records `a,b` is

`D = sqrt(dsol^2 + dlon^2 + dlat^2 + dvg^2)`

with

- `dsol = wrap180(sol_b-sol_a)/4`;
- `dlon = wrap180(sun_lon_b-sun_lon_a) * cos((ecl_lat_a+ecl_lat_b)/2) / 2`;
- `dlat = (ecl_lat_b-ecl_lat_a)/2`;
- `dvg = (vg_b-vg_a)/2`.

Angles inside the cosine are converted to radians. This is the exact frozen 4-degree/2-degree/2-km-s geometry inherited from the support source.

## 4. Exact fixed4 label-free proposal generation

For each year independently and each 10-degree solar-longitude bin `b=0..35`:

- `low=10b`, `high=10(b+1)`, `center=low+5`;
- anchors are all events with `low <= sol < high`;
- the proposal pool contains all same-year events with `abs(wrap180(sol-center)) <= 15` degrees;
- a bin is scannable only if it has at least one anchor and at least 128 pool events.

The Euclidean nearest-neighbour prefilter uses the exact feature matrix:

- `wrap180(sol-center)/4`;
- radiant Cartesian unit-vector coordinates multiplied by `(180/pi)/2`;
- `vg/2`.

`NearestNeighbors(metric='euclidean', algorithm='auto', n_jobs=-1)` requests 128 neighbours. For each anchor, the anchor itself is removed. The first shortlist uses the first 63 remaining candidates (the frozen shortlist-64 convention including the query point), then exact fixed4 distances are stably sorted and the three closest events are joined to the anchor.

The quartet score is the negative maximum of all exact pairwise fixed4 distances among the four events.

Every proposed quartet is independently audited against the first 127 remaining candidates (the frozen audit-shortlist-128 convention). If IDs or score differ by more than `1e-12`, the audited quartet and audited score replace the first result. This audit is deterministic and cannot remove a quartet by a score threshold because **v8 proposal generation has no calibration or detector-score threshold**.

Within a year/bin, quartets are deduplicated by the sorted four trajectory IDs. Anchor multiplicity is accumulated and the retained score is the maximum observed quartet score. A quartet is retained only when `anchor_count >= 2`.

Before the fixed cap, quartets are sorted by:

1. anchor count descending;
2. quartet score descending;
3. sorted quartet-ID tuple ascending.

Retain exactly the first at most 512 quartets per year/bin. For retained rank `r` among `n` retained quartets, define

`bin_strength = -log10((r-0.5)/n)`.

No label, target datum, calibration p-value, threshold, alternative cap, alternative shortlist, or post-result selection may enter proposal generation.

## 5. Exact within-year component construction

Each retained quartet contributes all six undirected edges among its four event IDs. Within each year, connected components of this event graph are constructed by the inherited v6 source.

A component is retained iff it contains:

- at least 4 distinct events; and
- at least 2 distinct retained quartets.

For each component:

- event IDs are unique and sorted;
- `component_strength = sum(bin_strength of supporting quartets) / sqrt(number of supporting quartets)`;
- `sol` centroid = circular mean of event `sol`;
- `sun_lon` centroid = circular mean of event `sun_lon`;
- `ecl_lat` centroid = median event `ecl_lat`;
- `vg` centroid = median event `vg`;
- quartet count, summed anchor count, best quartet score, median quartet score, and solar span are preserved.

Component ordering/IDs use the exact inherited v6 implementation. Stage A runs with `PYTHONHASHSEED=0` so set traversal and any otherwise equivalent serialization are reproducible.

## 6. Exact v6 connected-family semantics

Consider every pair of retained components from **different** years. Add an undirected cross-year edge iff the exact centroid distance defined in section 3 is `<= 1.5`.

No same-year direct edge is added. Recurrent families are ordinary connected components of this cross-year component graph. Therefore transitive closure is binding, and multiple components from the same year may coexist in one family through cross-year paths. The failed v7 one-component-per-year topology and failed v9 support-overlap adjacency are forbidden.

A family is retained iff it spans at least **2 distinct years**.

The family record inherits exact v6 semantics:

- union of unique event IDs;
- sorted component IDs;
- `family_id = 'G' + sha256('|'.join(sorted_component_ids))[:12]`;
- `year_strength[year] = max(component_strength among that family's components in that year)`;
- total component/event/quartet/anchor counts and best quartet score are preserved.

The label-free persistence ranking may be serialized as a structural diagnostic only. It cannot replace or modify the v8 multiplicity ranking.

## 7. Exact v8 pooled same-year centroid repair

After the v6 family graph, IDs, event unions, and all non-centroid structure are frozen, apply the sole v8 repair.

For each `(family, year)` represented in that family:

1. collect every component in that family from that year;
2. form the union of their unique event IDs;
3. retrieve those events from the same-year Stage A scan corpus;
4. recompute one pooled family-year centroid using:
   - circular mean `sol`;
   - circular mean `sun_lon`;
   - median `ecl_lat`;
   - median `vg`.

No component-centroid averaging, weighting, medoid, radius adjustment, one-to-one matching, or alternate pooling rule is allowed. For a family-year containing exactly one component, pooled and original component centroids must agree within `1e-12` in the frozen centroid distance.

The repair is forbidden from changing family membership, family/component/event IDs, counts, year support, structural strengths, or persistence order.

## 8. Exact 128-event local episode construction

For every retained family and every year that family supports, let the pooled family-year centroid be the synthetic episode anchor.

The local temporal window is the frozen wavelet window of width 10 degrees:

`abs(wrap180(event.sol - centroid.sol)) < 5 degrees`.

The strict `<5` boundary is binding. At least 128 same-year scan events must exist in the window.

For every window event, compute the exact frozen wavelet radius

`r^2 = (angular_separation/4deg)^2 + ((Vg-centroid_Vg)/(0.10*centroid_Vg))^2`,

where angular separation is the great-circle radiant separation between `(sun_lon,ecl_lat)` and the pooled centroid radiant.

Select exactly the 128 smallest `r^2` values using the frozen stable selection rule: values below the partition threshold first, then equal-threshold indices in original event order, followed by value/index lexicographic ordering. The episode contains those 128 events' `sun_lon`, `ecl_lat`, and `vg` arrays. No family event is forcibly inserted and no target/member identity is used.

## 9. Exact multiplicity score

On each 128-event family-year episode:

- compute the frozen multi-anchor v3 episode score;
- obtain its `brown_peak`;
- independently compute the frozen Brown-family wavelet episode score;
- require `abs(brown_peak - independent_Brown) <= 1e-10` and Brown > 0;
- define `M_year = (v3 / Brown)^2`.

Every `M_year` must lie in `[1-1e-10, 4+1e-10]`.

No multiplicity p-value, calibration, threshold, RRF, target-specific weighting, support bonus, or score transformation is permitted.

## 10. Exact family ranking and deterministic tie breakers

For a family supported in `n>=2` years, define:

- `M_worst = min(M_year)`;
- `M_geo = exp(mean(log(M_year)))` over **all and only the years supported by that family**.

The exponential mean-log definition is the unique frozen multi-year extension of the two-year geometric mean used in v8 development; for `n=2` it is mathematically identical to `sqrt(M1*M2)`.

The sole primary ranking sorts all recurrent families by:

1. `M_worst` descending;
2. `M_geo` descending;
3. stable `family_id` lexicographically ascending.

Ranks are 1-based and unique. No persistence, event count, year count, target overlap, Brown score, v3 score, family size, old blind rank, or manual inspection may enter a tie breaker.

Stage A must serialize **every** ranked family, not merely the top 25 or top 100.

## 11. Minimum recurrence/support and Stage A integrity gates

Scientific family eligibility is fixed at the inherited structural minima:

- proposal anchor multiplicity >=2;
- <=512 retained quartets per 10-degree year-bin after deterministic ordering;
- component >=4 events and >=2 quartets;
- family >=2 distinct years;
- every scored family-year episode exactly 128 events.

A Stage A execution is valid only if, before any withheld reference is accessed:

- every exact monthly key in section 1 was read exactly once;
- no other monthly key was read;
- no source-label normalization/evaluation occurred;
- at least 24 bins are scannable in every input year;
- at least 100 recurrent families are produced;
- every family score is finite;
- every episode has size 128;
- Brown equivalence is within `1e-10`;
- all Stage A source and parent hashes match the frozen manifest;
- `PYTHONHASHSEED=0` is recorded;
- the complete ranked-family payload is hashed before Stage A terminates.

Failure of any integrity gate invalidates the run. It does not authorize a scientific-rule change.

## 12. Catalogue/rank depth defining independent recovery

The Stage A catalogue itself includes all families. The reveal endpoint is inherited unchanged from the old pre-reveal firewall and is not selected using any old recovery result:

- **full independent recovery depth: rank <=25**;
- **partial recovery depth: rank <=100**;
- a family ranked >100 cannot produce a positive or partial recovery verdict and is descriptive only.

There is no top-k search and no rank-depth sensitivity analysis that can replace these frozen endpoints.

## 13. Post-freeze identification of a withheld-reference-consistent family

Stage A has no reference input and cannot perform matching.

Only after the Stage A ZIP digest and inner ranked-family SHA-256 are frozen may Stage B receive a separate withheld-reference bundle. The reveal interface contains only unique stable GMN event IDs and their years. Stage B intersects each already-frozen family's event-ID set with the withheld-reference event-ID set and computes overlap counts and per-year overlap.

The family list, family IDs, family membership, scores, and ranks are read-only during Stage B. No family merging, splitting, rescoring, reranking, centroid shift, event reassignment, or candidate expansion is allowed.

## 14. Exact reveal matching criterion/tolerance

The primary reveal match is **exact stable GMN trajectory/event-ID equality**.

The matching tolerance is therefore **zero**: an event either has exactly the same identifier in the frozen family and withheld reference or it does not match.

Radiant, speed, orbit, activity peak, solar longitude, D-criterion, nearest-neighbour tolerance, coordinate tolerance, and historical HDBSCAN assignments are forbidden from the recovery classification. They may not rescue a failed exact-ID match.

If more than one family satisfies a verdict class, the reported family is the one with the best already-frozen blind rank; remaining ties are broken by larger exact overlap, then larger overlap/family-size precision, then `family_id` lexicographically ascending. These rules cannot alter any Stage A rank.

## 15. Frozen full/partial/no-recovery classifications

`FULL_BLIND_INDEPENDENT_RECOVERY` requires at least one already-frozen family satisfying all of:

- blind rank <=25;
- family spans >=4 distinct years;
- exact withheld-reference overlap >=16 events total;
- at least 4 exact withheld-reference events in each of >=3 distinct years.

`PARTIAL_BLIND_INDEPENDENT_RECOVERY` applies only if no family passes the full rule and at least one already-frozen family satisfies all of:

- blind rank <=100;
- family spans >=3 distinct years;
- exact withheld-reference overlap >=12 events total;
- at least 4 exact withheld-reference events in each of >=2 distinct years.

`NO_BLIND_INDEPENDENT_RECOVERY` applies otherwise.

Precision (`overlap/family_event_count`), reference recall (`overlap/reference_event_count`), and all overlap distributions are reported descriptively. They are not substitute gates. No statistical enrichment test can replace the classification.

## 16. Immutable hashes and provenance required before target-region/reference access

The following upstream objects are frozen prerequisites:

- v8 scientific parent commit: `c9d6c44704013ba0c9430100e98a29a56b453304`;
- passed v8 development artifact digest: `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- v8 protocol SHA-256: `ff906238ab80453c4e7d78153fafeeaeb7e948e9be133b1f25f9e2f0de3bee30`;
- v8 development source SHA-256: `0632e728f9c237ce9beac3c5804bc8fde6525203470853395716944b17bd4a8a`;
- inherited v6 source SHA-256: `5c1ed5606c9a5351b93f9475a1bfc82bed90c2d9dcfc384ea580dd6d344e9a48`;
- multiplicity-v5 scoring source SHA-256: `fd9526ecb75751b6fb0e936fe5dd237a77c406b729c96ecd9b24aba634b0f43f`;
- frozen wavelet-catalogue runtime SHA-256: `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`;
- fixed4 support source SHA-256: `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`;
- multi-anchor v3 source SHA-256: `f80676974804768cb1994ef1b8de3ad551028c934c8759d247db915a3925fe91`;
- independent Brown comparator SHA-256: `5ef0f7b33a1c3ed87885ee70be0cdd184055d819eb1196c65eebc7e867f747e2`;
- decoded fixed4 candidate source SHA-256: `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`;
- decoded baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- decoded scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

The new freeze branch's protocol, Stage A runner, Stage B runner, source audit, and workflow files must also be SHA-256 recorded in `FREEZE_MANIFEST.json` before any target-containing execution. Stage A records its own Git commit SHA, environment, package freeze, all 55 raw GMN source hashes, complete ranked-family payload hash, and source manifest.

## Two-stage firewall

### STAGE A — BLIND DISCOVERY

Stage A can start only after a separate external-validation authorization artifact passes the frozen authorization schema. Until that artifact is supplied, the target-containing workflow is operationally blocked.

Stage A may access the exact target-containing GMN months in section 1 but receives **no withheld-reference artifact, member list, target coordinates, target identity, expected radiant/speed/orbit, historical HDBSCAN output, or prior reveal output**. It constructs and freezes all family records and the complete v8 multiplicity ranking. The Stage A artifact explicitly records `withheld_reference_loaded=false` and an inner SHA-256 of the canonical ranked payload.

### STAGE B — REVEAL

Stage B is a separate workflow/process. It first downloads and verifies the immutable Stage A artifact and inner ranked payload **before** it is permitted to download a withheld-reference bundle. Only then does it load the exact-ID reference and apply sections 13-15 mechanically.

Stage B cannot call detector code, GMN catalogue loaders, family builders, centroid code, scoring code, or ranking code. It is a pure set-intersection/classification process over immutable Stage A families.

## Forbidden post-authorization decisions

After external validation is known, no scientific choice may change: no year/month expansion, data-quality cut, coordinate transform, proposal threshold, shortlist, cap, component rule, family link rule, centroid rule, episode rule, score definition, rank rule, support minimum, match tolerance, rank depth, or recovery threshold. A technical failure may be repaired only if a source audit proves scientific equivalence and the failed attempt had not emitted a scientifically interpretable Stage A ranking; otherwise the frozen outcome stands.
