# Phase-intensity-equalized recurrent-EOM HDBSCAN v1 — frozen GMN development protocol

## Scientific role

This is a separately motivated successor to promoted recurrent-EOM HDBSCAN v1. It is frozen before its first technically valid GMN 2022/2023 outcome.

The motivation is independent of any external-validation result: meteor-background discrimination is known to vary with solar longitude, while density-based clustering assumes that distances are interpreted against a single pooled density geometry. The successor tests whether a label-free cumulative-intensity reparameterization of **accessible solar phase only** can reduce seasonal/exposure-density distortion while preserving the recurrent-EOM hierarchy/extraction logic.

This protocol does not use or inspect ASFN, EFN, AMOS, SonotaCo, MAARSY, DMS, OrbitTrace target information, or protected-region events. External outcomes may not be used to alter this method.

## Immutable parent

The scientific parent is exact promoted recurrent-EOM HDBSCAN v1:

- recurrent-EOM source Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- promoted GMN development runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- development years exactly `2022,2023`;
- inclusive blind exclusion `[20.0,55.0]` before detector geometry/truth;
- raw parent representation `GEO6 = (cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM cluster selection;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- annual EOM contribution divided by accessible annual event count;
- recurrent stability = minimum of the two annual normalized EOM contributions;
- exact HDBSCAN `get_clusters` extraction on the resulting recurrent stability;
- recurrent ranking = descending recurrent stability, descending ordinary stability, descending member count, deterministic family ID.

The parent method itself is not refit/tuned from this successor's result.

## Sole scientific change: pooled empirical phase-intensity equalization

Only after the inclusive `[20.0,55.0]` blind exclusion has already removed protected events, define the accessible circular solar-longitude arc from `55 deg` forward through `360/0 deg` to `20 deg`. Its fixed angular length is:

`L = 360 - (55 - 20) = 325 deg`.

For every accessible pooled GMN 2022/2023 event with raw solar longitude `sol`, define the unwrapped accessible-arc coordinate:

`s = (sol - 55) mod 360`.

Because the blind interval is inclusive, every scientifically usable event must satisfy strictly:

`0 < s < 325`.

Let the pooled accessible sample contain `N` events. The phase warp uses **only the pooled vector of raw accessible solar longitudes**; year, radiant, velocity, event identity, labels, known-shower information, candidate information, parent scores, and external-survey information cannot enter the transform.

For each distinct value `s0`, let:

- `lo(s0)` = number of pooled accessible events with `s < s0`;
- `hi(s0)` = number of pooled accessible events with `s <= s0`.

Define the deterministic empirical mid-distribution value:

`u(s0) = (lo(s0) + hi(s0)) / (2N)`.

All exact ties therefore receive the same value. No jitter is allowed.

Map back onto the **same 325-degree accessible arc**:

`s_eq = 325 * u(s)`

`sol_eq = (55 + s_eq) mod 360`.

Since `0 < u < 1`, every transformed point remains outside the protected `[20,55]` interval and the protected 35-degree gap remains a geometric gap rather than being compressed away.

The successor representation is exactly:

`GEO6_PHASE_EQ = (cos(sol_eq), sin(sol_eq), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72)`.

All non-phase GEO6 coordinates are byte-for-byte numerically inherited from the same normalized event rows.

## Why pooled rather than year-specific equalization

The pooled HDBSCAN hierarchy is built on the pooled two-year point process, so the transform normalizes the marginal solar-phase intensity of the exact pooled clustering universe. A year-specific warp would give the same physical solar longitude a different coordinate in 2022 and 2023 and would directly alter the meaning of cross-year recurrence. It is therefore prohibited.

No equal-year averaging, annual CDF blend, exposure model, smoothing, kernel bandwidth, histogram binning, spline, density estimator, clipping, regularization, or learned mapping is permitted.

## Successor HDBSCAN / recurrent-EOM extraction

Fit one HDBSCAN hierarchy to `GEO6_PHASE_EQ` using the exact parent HDBSCAN settings above.

On that hierarchy:

1. compute ordinary HDBSCAN EOM stability exactly as the parent does;
2. compute annual normalized EOM contribution using exact event years and the parent recurrent-EOM implementation;
3. recurrent stability is the minimum annual normalized contribution;
4. extract the flat clustering using the exact recurrent-EOM `get_clusters` path;
5. rank candidates with the exact parent recurrent ranking rule.

No parent/successor fusion, fallback, union, reranking, family matching, or score blending is allowed.

## Prelabel boundary

Before any known-shower label value is opened, persist and hash-freeze at minimum:

- exact event counts by year;
- exact ordered pooled event-ID hash;
- raw solar-longitude vector SHA-256;
- unwrapped accessible-arc vector SHA-256;
- equalized solar-longitude vector SHA-256;
- exact `GEO6_PHASE_EQ` array SHA-256;
- equalized hierarchy / condensed-tree identity;
- selected recurrent-EOM nodes;
- every candidate membership;
- ordinary and recurrent candidate scores;
- complete deterministic candidate order;
- transform invariants and source identities.

Only after the complete successor prelabel payload is durable may the already-frozen promoted-parent artifacts and sealed GMN shower truth be opened for comparison/evaluation.

## Frozen development comparison and gate

Compare against promoted recurrent-EOM HDBSCAN v1, not v31 and not vanilla HDBSCAN.

The exact promoted parent artifacts must be reproduced against the same current target-excluded GMN event IDs before the result is accepted.

For **each** of 2022 and 2023, the successor must satisfy all of:

1. recovered@50 >= recurrent-EOM parent;
2. recovered@100 >= recurrent-EOM parent;
3. top-100 dominant precision >= recurrent-EOM parent;
4. MRR >= recurrent-EOM parent;
5. median top-500 fragmentation <= recurrent-EOM parent.

Across the two years:

6. recovered@100 must be strictly higher than recurrent-EOM in at least one year;
7. the successor's ordered candidate membership universe must differ from the parent's (`mechanism_active=true`);
8. the phase transform must be non-identity on the real pooled input.

PASS token:

`PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT`

Otherwise:

`FAIL_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT`.

The first technically valid outcome is binding.

## Permanently prohibited variants / rescue

Do not search or change after the first valid outcome:

- CDF origin other than fixed `55 deg`;
- accessible arc length other than exact `325 deg`;
- pooled versus per-year/equal-year transform;
- empirical-CDF tie rule;
- smoothing or bandwidth;
- histogram/bin count;
- blending raw and equalized solar longitude;
- partial equalization strength;
- alternate monotone transforms;
- HDBSCAN parameters;
- GEO6 non-phase dimensions or velocity scale;
- recurrent annual combiner or annual weights;
- ranking or tie-breakers;
- truth eligibility/overlap/precision rules;
- budgets or evaluation metric;
- parent/successor fusion;
- survey-specific calibration.

A valid failure permanently closes this exact successor. No outcome-informed variant is authorized.

## Firewall declarations

Every synthetic/prelabel/result artifact must assert as appropriate:

- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_2013_2014_access=false`;
- `amos_scientific_access=false`;
- `efn_scientific_access=false`;
- `asfn_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
