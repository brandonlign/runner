# OrbitTrace v62 intrinsic-representation strict-OOF local-geometry margin v1

## Scientific role

This is one separately frozen **SonotaCo 2013/2014 exposed-development successor** to v31. SonotaCo remains exposed development-only, not external validation.

The motivation is fixed before outcome. v31 established that strict whole-shower out-of-fold nearest-reference geometry can beat the literature comparator in 2/4 SonotaCo panels. A later target-excluded GMN diagnostic tested the same nearest-positive / nearest-nonpositive geometry principle on a deliberately intrinsic 23D family representation and passed all preregistered GMN gates: recovered@100 59→66, recovered@50 38→41, top-100 dominant precision 0.6884631112636006→0.7229521515453452, and MRR 0.046734076055452344→0.050244164168646674, with qualified-family count unchanged at 95.

v62 therefore changes **only the family representation** used by the already-frozen v31 geometry machinery. It does not change k, metric, scaling, OOF grouping, annual reference definition, annual combiner, diversity, fusion, memberships, candidate universe, or literature evaluator.

## Immutable candidate universe and pretruth source

Use exactly the immutable v24/v22 SonotaCo pretruth payload already used by v31:

- Sugar candidate universe and memberships unchanged;
- HDBSCAN candidate universe and memberships unchanged;
- exact v19 order unchanged;
- exact centroid arrays unchanged;
- `truth_accessed=false` must hold for the source manifests and memberships before v62 representation construction.

The v22 71D feature matrix is known by construction to be:

`[raw_839 (34), relative_noncat_839 (30), rank_percentiles (3), consensus_graph (4)]`.

The first 34 dimensions are the exact label-free raw URC representation produced before any SonotaCo shower truth is accepted.

## Sole representation change: exact 23D intrinsic subset

Before loading SonotaCo truth, derive the v62 representation by selecting exactly these zero-based columns from the immutable 71D v22 matrix:

- `1..10` inclusive — ten intrinsic structural features:
  - log event count,
  - log anchor count,
  - log quartet count,
  - log component count,
  - best score,
  - minimum annual strength,
  - maximum annual strength,
  - annual-strength balance,
  - member-year balance,
  - cross-year centroid distance;
- `14..20` inclusive — seven exact cohesion features:
  - minimum annual member count,
  - maximum annual member count,
  - member-count balance,
  - all-member median centroid distance,
  - all-member q90 centroid distance,
  - all-member maximum centroid distance,
  - worst annual q90 centroid distance;
- `28..33` inclusive — six exact centroid-neighborhood descriptors:
  - log neighbor counts within the frozen 0.25/0.5/1.0/1.5 centroid distances,
  - nearest-neighbor distance,
  - median distance to the nearest five neighbors.

Equivalently, the immutable column tuple is:

`(1,2,3,4,5,6,7,8,9,10,14,15,16,17,18,19,20,28,29,30,31,32,33)`.

This is the exact cross-domain representation used by the binding GMN PASS, mapped to SonotaCo through the already-frozen portable URC feature definitions. The following raw fields are explicitly excluded: soft/source indicator, hard-rank percentile, soft-support fraction, soft-trigger distance, source one-hot indicators, all P20-only fields, all relative-rank transforms, all prior rank percentiles, and all consensus-graph features.

There is no feature subset search, column replacement, imputation, representation weighting, or post-outcome feature edit.

The complete Sugar and HDBSCAN 23D matrices must be written, hashed, and firewall-verified before SonotaCo truth is loaded.

## v31 machinery retained unchanged

After the 23D pretruth matrices are sealed, use the exact v31 strict-OOF procedure across the stacked Sugar+HDBSCAN family universe:

1. exact deterministic strict-whole-shower five-fold assignment;
2. for each fold and each year separately, compute training-only arithmetic mean and population standard deviation (`ddof=0`) for all 23 features; exactly-zero standard deviations become 1.0;
3. annual positive references are defined exactly as in v31 from the already-frozen literature event `F1_y > 0.5` for the fixed best recurrent label; all other training examples are annual nonpositive references;
4. `k=1` ordinary Euclidean distance to the nearest annual-positive and nearest annual-nonpositive training reference;
5. annual margin `d_nonpositive - d_positive`;
6. exact v31 conservative annual combiner `min(margin_2013, margin_2014)`;
7. route-local exact #839 geometric diversity with `lambda=0.8`, `scale=1.0` and the immutable tie rule;
8. exactly one equal rank-sum fusion with the immutable v19 order.

The fused order is the sole promotion candidate. No intrinsic-only promotion, alternate annual combiner, alternate diversity, rank product, sequential fusion, route-specific rule, or source quota is evaluated.

## Binding gate

The first technically valid v62 execution is binding.

PASS requires the sole fused order to beat the corresponding frozen literature comparator in **all four** Sugar/HDBSCAN × 2013/2014 panels:

- macro-F1 strictly higher than literature; and
- recovered `F1 > 0.5` count at least equal to literature.

Otherwise v62 is permanently rejected. No k, metric, scaling, feature, column, annual reference, annual combiner, diversity, fusion, threshold, source quota, or membership rescue is authorized after the outcome.

v31 remains the parent control and strongest demonstrated SonotaCo method unless v62 passes the frozen 4/4 gate.

## Firewall

- SonotaCo 2013/2014 role: `EXPOSED_DEVELOPMENT_ONLY`.
- OrbitTrace protected target solar longitude 20°–55° remains inaccessible.
- OrbitTrace target information and target-region events remain inaccessible.
- MAARSY and DMS remain scientifically inaccessible.
- Candidate memberships are immutable.
- No protected/heldout catalogue is authorized by this protocol.
