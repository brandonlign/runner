# OrbitTrace v15 label-free v8 deployment qualification v1

## Purpose

Qualify the intended survey-portable end-to-end detector before any further SonotaCo or MAARSY use:

`canonical event rows -> exact promoted v8 label-free family graph -> exact v8 pooled same-year centroids -> frozen v15 nominal-128 multiscale consensus`.

This is not a parameter search and does not replace any dataset. It resolves an implementation-boundary issue discovered during canonicalization: the historical v15 development harness inherited the older v5 GMN scanner, whose calibration pool was selected from rows labeled `SPORADIC`. That historical v15 result remains valid for its frozen 92-family development universe, but that scanner is not an acceptable survey-independent pre-truth family generator. The promoted v8 architecture already contains the required label-free generator and is therefore the only allowed family-generation binding here.

The qualification uses only already-exposed, target-excluded GMN 2022/2023 development data. SonotaCo 2013/2014, MAARSY event values, DMS, the OrbitTrace target interval, and OrbitTrace target information remain inaccessible.

## Frozen end-to-end method

### Canonical input

Every event is first projected through `orbittrace_v15_canonical_events_v1` to exactly:

`id, year, sol, sun_lon, ecl_lat, vg, iau=0, complex_key=HIDDEN`.

Years are exactly 2022 and 2023 for this qualification. No survey-conditioned science may occur after this boundary.

### Proposal / family layer

Use the exact promoted v8 sources from commit `c9d6c44704013ba0c9430100e98a29a56b453304`:

1. exact v6 `label_free_scan_year` within each year;
2. no calibration events and no score threshold;
3. exact fixed4 64/128 shortlist audit, anchor multiplicity >=2, top-512/bin cap;
4. exact frozen within-year component construction;
5. exact cross-year connected-family graph with link radius 1.5;
6. exact v8 pooled same-year centroid repair using circular mean for `sol`/`sun_lon` and median for `ecl_lat`/`vg`.

The family graph must contain exactly the frozen v8 count of 226 recurrent families. No P19, P20, URC ranker, halo, support rescue, new radius, or alternate recurrence rule is permitted.

### v15 rank layer

Use the merged common application without survey branches. Final deployment remains nominal 128 with component caps exactly `(128, 96, 64)`.

For each family/year/cap:

- unchanged 10-degree local window;
- `k=min(cap,N_local)`, fail closed only when `k<4`;
- exact frozen wavelet distance and stable nearest-event selection;
- exact multiplicity `(multi-anchor-v3 / Brown)^2` with Brown-equivalence <=1e-10.

Each component order is descending worst-year multiplicity, descending geometric-mean multiplicity, stable family ID. Final v15 order is ascending median zero-based rank across 128/96/64, then r128, r96, r64, family ID.

## Pre-truth boundary

The canonical rows, v8 proposals, components, families, pooled centroids, all three component orders, and final v15 order must exist before known-shower truth is evaluated.

The v8 parser may return its historical hidden-label mapping, but the qualification runner may not read that mapping until the final v15 order and direct frozen-v8 identity control order are frozen in memory.

## Exact v8 identity control

Before interpreting v15 performance, the same run must reproduce the frozen v8 2022/2023 baseline from run `31217916558`:

- recurrent families: 226;
- qualified known showers: 95;
- direct fixed-128 multiplicity recovered@100: 58;
- direct fixed-128 multiplicity MRR: `0.045531138942766655`;
- direct fixed-128 top-100 dominant precision: `0.6884631112636006`.

The common application's cap-128 component order must be exactly identical to the direct frozen-v8 multiplicity order generated in the same pre-truth run.

Any failure of this control is `FAIL_V15_LABEL_FREE_V8_DEPLOYMENT_INTEGRITY`, not a reason to alter the canonical schema or method.

## Predeclared preservation gates

Because the only intended scientific change relative to promoted v8 is the already-frozen v15 rank consensus, the final v15 order must preserve full-cardinality v8 performance using the same preservation standard used when v15 was developed:

1. recovered@100 >= 58;
2. MRR >= `0.95 * 0.045531138942766655 = 0.04325458199562832`;
3. top-100 dominant precision >= `0.6884631112636006 - 0.05 = 0.6384631112636006`;
4. qualified-known-shower count exactly 95;
5. family universe remains exactly the same 226 promoted-v8 families.

No gate or method component may be changed after execution.

## Decision rule

- all source/firewall/integrity controls and all preservation gates pass:
  `PASS_V15_LABEL_FREE_V8_DEPLOYMENT_QUALIFICATION`
- source/family/direct-v8 identity control fails:
  `FAIL_V15_LABEL_FREE_V8_DEPLOYMENT_INTEGRITY`
- identity controls pass but one or more preservation gates fail:
  `FAIL_V15_LABEL_FREE_V8_DEPLOYMENT_PERFORMANCE`

A PASS qualifies one survey-independent label-free detector implementation for the next **SonotaCo engineering-applicability** stage. It is not a new external-validation result, does not make SonotaCo pristine again, and does not authorize MAARSY event access or OrbitTrace reveal.

## Explicit exclusions

- no DMS or replacement dataset;
- no new GMN year selection;
- no v5 SPORADIC-label calibration in the deployed family generator;
- no survey-specific detector branch;
- no SonotaCo or MAARSY scientific access;
- no target-region or OrbitTrace target access;
- no parameter/radius/cap/threshold/weight/model search.
