# OrbitTrace v31 three-way full-universe refinement diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1091 established the exact candidate direction `(positive_quality_suppression AND component_closure_opportunity)` on recoverable HDB group representatives;
- #1098 showed its exact full-universe extension is recoverability-enriched but broad at `60/229` HDB families;
- v42 showed that acting on all 60 by full quality-rank transfer chooses harmful tiny-budget entrants;
- v43 showed that conservative shared-support placement makes no top-9/top-11 membership correction;
- #1114 showed the third already-frozen sign `crossroute_rank_gap>0` is present for every #1091 joint-positive missed recoverable representative in both years, while surfaced joint-positive recoverable representatives remain absent.

The remaining question is whether the third sign **actually refines the broad 60-family candidate population**, rather than merely corroborating the same truth-conditioned representatives.

This diagnostic evaluates no candidate total order, replacement, promotion position, literature panel, threshold, top-k, rank window, or successor.

## Immutable sources

### Primary full-universe source

Use the authoritative first technically valid #1098 run:

- run `31457788803`;
- artifact `9088683367`;
- ZIP digest `sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11`;
- `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json` SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
- captured exact-v31 engine result SHA-256 `6cb413b133a0bff6886b7108e9a383d4a341ff254cc70b175dbdf595609e4732`;
- radius-1 graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

Require:

- exactly 229 HDB families and 267 Sugar families;
- exactly 60 #1098 `joint_signal=true` HDB families;
- exact #1098 joint definition `(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)`;
- unchanged graph family universes and adjacency;
- exact captured v31 HDB and Sugar total orders from the #1098 capture engine.

No source statistic is recomputed or modified except the direct cross-route sign defined below.

### Direct-crossroute validation source

After the full 229-family three-way vector has been frozen, use authoritative #1093 only to validate that the candidate-level direct-crossroute construction reproduces its already-frozen annual representative rows:

- run `31457199102`;
- artifact `9088482597`;
- ZIP digest `sha256:c709ca3f5aaef103a1cf7668fce7241cb52a4c43b36c0263d5b6b34b8208e6c4`;
- result SHA-256 `62ed82eeb4f10b4371ec2072af7de527482ab070866693a2230be564ebf6af35`.

#1093 may validate the vector but may not define or alter any candidate sign after freeze.

### Recoverability audit sources

Only after the three-way vector is frozen, restore:

- immutable #950 pretruth payload artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
- immutable exposed SonotaCo truth artifact `9069505548`, ZIP SHA-256 `cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`;
- frozen v40 source commit `31704c312c09be2765ad3f65a0685d1acfd2b055` only for exact unchanged v22/v24 truth/recoverability functions.

SonotaCo remains exposed development only.

## Phase A: frozen 229-family three-way vector

From #1098's captured exact-v31 engine result, recover exact route orders as follows:

- `sugar_order` is the ordered `representative_family_id` list in `primary_component_rows['sugar']`;
- `hdb_order` is the ordered `representative_family_id` list in `primary_component_rows['hdbscan']`.

Require these contain 267 and 229 unique families respectively and their order SHA identities agree with the #1098 engine's exact-v31 order diagnostics.

For every HDB family `i`, preserve #1098's:

- exact `v31_rank` and `v31_percentile`;
- `positive_quality_suppression`;
- `component_closure_opportunity`;
- `joint_signal`.

Using only the frozen #1098 radius-1 graph, let the Sugar neighbors of HDB family `i` be its exact `hdbscan_to_sugar_adjacency` entries. Define:

- if there is at least one Sugar neighbor, `best_sugar_rank(i)` = the smallest exact-v31 Sugar rank among those neighbors;
- `best_sugar_percentile(i) = (best_sugar_rank(i)-1)/266`;
- `crossroute_rank_gap(i) = v31_percentile(i) - best_sugar_percentile(i)`;
- `crossroute_positive(i) := crossroute_rank_gap(i) > 0`;
- if there is no Sugar neighbor, `best_sugar_rank`, `best_sugar_percentile`, and `crossroute_rank_gap` are null and `crossroute_positive=false`.

Finally define exactly:

