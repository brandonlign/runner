# OrbitTrace v40 component route-consensus diagnostic v1

## Scientific role

Post-result exposed-development diagnostic only after the binding v40 failure. No new candidate score, total order, selector, fusion, threshold, or successor is evaluated here.

The current problem is extremely narrow. #1071 proved that one nested HDB top-9 ⊂ top-11 ordering can clear both HDB literature panels with only one replacement relative to v31's top 9 and two replacements relative to v31's top 11. v40 independently made exactly one top-9 and two top-11 HDB component replacements, improving HDB13 to `0.1609800149 / 10`, but it selected the wrong replacements for a joint pass and regressed HDB14.

v40's component score used **best-route evidence**: a component could be promoted by a very strong Sugar v31 rank even when HDB itself ranked that component much worse. Because v39 had already shown that unrestricted best-route transfer is too broad, the specific post-v40 question is:

> Were v40's newly promoted HDB prefix components systematically one-route outliers, rather than components supported comparably well by both Sugar and HDB?

If yes, this supports one separately frozen conservative cross-route-consensus successor. If not, the route-consensus direction is closed. This diagnostic itself is truth-free with respect to candidate quality: it uses only already-frozen v31 ranks, component identities, and v40 primary positions from the authoritative v40 artifact.

## Immutable source

Use only the authoritative v40 result from:

- PR #1079;
- workflow run `31455562054`;
- execution commit `31704c312c09be2765ad3f65a0685d1acfd2b055`;
- artifact `9087888653`;
- artifact digest `sha256:f74cb12bd5b1c958720bd6f1cd5a2d373dc3398e354053ada7a130822505c5d3`.

Required inherited facts:

- v40 verdict is `FAIL_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT`;
- v40 reproduced exact v31 before its sole selector;
- HDB family count is 229 and Sugar family count is 267;
- v40 primary component rows exist for both routes;
- the HDB exact literature budgets remain 9 and 11;
- no target, MAARSY, or DMS access occurred.

No v40 result field involving candidate truth, annual F1, shower label, oracle identity, or literature outcome may enter the diagnostic statistic. The v40 verdict is checked only to establish source identity.

## Frozen component rank quantities

For each frozen connected component represented in both route primary-component tables, use exactly:

- `r_h`: the component's `route_best_rank` in the HDB primary row;
- `r_s`: the same component's `route_best_rank` in the Sugar primary row.

Normalize by the fixed route universes:

`p_h = (r_h - 1) / 228`

`p_s = (r_s - 1) / 266`.

Define exactly:

- `p_best = min(p_h, p_s)`;
- `p_worst = max(p_h, p_s)`;
- `route_rank_disagreement = abs(p_h - p_s)`;
- `sugar_driven = (p_s < p_h)`.

These are descriptive only. No alternate normalization, rank ratio, log transform, coefficient, clipping, distance weight, component-size weight, or threshold is considered.

## Frozen HDB prefix-change sets

For each exact HDB budget `B ∈ {9, 11}`:

1. Reconstruct the v31 HDB prefix-component set as HDB primary rows whose `representative_v31_rank <= B`.
   - #1070 already established that v31's HDB top 9 and top 11 occupy 9 and 11 distinct frozen components, so this must yield exactly B components.
2. Reconstruct the v40 HDB prefix-component set as HDB primary rows whose `v40_primary_position <= B`.
   - This must also yield exactly B components.
3. Define:
   - `preserved = v31_prefix ∩ v40_prefix`;
   - `incoming = v40_prefix - v31_prefix`;
   - `outgoing = v31_prefix - v40_prefix`.

The expected change counts are not hard-coded as a scientific requirement, but the diagnostic reports them and fails closed if either prefix contains duplicate component IDs.

For preserved, incoming, and outgoing components report the frozen rank quantities above, plus median `route_rank_disagreement` for each nonempty set.

## Predeclared direction criterion

The **route-consensus direction is supported at a budget** iff:

1. every incoming component is represented in both routes;
2. every incoming component is `sugar_driven` (`p_s < p_h`); and
3. median incoming `route_rank_disagreement` is strictly greater than median preserved `route_rank_disagreement`.

The overall diagnostic direction is supported only if this holds at **both B=9 and B=11**.

No effect-size threshold is selected. The preserved-set median is the sole predeclared comparison because the scientific question is whether v40's actual replacements are more cross-route-discordant than the components it retained.

## Interpretation boundary

If the direction is supported at both budgets, it justifies exactly one separately frozen successor based on **conservative route consensus** rather than v40's best-route component evidence. The canonical successor to consider is the worst-route normalized component rank (`max(p_h,p_s)`), but this diagnostic does not evaluate that ordering or any literature outcome.

If the direction fails at either budget, component route-consensus is closed as the next mechanism.

No v40 incoming/outgoing family or component identity may be hard-coded into a successor. Any successor must recompute the same truth-free component/rank quantities from frozen inputs.

## Explicit non-search commitments

No:

- new candidate order or prefix evaluation;
- candidate truth or annual F1 use in the statistic;
- oracle identity use from #1050/#1053/#1071;
- route-rank coefficient or weighted average;
- rank-gap threshold;
- HDB-only rescue rule;
- component-size threshold;
- radius/metric/feature change;
- graph pruning/expansion;
- representative change;
- secondary-fragment placement change;
- budget-specific successor;
- post-result alternate diagnostic statistic search.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No protected validation is authorized by a positive diagnostic.
