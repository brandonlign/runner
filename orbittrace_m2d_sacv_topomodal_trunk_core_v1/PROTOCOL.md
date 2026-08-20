# OrbitTrace M2D SACV TopoModal trunk core v1 — frozen protocol

## Status

**FROZEN BEFORE TARGET-EXCLUDED GMN OUTCOME. POST-TARGET-REVEAL DEVELOPMENT ONLY.**

This is a narrow successor to the failed dual-output recurrent core v1 (#1418). The immutable discovery output remains exact SACV v1. The only new object is an optional nested recurrent core for SACV fallback cases, obtained by applying the pre-reveal recurrent-local-TopoModal-trunk principle to the already-validated SACV hypothesis-recurrence graph.

No OrbitTrace target information may enter construction, scoring, selection, or GMN evaluation. A later target characterization could only occur after a binding GMN PASS and unchanged SonotaCo transfer PASS and would remain post-reveal characterization, not pristine independent rediscovery.

## 1. Immutable ancestry and closed lanes

The following are immutable no-go results and may not be rescue-swept:

- recurrence-component union (#1408/#1411): percolates;
- one recurrent pair (#1409): over-prunes;
- edge-consensus membership (#1412): fails SACV-v1 non-regression;
- reciprocal-nearest recurrence (#1414): fragments too aggressively;
- fallback-only recurrent-component replacement (#1417): Sugar F1 regression;
- dual-output natural recurrent-component core (#1418): powered Sugar core precision improves but F1 fails;
- historical bipartite bicore recurrence (#1301): one giant recurrent component;
- density-sync FLASC refinement: catastrophic early-catalogue recovery loss.

The positive ancestry used here is the **pre-reveal recurrent local TopoModal trunk v1** lineage (#1313–#1342). Its exact event-level rule was frozen before target reveal and its binding target-excluded GMN run passed 15/16 gates, missing only 2023 top-100 precision by about 2e-5. This successor ports its hierarchy principle, not its event-space radius graph: SACV already supplies the graph.

## 2. Immutable SACV primary

For every target-excluded GMN candidate occurrence, the primary output IDs, refinement state, parent rank and family identity must be exactly equal to frozen passed SACV v1 (#1405), using its sealed pretruth SHA-256:

`77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b`.

All 328 candidate occurrences must match byte-for-byte at ordered ID-list level before hidden shower truth may open. The nested core is never a second ranked discovery candidate and never changes primary matching or literature capacity.

## 3. Unchanged SACV hypothesis and recurrence construction

Reuse the exact #1417 fallback-recurrence runtime:

1. same M2D parent;
2. same SACV physical embedding;
3. same Moorhead-style 25 seasonal analog positions;
4. same 10% modeled-contamination ceiling;
5. same minimum support 4;
6. same admissible radii and annual local hypotheses;
7. same reciprocal cross-year recurrence validation;
8. same recurrence component construction;
9. same frozen component selector:
   `edge_count desc, node_count desc, min_cross_support desc, member_n asc, membership_hash asc`.

A source-only instrumentation patch may expose the already-existing selected component node IDs, hypothesis memberships and validated edges. It may not change any existing route, output ID, recurrence edge, component, score, radius, support or tie break. Source audit must prove this before scientific activation.

## 4. Sole new rule — TopoModal trunk of the frozen selected recurrence component

This rule is considered **only** when the exact frozen runtime route is `recurrence_fallback`: exact SACV top-1 validation failed, but the unchanged all-hypothesis recurrence graph contains a selected recurrent component.

Let the selected component contain hypothesis nodes `V` and unchanged validated recurrence edges `E`.

### 4.1 Manual graph and density

- Sort hypothesis node IDs lexicographically.
- Build the exact undirected manual graph from `E` only.
- Include each node itself in its manual neighborhood, matching the pre-reveal local-TopoModal-trunk convention.
- No new k-NN, radius or edge threshold is introduced.
- Define `rho_i = |N_i| / |V|`, equivalently `(validated degree_i + 1)/|V|`.
- Run GUDHI `3.12.0` ToMATo with `graph_type='manual'`, `density_type='manual'`, exact neighborhood lists and `rho_i` weights.
- Request no flat cluster count and no persistence threshold.

### 4.2 Anchor-chain trunk

- The anchor hypothesis is the node with maximum `rho_i`; lexicographically smallest exact node ID breaks ties.
- Find the ToMATo leaf containing the anchor.
- Follow its unique parent chain through the full hierarchy to the connected-component root.
- Reconstruct the hypothesis-node membership of every unique anchor-chain state.

For each state, define its event membership as the union of the **already-frozen SACV local-hypothesis event memberships** belonging to that state. No event is added from outside those hypothesis memberships.

A state is reportable only if all of the following hold:

1. its hypothesis-node set is a strict subset of the selected recurrent component;
2. its event union is a strict subset of the selected component's full event union (otherwise it is scientifically identical to failed #1418 natural component membership);
3. its event union contains at least 4 target-excluded parent events from 2022 and at least 4 from 2023, preserving the inherited support-4 recurrence floor at the event-output level.

If one or more reportable states exist, choose the one with the **largest hypothesis-node count**. The anchor chain is nested, so this is the unique least-aggressive topological erosion. Exact duplicate hypothesis memberships are deduplicated.

If no reportable strict state exists, emit **no nested core** for that occurrence. Do not fall back to the failed full component union.

## 5. Output semantics

- Exact SACV primary is unchanged on every occurrence.
- On `sacv_v1_success`: no nested core is emitted.
- On `parent_fallback` with no recurrence component: no nested core is emitted.
- On `recurrence_fallback`: emit the TopoModal trunk event union only when the strict reportability rule above succeeds; otherwise no nested core.
- Every core must be a subset of the exact parent and must be strictly smaller than the failed natural selected-component event union.
- No reranking, extra catalogue slot, family merge, parent switch or rematching opportunity is created.

## 6. Target-excluded GMN binding evaluation

Reuse the exact #1418 primary and nested-core evaluation semantics and gates without alteration.

### Primary integrity

Primary paired benchmark metrics must exactly reproduce frozen SACV v1:

- Sugar2017 precision `0.8508954378869`, F1 `0.8169897091265172`;
- HDBSCAN2025 precision `0.9369285146156977`, F1 `0.8863023728371738`.

### Nested core utility

For each comparator route independently, evaluate only the same M2D parent assignment rows that actually possess a nonempty TopoModal trunk core. The SACV-v1 primary on that same assignment is the reference. A route is powered only at paired `n >= 20`.

For each powered route all inherited #1418 core gates must pass:

- nonempty fraction >= 0.75;
- mean core precision >= 0.80;
- mean core precision strictly greater than exact SACV primary on those same assignments;
- mean core F1 >= 0.75 x exact SACV-primary F1 on those same assignments;
- nonempty precision non-regression fraction >= 0.50;
- at least one strict core refinement.

Binding verdict:

- PASS only if primary integrity is exact, at least one comparator route is powered, and every powered core route passes all inherited gates;
- POWER_INCONCLUSIVE if primary integrity is exact but no route reaches paired n >= 20;
- FAIL otherwise.

The first technically valid truth execution is binding. Technical repairs may restore only frozen transport/provenance/source execution and may not alter this rule or gates.

## 7. Transfer and target firewall

Only exact `PASS_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_DEVELOPMENT` authorizes one unchanged SonotaCo transfer. SonotaCo receives the exact same graph/topology/core rule with no survey-specific tuning.

Only GMN PASS followed by SonotaCo PASS could authorize a later frozen OrbitTrace characterization. Any such application is explicitly post-target-reveal and cannot retroactively convert #1406 into a pristine independent rediscovery.

## 8. Permanent closure

A valid FAIL permanently closes this exact rule. Do not rescue it by changing:

- component selector;
- recurrence edge validation;
- ToMATo persistence or flat cluster count;
- density definition;
- anchor definition;
- support floor;
- graph self-neighborhood convention;
- choosing a deeper/smaller anchor-chain state;
- retained-fraction, node-count, degree, edge-count or event-count thresholds;
- using multiple trunks/siblings;
- adding the natural component union beside the trunk;
- changing primary SACV output/rank/matching;
- tuning from OrbitTrace target IDs or coordinates.