`threeway_signal(i) := joint_signal(i) AND crossroute_positive(i)`.

This vector over all 229 HDB families must be serialized and SHA-frozen before #1093 representative rows or raw exposed truth are loaded.

No distance weighting, best-k, average neighbor rank, component aggregation, magnitude threshold, alternate normalization, OR/XOR logic, or alternative direct-crossroute statistic is allowed.

## Phase B: exact validation against #1093

After the full vector is frozen, load #1093. For each of its annual recoverable-group representatives, require exact agreement with the frozen full-universe row on:

- family identity;
- exact v31 rank;
- `crossroute_positive`;
- `crossroute_rank_gap` to numerical tolerance `1e-15` when non-null.

Any mismatch is an engineering/provenance failure and yields no scientific diagnostic result.

## Phase C: incremental full-universe selector audit

Use exact v22/v24 strict recurrent best-label and annual F1 definitions unchanged.

For every fixed HDB family:

- `family_recoverable_y := annual_F1_y > 0.5`;
- diagnostic strict group = `SHOWER/<best_label>` for recurrent positive families, otherwise unique `NEG/<family_id>`.

At family level, restrict the comparison population to the exact 60 #1098 joint-positive families and split it into:

- `threeway`: `threeway_signal=true`;
- `joint_only`: `joint_signal=true AND threeway_signal=false`.

At diagnostic-group level, define:

- `group_joint := any(joint_signal)` among fixed families in the group;
- `group_threeway := any(threeway_signal)` among fixed families in the group;
- `group_recoverable_y := any(family_recoverable_y)` among fixed families in the group.

Restrict to `group_joint=true` and split into:

- `threeway_group`: `group_threeway=true`;
- `joint_only_group`: `group_joint=true AND group_threeway=false`.

For each year and each level report:

- stratum counts;
- recoverable counts and fractions;
- finite risk ratio `P(recoverable|threeway) / P(recoverable|joint_only)` when the joint-only recoverable fraction is positive;
- `risk_ratio_infinite=true` when the joint-only recoverable fraction is zero and the three-way recoverable fraction is positive; in that case the numeric risk-ratio field is null for JSON serialization;
- `risk_ratio_infinite=false` otherwise.

Also report the frozen three-way family count/fraction and reduction relative to the 60-family #1098 joint set. These breadth values are descriptive; no maximum selector size is selected.

## Predeclared interpretation gate

The third sign is considered a useful categorical selector refinement only if **all** of the following hold:

1. the frozen three-way family set is a strict nonempty subset of the #1098 joint set: `0 < threeway_family_count < 60`;
2. in both 2013 and 2014, family-level recoverable fraction among three-way families is strictly greater than among joint-only families, and the risk-ratio condition is satisfied either by a finite ratio strictly greater than 1 or by `risk_ratio_infinite=true`;
3. in both 2013 and 2014, diagnostic-group recoverable fraction among three-way groups is strictly greater than among joint-only groups, and the risk-ratio condition is satisfied either by a finite ratio strictly greater than 1 or by `risk_ratio_infinite=true`.

If both strata have zero recoverable fraction, or the three-way recoverable fraction is not strictly greater, the corresponding gate fails.

No minimum effect size, significance threshold, precision target, maximum family count, oracle cardinality, or literature-budget condition is selected.

A PASS means only that direct cross-route positivity adds incremental full-universe selector information beyond #1091/#1098. Any deployable successor must be separately frozen and may not infer how many families to promote or where to place them from this result.

A FAIL closes categorical use of the third sign as a refinement of the #1098 gate. Do not rescue it with a rank-gap magnitude threshold, top-k, rank window, OR rule, component-size rule, route/year/budget exception, or post-result alternate direct-crossroute statistic.

## Explicit non-search commitments

No new total rank or literature panel; no replacement rule; no promotion position; no threshold/top-k/rank-window; no signal magnitude use; no neighbor aggregation search; no graph/radius/metric change; no Boolean-combination search; no feature/model/fusion/diversity/source-quota search; no candidate/membership change; no oracle identity rule; no post-result second statistic.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053/#1071 cannot define the full-universe vector or gate.
