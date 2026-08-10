# OrbitTrace density-capped multiplicity v13 — target-excluded development protocol

## Purpose

This is a **new successor method** motivated only by the established external architectural fact that a fixed 128-event local episode is not portable to every survey panel. It does not modify, rescue, or reinterpret frozen #839/v8.

Development is restricted to target-excluded GMN data. SonotaCo 2013/2014, all historical result-bearing SonotaCo benchmark branches, MAARSY scientific data, the OrbitTrace target region, and OrbitTrace target identity/coordinates/members remain inaccessible.

## Single scientific change

Retain the exact frozen v5/v8 proposal generation, recurrent-family construction, Brown geometry, multi-anchor-v3 geometry, and multiplicity definition

`M = (multi_anchor_v3_energy / Brown_peak)^2`.

Replace only the fixed-cardinality local-episode rule:

- old: require at least 128 local events and select the nearest 128;
- v13: let `N` be the number of events in the unchanged local window and select the nearest `K = min(128, N)` events;
- the scorer already requires at least four finite events because there are four top anchors; `N < 4` fails closed;
- no family is deleted merely for having fewer than 128 local events;
- no window widening, imputation, resampling, duplicated events, density-derived weight, new score term, or label-dependent rule is allowed.

The primary ranking remains exactly:

1. descending worst-year multiplicity;
2. descending geometric-mean multiplicity;
3. stable family ID.

Absolute Brown and v3 amplitudes are not added to the primary ranking.

## Why variable cardinality is testable without a new amplitude normalization

The frozen multiplicity is a ratio. For one episode, Brown is the largest leave-one-out coefficient and multi-anchor v3 is the L2 energy of the four largest positive coefficients. Therefore the common coefficient scale cancels in `M`, which remains bounded in `[1,4]`. The development question is not amplitude calibration; it is whether lower cardinality makes the ratio too noisy to preserve useful ranking performance.

## Development data and firewall

Use the already-established target-excluded GMN 2020/2021 development/holdout machinery only. Solar longitude 20°–55° must be removed by the frozen source before labels enter evaluation.

No SonotaCo 2013/2014 row, count, family, comparator output, shower label, score, or result may be loaded by this branch. Do not inspect PR #351 or other historical result-bearing external benchmark payloads while v13 is under development.

Known-shower labels may be consulted only after every candidate family and ranking for a stress run has been frozen in memory/output.

## Predeclared cardinality stress test

The final v13 rule is adaptive `K=min(128,N)`; the following are **stress tests, not selectable models**. Run the same target-excluded 2020/2021 family universe at exact global episode caps:

- 128 — identity control;
- 96;
- 64;
- 32.

No cap is chosen by performance. All lower-cardinality stress conditions must pass. The 32-event floor for the stress panel is pre-existing in the frozen multi-anchor-v3 self-test; it is not a final-method minimum.

Additionally run synthetic scorer-only checks at episode sizes 4, 8, 16, 32, 64, 96, and 128 to require finite scores, Brown equivalence, permutation invariance, and `1 <= M <= 4`.

## Frozen gates

### Integrity gates

All must pass:

1. cap-128 execution exactly reproduces the direct frozen-v5 multiplicity family universe and multiplicity order;
2. every stress run uses the identical recurrent-family universe;
3. Brown-equivalence difference is <= `1e-10` for every scored episode;
4. every episode uses exactly `min(cap, N_local)` nearest events and no duplicated/imputed event;
5. no target-region, SonotaCo 2013/2014, MAARSY, or OrbitTrace target access occurs;
6. labels enter only after rankings exist.

### Scientific robustness gates

Let cap 128 be the development reference. For **each** of caps 96, 64, and 32:

1. multiplicity recovered@100 must be at least `ceil(0.90 * cap128_recovered_at_100)`;
2. multiplicity MRR must be at least `0.90 * cap128_MRR`;
3. top-100 dominant precision must be at least `0.50`;
4. top-100 dominant precision may fall by at most `0.05` absolute from cap 128;
5. qualified-known-shower count must equal cap 128 because the family universe is unchanged.

There is no search over these gates, no best-cap selection, and no second contingency.

## Decision rule

- If every integrity and robustness gate passes: `PASS_DENSITY_CAPPED_MULTIPLICITY_V13_TARGET_EXCLUDED_DEVELOPMENT` and the adaptive cardinality rule may be frozen for later independent validation.
- Otherwise: `FAIL_DENSITY_CAPPED_MULTIPLICITY_V13_TARGET_EXCLUDED_DEVELOPMENT` and v13 is a permanent no-go in this form.

A pass does **not** authorize reuse of SonotaCo 2013/2014 as an external validation set. A later v13 external test must use a different untouched dataset and must be separately preregistered before any scientific access.
