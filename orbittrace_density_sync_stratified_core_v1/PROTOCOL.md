# OrbitTrace density-synchronous stratified-core HDBSCAN v1 — frozen protocol

## Scientific role

This is a single direct successor to the promoted density-synchronous recurrent-EOM HDBSCAN v1 method at commit `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d` (PR #1263). It changes **only the HDBSCAN core-distance construction**. The promoted density-synchronous FOSC/EOM extraction criterion, representation, target firewall, evaluation, and superiority gate remain unchanged.

The scientific motivation is fixed before any technically valid GMN outcome: ordinary pooled `min_samples=10` core distance can be supported primarily by one observing year. For a recurrent meteor-stream detector, local density support should itself be present in both years before hierarchy construction. The successor therefore replaces the pooled tenth-other core scale with a balanced annual support scale.

## Permanent data split and firewall

The permanent OrbitTrace governance remains binding:

- **TRAIN / DEVELOPMENT:** GMN 2022+2023 only, with solar longitude `[20°,55°]` removed before scientific use.
- **VALIDATION:** SonotaCo 2013+2014 only if this exact successor passes the frozen GMN development gate; SonotaCo is EXPOSED DEVELOPMENT ONLY and never external validation.
- **FINAL TEST:** untouched AMOS 2023+2024 only after methodology selection is closed and one final method is selected.

This protocol does not authorize SonotaCo, EFN, ASFN, AMOS, MAARSY, DMS, OrbitTrace target information/events, or protected-target-region event access during the GMN development run.

## Frozen parent

Direct comparator: density-synchronous recurrent-EOM HDBSCAN v1 (#1263), exact binding head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

The parent uses:

- GEO6 representation unchanged.
- pooled target-excluded GMN 2022+2023 hierarchy.
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean metric, `cluster_selection_method='eom'`, `cluster_selection_epsilon=0`, `allow_single_cluster=False`.
- density-synchronous node quality
  `S_sync(C)=integral min(A_2022^C(lambda), A_2023^C(lambda)) d lambda`.
- FOSC/EOM selection using that node quality.
- ranking by descending synchronous stability, then ordinary stability, member count, deterministic family ID.

Binding parent metrics are frozen as:

### 2022
- recovered @25: 22
- recovered @50: 45
- recovered @100: 89
- qualified matches: 236
- top-100 dominant precision: `0.7873334042799703`
- MRR: `0.022505373166085363`
- fragmentation median top500: `1.0`

### 2023
- recovered @25: 23
- recovered @50: 46
- recovered @100: 90
- qualified matches: 244
- top-100 dominant precision: `0.7898245986099988`
- MRR: `0.02203028490649908`
- fragmentation median top500: `1.0`

Parent candidate count: 2094.

## Sole successor change: balanced annual core support

For every accessible event `i`, use the unchanged GEO6 coordinates and year identity.

Let:

- `d_2022(i)` be the Euclidean distance from `i` to its fifth nearest **other** accessible GMN 2022 event.
- `d_2023(i)` be the Euclidean distance from `i` to its fifth nearest **other** accessible GMN 2023 event.

Exact event identity, not coordinate equality, defines self-exclusion. A different event at identical coordinates is a valid zero-distance neighbor.

Freeze:

`k_year = 5`

and define the successor core distance:

`core_strat(i) = max(d_2022(i), d_2023(i))`.

This is the only scientific change relative to #1263. It requires local support from at least five events in each observing year at the event's core scale. There is no fitted annual weight, threshold, blend, adaptive k, alternate aggregation, or result-informed rescue.

The audited injected-core HDBSCAN implementation is inherited **bit-for-bit** from `orbittrace_stratified_core_hdbscan_v1/stratified_core.py`, blob `ce22a6c762829b03184e136cd43cc0b821763e0c`. Its synthetic injection audit passed in GitHub Actions run `31861223877` at commit `12b2bcd299e74c85270c037cd8b5fbf5262ff4f8` before this successor accesses GMN scientifically.

## Unchanged hierarchy/extraction semantics

After substituting `core_strat` for the ordinary pooled HDBSCAN core distances:

- Euclidean mutual reachability semantics remain unchanged except for the supplied core distances.
- HDBSCAN Boruvka/KDTree settings remain those audited for the injection path: `min_samples=10` semantics, `alpha=1`, `approx_min_span_tree=True`, `leaf_size=40`, Boruvka leaf size `40//3`, `n_jobs=1`.
- `min_cluster_size=10` remains unchanged.
- The condensed hierarchy is passed to the **exact unchanged #1263 density-synchronous kernel**, blob `587a304f451e41b9503272f1783a6c6ebb295000`.
- The density-synchronous node objective is not modified.
- FOSC/EOM extraction is not modified.
- Candidate ranking semantics are not modified.

No ordinary/recurrent/synchronous score blending is permitted.

## Required pretruth freeze

Before any hidden shower labels are used, the run must persist enough information to reproduce the scientific proposal, including at minimum:

- accessible event counts by year;
- hash of the successor condensed tree;
- selected node IDs;
- candidate memberships and their deterministic order;
- successor candidate count;
- synchronous stability map;
- stratified-core summary/provenance sufficient to verify the frozen construction;
- firewall flags confirming no protected or external access.

The parent #1263 proposal must also be reconstructed independently on the ordinary hierarchy and checked against the frozen parent metrics before successor truth evaluation is accepted.

## Frozen development evaluator

Use the exact same hidden GMN shower labels and metric implementation already frozen for the #1263 development gate. No label enters hierarchy construction, density-synchronous scoring, FOSC selection, or ranking.

Per year report at minimum:

- qualified matches;
- recovered @25;
- recovered @50;
- recovered @100;
- recovered @500 (reporting only);
- top-100 dominant precision;
- MRR;
- fragmentation median top500.

## Binding superiority gate

The successor passes GMN development **only if all conditions hold**:

1. The stratified-core mechanism is active (successor hierarchy/proposal is not identical to #1263).
2. For **each** of 2022 and 2023:
   - recovered @50 is not lower than #1263;
   - recovered @100 is not lower than #1263;
   - top-100 dominant precision is not lower than #1263;
   - MRR is not lower than #1263;
   - fragmentation median top500 is not higher than #1263.
3. There is a **strict recovered-@100 improvement in at least one year**.

Recovered @25, @500, qualified-match count, candidate count, and other diagnostics are reporting-only and cannot rescue a failed binding gate.

If any binding condition fails, verdict is permanent:

`FAIL_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT`

and this exact version is closed. No SonotaCo execution, parameter rescue, alternate k, alternate annual-core aggregation, scoring blend, or reranking is allowed.

If every binding condition passes, verdict is:

`PASS_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT`

Only then may an exact SonotaCo 2013+2014 validation protocol be frozen before SonotaCo execution. SonotaCo remains exposed development validation, not external validation.

## Engineering audit requirement

Before GMN activation, a zero-truth composition/source audit must prove:

- the stratified-core implementation is exactly the already-passed blob `ce22a6c762829b03184e136cd43cc0b821763e0c`;
- the density-synchronous kernel is exactly blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- the recurrent-EOM kernel and GMN evaluator/runtime dependencies remain the frozen parent versions;
- ordinary-core injection equivalence remains covered by the prior synthetic PASS `31861223877`;
- the new composition runner changes hierarchy construction only and does not expose a tuning surface;
- no scientific catalogue, hidden labels, protected target data, SonotaCo, EFN, ASFN, AMOS, MAARSY, or DMS are accessed by the audit.

Only a complete engineering PASS authorizes the one binding target-excluded GMN development execution.

## No rescue / no reinterpretation

This protocol is frozen before the first technically valid scientific outcome. Technical failures before scientific access may receive narrowly documented engineering repairs only when the scientific source, parameters, evaluator, and gate remain unchanged. Every no-result and failed outcome must be preserved.
