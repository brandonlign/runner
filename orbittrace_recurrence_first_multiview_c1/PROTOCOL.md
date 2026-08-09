# OrbitTrace C1 — recurrence-first multiview anchor graph

## Status and purpose

C1 is a genuinely new target-excluded successor after the frozen B1 background-odds membership architecture failed its preregistered GMN 2022/2023 development gate. B1 is a permanent no-go and none of its feature/model/cutoff choices may be tuned from that result.

C1 changes the family-generation architecture rather than applying another membership rule to the inherited v8 family universe. The scientific hypothesis is that weak and broad showers are being lost before membership assignment because hard within-year detection and threshold-then-link construction produces too few recurrent families. C1 therefore retains a generous label-free proposal set and makes cross-year recurrence itself the primary false-positive filter.

No SonotaCo matched-result value is used to choose any C1 constant. SonotaCo 2023/2025 remains exposed diagnostic-only. The failed 2014+2016 reservation is not a C1 development input. MAARSY and all target-containing data remain unopened.

## Development data and target firewall

Development uses exactly GMN 2022 and 2023.

The closed solar-longitude interval **20°–55°** is removed before label normalization/storage, orbit decoding, proposal generation, calibration, graph construction, family ranking, or evaluation. The orbit parser must refuse to decode any orbit whose event ID was not first admitted by the already target-excluded geometry scan.

No 2024–2026 GMN catalogue, no matched-literature panel, no external-validation scientific value, and no OrbitTrace coordinate/member/identity/recovery result may be loaded.

Labels are held in a separate lookup used only after the complete C1 family list, membership, and ranking have been frozen and hashed in memory.

## Frozen inherited geometry and proposal budget

C1 does not search detector scales or proposal counts.

- activity windows: 10° wide, stepped by 5°;
- observation-space geometry: the already frozen 4° angular / 10%-speed Brown-family geometry used by the v3 multi-anchor score;
- positive-lobe core membership: `r² < 3`;
- minimum core size: 4 events;
- primary proposal budget: the inherited catalogue-v6 capacity of the top **512 label-free Brown proposals per 10° window** before expensive exact v3 scoring;
- primary score: exact frozen v3 multi-anchor wavelet-energy score, unchanged;
- sparse proposal channel: exact frozen fixed4 score, with every minimum attainable empirical rescue `p_fixed4 = 1/129` retained even if absent from the primary 512 proposals;
- calibration count for recurrence nulls: 128, inherited from the established source-preserving Mondrian calibration architecture;
- no parameter, threshold, feature-weight, proposal-budget, or scale search.

Brown is proposal-only. It cannot enter the final C1 family score. v3 and fixed4 scientific source must be reconstructed from their already-frozen pre-C1 sources and hash-checked before catalogue access.

## Proposal objects

Every exact-scored proposal is converted to an immutable core node containing only target-excluded information:

- year and 5° window center;
- proposal channel (`v3` or minimum-p `fixed4` rescue);
- original core event IDs;
- positive-lobe observation-space centroid in Sun-centered radiant/speed coordinates;
- exact empirical detector p-value for its channel;
- orbit medoid chosen only from the node's original core members using Southworth–Hawkins `D_SH` over q/e/i/peri/node;
- node provenance hashes.

No added member may ever be reused to refit a node, change its centroid/orbit medoid, create a proposal, or improve recurrence evidence.

## Recurrence-first cross-year graph

C1 does **not** require a proposal to pass a hard within-year scientific detection threshold before recurrence testing.

For each node, opposite-year candidate nodes are restricted only to the same or immediately adjacent 5° window centers. For every candidate pair, compute two independent physical closeness statistics:

1. observation-space centroid distance in the frozen Brown/v3 metric;
2. `D_SH` between the two immutable core orbit medoids.

Each statistic is converted to an empirical local-field tail probability using exactly 128 deterministic source-preserving null pairings. Null pairings keep both node representations unchanged but pair the source node against opposite-year nodes drawn from non-adjacent activity windows; the deterministic selection seed is fixed before development execution. Null construction cannot read labels.

