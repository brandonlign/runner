# OrbitTrace topomodal lineage-balanced ranking v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

The fixed-scale #1284 hierarchy repeatedly gives superior sparse known-stream coverage/purity, but all-node scalar ranking gives poor MRR. Finite-only and disjoint-cut selectors then lose recovery by deleting useful alternative hierarchy levels. This successor therefore keeps the **complete unchanged #1284 candidate universe** and changes only rank allocation across nested modal lineages.

## Firewall

Use only target-excluded GMN 2022+2023. Remove inclusive solar longitude `[20,55]` before all processing. No OrbitTrace target data/information; no SonotaCo scientific access; no ASFN/EFN event-level access; no AMOS, MAARSY, or DMS scientific access. No post-result changes to geometry, hierarchy, lineage rule, ranking, panels, truth metrics, candidate budget, or gates.

## Exact panels and hierarchy

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`, denominators `128` and `1024`, buckets `0..3`, and the exact #1284 physical embedding, radius-1 symmetric self-inclusive graph, `rho=degree/n`, GUDHI 3.12 manual ToMATo hierarchy, exact membership dedupe, and support >=4 reporting floor.

Before truth, complete successor memberships and recurrent-EOM comparator memberships must reproduce authoritative #1284 run `31955621864` / result SHA `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497` exactly.

## Active mode lineage

Reconstruct the hierarchy and finite persistence pairing exactly as already audited:

- leaf active mode = maximum-rho event, exact ties by lexicographically smallest event ID;
- at each merge, larger active peak survives; exact ties by smaller active-mode key;
- the new parent inherits the surviving active mode;
- the dying mode plus the sorted ToMATo prominence sequence must reconstruct `diagram_` within absolute tolerance `1e-12` before truth.

Every eligible hierarchy candidate is assigned to the active-mode key carried by its first hierarchy node. No candidate is deleted.

## Node lifetime

For each hierarchy node define its density-level lifetime:

- leaf formation level = its active-mode peak density;
- internal-node formation level = the density merge level at which its two children join;
- outside merge level = the density merge level at which the node joins its parent;
- connected-component root outside level = `0`.

`level_lifetime = formation_level - outside_merge_level`.

Require every lifetime finite and >=0 up to `1e-12`. This is the exact density-threshold interval during which that node membership is the current cluster-tree component; it is not fitted and has no weight.

## Lineage-balanced rank schedule

Within each active-mode lineage, sort its eligible candidates by:

1. decreasing `level_lifetime`;
2. `family_hash` ascending.

Assign within-lineage ordinal `lineage_round = 1,2,...`.

Global successor ranking is lexicographic:

1. increasing `lineage_round`;
2. decreasing `level_lifetime`;
3. `family_hash` ascending.

Thus every represented modal lineage receives its best-lived hierarchy level before any lineage receives a second nested variant, then every lineage's second variant precedes any third variant, etc. There is no diversity coefficient, quota, threshold, learned feature, or score blend.

## Comparator, budget, immutable boundary

Recurrent-EOM HDBSCAN v1 is unchanged. For each subset let `K` equal its recurrent-EOM candidate count; evaluate recurrent-EOM's full ranked list and exactly the first `K` successor candidates. #1284 has already established successor candidate count >= comparator count in these panels; if that invariant fails, abort before truth.

Persist every successor membership, lineage key, formation/outside levels, lifetime, lineage round, final rank, every comparator membership/rank, hashes, and firewall flags to `TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL.json`. Hash and verify this file in a separate workflow step before truth. Candidate generation/ranking may not rerun after truth.

## Truth and gates

Use the selected parent's unchanged `metrics(...)` semantics separately by year. Keep the same ten frozen sparse gates used by the preceding all-node tests:

Fine `d=1024`: successor qualified total strictly greater; qualified nonloss >=6/8; MRR mean >= parent; precision mean >= parent; fragmentation mean <= parent.

Coarse `d=128`: successor qualified total >= parent; qualified nonloss >=6/8; MRR mean >= parent; precision mean >= parent; fragmentation mean <= parent.

PASS only if all ten hold; otherwise FAIL.

## Closure

A PASS means the complete sample-size-stable #1284 hierarchy plus a parameter-free lineage-balanced rank schedule beats recurrent-EOM in sparse recovery/ranking and justifies full-GMN scaling. A FAIL permanently closes this exact lineage assignment, lifetime definition, and round-robin schedule. Do not change lineage grouping, lifetime, round ordering, tie-breaks, budget, or gates after truth.