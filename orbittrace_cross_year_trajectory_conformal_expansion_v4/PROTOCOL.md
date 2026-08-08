# OrbitTrace cross-year trajectory-conformal expansion v4 — frozen development protocol

## Purpose

v1–v3 established a stable result on the exact target-excluded promoted-v8 family universe: v8's recurrent families are useful high-purity discovery seeds, but treating the seed event union as final membership severely under-recovers known streams. Radius-only expansion (v1), absolute two-witness expansion (v2), and family-density-normalized second-neighbor expansion (v3) all produced large membership-F1 gains, while v3 materially repaired overexpansion and restored the precision gate. v3 still failed recovery/qualified non-regression and narrowly missed the required annual mean-F1 gains.

The remaining geometric mismatch is phase evolution. A meteor stream may change radiant and geocentric speed systematically with solar longitude. v1–v3 can only accept events near discrete source seeds and do not use the recurrent family to predict that drift.

v4 tests one cross-year trajectory-residual successor. It keeps the exact v8 discovery/ranking stage unchanged and uses the original v8 seed family from the **other year only** to fit a deterministic linear radiant/speed trajectory versus solar longitude. Target-year events are evaluated by their residual from that independently fitted trajectory and a leave-one-out conformal calibration derived only from the source-year seeds.

## Relation to preserved drift no-gos

This is not a resurrection of the killed affine/radiant-drift quartet detectors (PRs #81, #118, #126).

Those methods changed the **detection statistic** by fitting a trajectory from each 4-event candidate quartet; the fit was too flexible for background and too brittle for four noisy meteors. v4 does neither:

- v8 detection, components, recurrence, scores, and ranking are frozen before v4 membership begins;
- the fitted object is an already-recurrent multi-event v8 family, not an arbitrary quartet;
- the fit is trained only on original seeds from the other year and evaluated on the target year;
- trajectory fit quality is calibrated by source-seed leave-one-out residuals before labels are consulted;
- a v4 failure does not reopen any earlier drift-detector formulation.

## Frozen base and prerequisites

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Reproduce exactly 226 v8 recurrent families, pooled-year centroids, 128-event scores, multiplicity order, and passed-v8 pre-expansion metrics.
- v3 run `31235705928`, artifact `9015557724`, digest `sha256:f702124b40452624ffc7210e52978e6d9622e60f0a000af3299abda81e3fa7d7` is an immutable no-go prerequisite and must be verified before v4 scientific-value access.
- Preserve v1/v2/v3 no-go conclusions; no alpha/radius/witness-count/neighbor-order tuning is permitted.
- v8 proposals, components, family graph, original membership, centroids, scores, and ranking remain unchanged.

## Frozen trajectory membership rule

For each family and target year independently:

1. use only the family's original v8 seed events from the **other year** as the source sample;
2. require the inherited minimum of four source seeds; no family is selected by label or score;
3. compute the source circular-mean solar longitude `sol0` and circular-mean Sun-centered longitude `lon0`;
4. unwrap each source solar longitude as `x = wrap180(sol - sol0)` and each source Sun-centered longitude as `y_lon = wrap180(sun_lon - lon0)`;
5. fit ordinary least-squares affine functions of `x` for `y_lon`, ecliptic latitude, and geocentric speed, each with intercept and slope. No slope bound, regularizer, robust-loss option, polynomial order, or model family is searched;
6. for each source seed, refit the same three affine functions after leaving that seed out and calculate the held-out trajectory residual;
7. for a target-year event, require solar longitude to lie inside the source family's minimum circular activity arc expanded by exactly the already-inherited v1–v3 necessary prefilter of 6° on each side; this prefilter alone can never accept an event;
8. evaluate the full-source trajectory at the target event's solar longitude and calculate the exact residual metric
   `R = sqrt((wrap180(lon-lon_hat)*cos((lat+lat_hat)/2)/2)^2 + ((lat-lat_hat)/2)^2 + ((vg-vg_hat)/2)^2)`;
   solar longitude is the independent phase variable and is therefore not included again in the residual;
9. retain an inherited hard residual-coherence ceiling `R <= 1.5` and compute the conservative conformal p-value
   `p = (1 + #{source LOO residual >= target residual}) / (n_source + 1)`;
10. accept the family-event pair only when `p > 0.05`;
11. if one event is accepted by multiple families, assign it exclusively to the family with smallest residual `R`, ties by stable family ID;
12. newly assigned events never become training support and original v8 seeds are never removed.

Alpha `0.05`, affine order 1, the inherited 6° activity prefilter, and the inherited residual ceiling 1.5 are frozen before execution. No alternatives are evaluated.

## Prohibited alternatives

Do not test from this result:

- another conformal alpha;
- constant, quadratic, spline, robust, piecewise, or regularized trajectory fits;
- slope caps or hand-set physical drift bounds;
- another activity-arc padding;
- another residual radius or coordinate weighting;
- same-year training, recursive growth, family-size caps, score-weighting, orbital/D_SH membership, or reranking;
- per-family fallback rules selected after labels.

Failure closes this exact cross-year affine-trajectory conformal membership architecture and does not authorize parameter tuning.

## Development panel and blindness

- Exact target-excluded GMN 2022 + 2023 development corpus inherited from v8.
- Solar longitude 20°–55° is removed before proposals, labels, scoring, or evaluation by the frozen parser.
- Exact v8 rankings and the complete v4 expanded-membership payload are SHA-256 frozen before known-shower labels are evaluated.
- No OrbitTrace coordinate, identity, member, target-region event, Stage A/B output, or reveal may be accessed.
- The already-seen literature benchmark is not used to choose a v4 constant or fit.

## Scientific gates

Reuse the exact v1–v3 promotion standard without relaxation:

1. multiplicity recovery@100 after expansion `>= 58`;
2. qualified matches after expansion `>= 95`;
3. top-100 dominant precision after expansion `>= 0.65`;
4. expanded macro F1 `>= v8 macro F1 + 0.05`;
5. all-shower annual mean-F1 gain `>= +0.10` in both 2022 and 2023;
6. 4–9 annual mean-F1 delta `>= -0.02` in both years;
7. at least one moderate/large bin (10–24, 25–49, 50–99, 100+) has mean-F1 gain `>= +0.10` in both years.

All exact-v8 reproduction, other-year-only fit, leave-one-out calibration, alpha=0.05, affine-order-1, inherited-arc, inherited-residual-ceiling, no-recursion, exclusive-assignment, pre-label-hash, exact-128-episode, Brown-equivalence, and target-exclusion integrity gates must pass.

## Decision rule

Promote v4 only if every integrity and scientific gate passes in this single frozen execution. Otherwise preserve it as a no-go. A pass authorizes only separately frozen prospective validation followed by matched literature comparison; it does not authorize OrbitTrace reveal by itself.