For a real cross-year pair define the conservative two-view recurrence probability

`p_recur = max(p_observation, p_orbit)`.

Thus both observation-space and orbital recurrence must be unusual; one view cannot rescue a poor match in the other. A cross-year edge is retained at the already standard nominal level `p_recur <= 0.05`.

To prevent dense fields from producing many interchangeable links, each node may contribute only its best opposite-year edge by `p_recur`, with deterministic tie breaks by observation p, orbit p, channel order, stable node ID. The edge is accepted only when it is reciprocal-best from both endpoints.

No recurrence threshold is tuned on development labels.

## Same-year consolidation and family formation

Same-year nodes are connected only when their immutable core memberships share at least **two exact event IDs**. This overlap rule contains no geometric threshold and allows adjacent-window observations of the same broad shower to consolidate without halo growth.

The full graph contains:

- reciprocal-best cross-year recurrence edges; and
- same-year two-event-overlap edges.

A C1 family is a connected component that contains at least one node from each development year and at least one accepted cross-year recurrence edge.

Primary families contain at least one v3 node in each year. Components supported only by minimum-p fixed4 nodes are preserved as a separate sparse-rescue queue and may not alter primary-family ordering.

## Membership

Family membership is the union of **original immutable core members only** across nodes in that graph component. C1 has no halo, no recursive expansion, no learned posterior membership cutoff, and no post-family threshold search.

If an event belongs to multiple components, assign it exclusively to the component with the smaller family recurrence probability defined below; remaining ties use larger number of cross-year edges, then larger original-core support, then stable family ID.

## Family significance and ranking

For each component, retain at most one recurrence edge per 5° window-center pair: the smallest `p_recur` in that pair.

Combine those retained recurrence p-values with the equal-weight Cauchy combination test. The resulting `p_family` is the sole primary continuous recurrence statistic. This combination is chosen prospectively because it remains useful under dependent evidence from overlapping activity windows and does not reward a family merely for containing more duplicate anchors.

Primary ranking is deterministic:

1. smaller `p_family`;
2. smaller median exact v3 empirical p-value across the component's v3 nodes;
3. larger number of distinct activity-window centers represented in both years;
4. larger union core membership;
5. stable family ID.

The fixed4-only rescue queue is ranked separately by the same recurrence statistic and never inserted into the primary ordering.

## Frozen GMN development gates

C1 is a scientific PASS only if every integrity gate passes and all of the following hold against the exact promoted-v8 target-excluded development baseline on the same GMN 2022/2023 label universe:

- primary recurrent-family count is at least **204** (90% of the 226-family baseline universe), preventing a return to high-quality/low-coverage solutions;
- qualified known-shower matches are at least **95** (non-regression);
- recovery@100 is at least **58** (non-regression);
- top-100 dominant-label precision is at least **0.65**;
- global macro F1 improves by at least **+0.05** over the v8 baseline;
- annual 4–9-member mean F1 regresses by no more than **0.01** in either year;
- annual all-shower mean F1 improves by at least **+0.03** in both years;
- in each year, at least one of the 25–49, 50–99, or 100+ member strata improves mean F1 by at least **+0.05**;
- no label, matched comparator result, external scientific value, target-region event, or OrbitTrace target information enters proposal generation, recurrence calibration, graph construction, membership, or ranking.

These gates are frozen before C1 scientific execution. Failure preserves C1 as a no-go; it does not authorize changing the proposal budget, recurrence p construction, 0.05 edge level, overlap rule, family score, or development gates from the observed result.

## Literature, external, and target boundary

A C1 development PASS does not itself authorize target access.

Before any fresh matched literature benchmark, a new panel must be reserved only after a metadata-only full-history audit establishes that every chosen year is scientifically unspent. The failed SonotaCo 2014+2016 pair may not be revived by opening 2014 alone, and SonotaCo 2016 is spent.

Only a later frozen successor that passes development, passes a defensible fresh matched Sugar/HDBSCAN comparison without retuning, and passes a no-retuning external/generalization route may authorize the final blind target-free search. Until then the 20°–55° firewall remains closed.