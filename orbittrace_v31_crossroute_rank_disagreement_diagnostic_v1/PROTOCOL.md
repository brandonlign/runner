# OrbitTrace v31 cross-route rank-disagreement diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only. Exact v31 remains the strongest genuine method at 2/4. #1050 proved the fixed HDB candidate universe can clear both exact HDB literature budgets. #1053 localized the residual error to a small number of shower-group substitutions. v36 and v37 rejected two local-geometry explanations; v38 rejected positive-reference archetype de-duplication. #1062 and #1064 then established that Sugar and HDB candidates frequently represent the same physical structures, with #1064's already-frozen radius-1 cross-route graph showing 2,308 same-shower edges, zero different-shower edges, and only 26 NEG-involved edges out of 2,334 total.

However, absolute Sugar corroboration is not selective: already-surfaced HDB groups have better Sugar ranks than missed groups. The remaining cross-route hypothesis is narrower:

> Are some recoverable HDB groups missed specifically because v31 ranks an already-corresponding physical structure substantially worse in HDB than Sugar ranks its radius-1 counterpart?

This diagnostic measures that **relative cross-route rank disagreement**. It evaluates no new candidate score, order, fusion, selector, replacement, cutoff, or successor.

## Immutable input

Use only the authoritative frozen output of #1064, run `31454067856`, artifact `9087373195`, digest `sha256:361e6113110dcc58761a458fc842f8c3e613f79d0e13a85c593bad297cd49d7a`.

#1064 already froze the radius-1 graph before truth and then reproduced exact v31. This diagnostic must not recompute or alter that graph, radius, metric, features, memberships, candidate universes, truth labels, v31 order, or annual recoverability categories.

Required inherited facts:

- Sugar family count: 267;
- HDB family count: 229;
- #1064 verdict: `PASS_V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC`;
- #1064 role: `POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_EVALUATED`;
- exact v31 reproduction on all four panels;
- no target, MAARSY, or DMS access.

## Sole diagnostic statistic

For each annual-recoverable HDB strict shower group row already frozen by #1064, use exactly the one #1064 predeclared best cross-route link:

- `best_sugar_neighbor_rank`: the smallest exact Sugar v31 fused rank among radius-1 Sugar neighbors of annual-recoverable HDB candidates in that group;
- `linked_hdb_rank`: the exact HDB v31 fused rank of the HDB candidate participating in that selected link.

If the group has no frozen cross-route edge, its rank disagreement is missing and it is reported separately. No fallback match is allowed.

Convert the two one-indexed ranks to route-normalized zero-to-one percentiles:

`p_hdb = (linked_hdb_rank - 1) / (229 - 1)`

`p_sugar = (best_sugar_neighbor_rank - 1) / (267 - 1)`

and define exactly

`crossroute_rank_gap = p_hdb - p_sugar`.

Positive values mean Sugar ranks the already-corresponding structure better than HDB; negative values mean HDB ranks it better. No absolute value, ratio, logarithm, overlap weighting, distance weighting, clipping, threshold, coefficient, route-budget normalization, or alternate disagreement statistic is authorized.

## Frozen summaries

Independently for 2013 and 2014, preserve #1064's surfaced/missed HDB recoverable-group split at the exact literature budgets and report, separately for surfaced and missed groups:

- group count and groups with a frozen cross-route link;
- median, mean, minimum, maximum, 25th percentile, and 75th percentile of `crossroute_rank_gap` among linked groups;
- count and fraction with strictly positive gap;
- median normalized HDB percentile and median normalized Sugar percentile;
- the full per-group rows inherited from #1064 plus the three derived fields `p_hdb`, `p_sugar`, and `crossroute_rank_gap`.

Also report the median gap difference `missed_median_gap - surfaced_median_gap` for each year. This is descriptive only; zero is the sole natural sign boundary and no effect-size threshold is selected.

## Interpretation boundary

A positive diagnostic direction requires missed recoverable groups to show meaningfully larger positive cross-route rank gaps than surfaced groups in both years. Such a result may justify exactly one separately frozen, truth-free rank-transfer successor using the already-frozen radius-1 relation.

If missed groups do not show larger positive rank gaps in both years, cross-route rank disagreement is closed as the next surfacing mechanism.

The diagnostic does not authorize a transfer formula, fusion weight, clipping rule, budget rule, route-specific exception, or successor. Any such method must be separately motivated and frozen after this result.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No truth-aware identity from #1050/#1053 may be hard-coded or converted into a rank rule.
- No graph/radius/metric/feature/membership/candidate change is authorized.
- No new rank, score, selector, fusion, cutoff, threshold, or parameter search is evaluated.
