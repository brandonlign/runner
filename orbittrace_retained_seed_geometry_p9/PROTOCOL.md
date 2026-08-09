# OrbitTrace P9 retained-seed joint-geometry protocol

## Status

Source/protocol-only successor after authoritative P8 scientific no-go. P9 remains fully target-excluded and may not access comparator outcomes, external-panel event values, solar longitude 20°–55°, or OrbitTrace target information.

Authoritative predecessor P8 is permanently frozen as `FAIL_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_NO_GO` from workflow `31296889081`, artifact `9033444168` (`sha256:f9d91b1633022a2ca7d5386d3b8de2e9b81a4237fc115eb4cbf668edc0317979`). P8 passed every substantive development gate except qualified-match non-regression: 92 versus the required v8 baseline 95.

P9 is a minimal continuation of the P3/P4/P5/P6/P8 membership lineage, not a detector restart.

## Pretruth structural diagnosis

The immutable P8 pretruth payload was inspected only after P8 was closed as a no-go, without inspecting per-shower truth endpoints. P8 deliberately discounts the lowest-scoring held-out recurrent seeds when constructing its finite-sample scalar membership floor:

`k = max(1, floor(P3_NEGATIVE_TAIL_MAX * (n + 1)))`,

`membership_floor = k-th smallest held-out recurrent-seed probability`.

However, inherited P5 geometry still constructs its joint `[d_obs,D_SH]` support frontier from **all** held-out recurrent seeds. Thus a seed that P8 has already declared below the robust retained-seed floor can still enlarge the geometric acceptance region.

Artifact-only scoring of the 742 inherited P5 frontier vectors with their exact P8 family-excluded held-fold models finds 71 frontier vectors below their direction's P8 membership floor, spanning 50 reliable directions (comparison tolerance 1e-12 only for the diagnostic arithmetic). This is an internal scalar/geometry inconsistency, not a known-shower truth optimization.

## Sole P9 scientific change

P9 keeps the exact P8 scalar membership floor and P3 reliability decision. For each family-direction, after computing the P8 membership floor from held-out recurrent-seed probabilities, define the **geometry-retained seed set** as exactly

`held-out seed rows with seed_probability >= membership_floor`.

P9 constructs the P5-style componentwise-maximal joint `[d_obs,D_SH]` support frontier **only from that geometry-retained seed set**. A candidate must be componentwise <= at least one retained-seed support vector in both coordinates.

Equivalently, the robust frontier is the Pareto-maximal representation of the exact same held-out seed set that P8 allows to define its scalar membership region.

No other scientific rule changes.

## Deterministic consequences

- If P8 rank `k=1`, every held-out recurrent seed is retained and P9 geometry is exactly the inherited P5/P8 geometry.
- If `k>1`, only seeds whose same-held-fold probability is at least the already-frozen P8 membership floor may geometrically support candidates.
- Ties at the P8 membership floor are retained because the exact rule is `>= membership_floor`; no arbitrary tie-breaking is introduced.
- The P4 coordinate-wise envelope remains computed from all held-out recurrent seeds exactly as before. P9 changes only the stricter P5 joint-support layer.
- P3 reliability remains computed from the original minimum held-out seed probability and original negative-tail rule exactly as before. P9 does not rescue or reject a direction at the reliability stage.

## Exact inherited architecture

P9 keeps unchanged:

- promoted-v8 226 recurrent families, every v8 seed, and exact multiplicity rank;
- years 2022/2023 and blind exclusion 20°–55°;
- P2 two-view features `[d_obs,D_SH]`, OAS observation geometry, exact Southworth–Hawkins implementation, ±5° local nonseed windows, >=128 negatives/direction, equal direction/class weights, weighted StandardScaler, and L2 logistic C=1.0/lbfgs/max_iter=1000/tol=1e-10;
- P3 deterministic five-fold SHA-256 family exclusion and original minimum-seed reliability gate;
- P4 coordinate-wise held-out-seed envelope from all held-out seeds;
- P6 same-held-fold candidate scoring and odds;
- P8 full finite-sample 10% order-statistic scalar membership floor using inherited `P3_NEGATIVE_TAIL_MAX=0.10`;
- unit background, strict winning responsibility >0.5, deterministic tie handling;
- immutable v8 seeds, no recursive growth, no refit from added members, no recentering, and no reranking.

The final all-family P2 model remains provenance-only and cannot determine P9 proposal inclusion or odds.

## Frozen development gates

The substantive gates are unchanged:

- exact v8 baseline reproduced;
- all 226 v8 families/order and every v8 seed preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5x v8;
- large-shower mean precision >=0.85;
- expansion nonvacuous;
- all source, pretruth, model, decision, membership and label-dataflow firewall gates pass.

Additional P9 integrity gates require:

- P8's exact finite-sample rank and membership floor remain unchanged;
- the geometry-retained seed mask is exactly `pp >= membership_floor` for every direction;
- every rank-one direction retains every held-out recurrent seed;
- every direction retains at least `n-k+1` held-out seeds, with any additional retained rows attributable only to ties at the membership floor;
- every geometry-retained held-out seed is componentwise supported by the P9 retained-seed frontier;
- every surviving proposal is componentwise supported by at least one P9 retained-seed frontier vector;
- no P8-unreliable direction can propose;
- at least one held-out seed is geometrically dropped somewhere, proving the P9 change is nonvacuous;
- all P9 frontiers, proposals, conflicts and complete memberships are SHA-frozen before any known-shower label value is indexed.

## Governance

There is exactly one primary P9 configuration: P8-retained held-out seeds (`probability >= P8 membership_floor`) define the joint support frontier. There is no new alpha, rank, support cutoff, quantile, multiplier, offset, tolerance, family-specific exception, or threshold search.

A genuine P9 development failure rejects this exact configuration. Any later successor must again be motivated from pretruth structure and frozen before another truth evaluation.

Matched Sugar/HDBSCAN comparison, MAARSY external validation, and the final target-containing search remain closed unless P9 first passes every development gate. Sparse-stream superiority against both Sugar and HDBSCAN in both SonotaCo 2023 and 2025 remains mandatory before external validation.
