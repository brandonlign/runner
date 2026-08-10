# URC fixed-rank fragment-membership merge lab v1

## Scientific question

PR #839 established the current strongest defensible GMN 2022/2023 ranking: the exact 4,504-family hard-v8 + P19-soft + P20-soft union, ranked by strict same-shower grouped ExtraTrees quality regression with diversity lambda 0.8 and scale 1.0. Its recovery@100 is 75 versus 59 for hard v8, but the proposal universe is highly fragmented.

PR #843 showed that selecting one consensus representative from each geometric fragment crowd is not a solution: it reduced recovery@100 to 55. This lab therefore preserves the exact #839 candidate universe and complete rank order byte-for-byte and changes only membership.

## Frozen membership family

For every already-ranked candidate, local neighbors are defined without labels by the inherited physical centroid metric in both 2022 and 2023. Pair distance is the maximum of the two annual centroid distances. Fixed radii are 0.25, 0.50, 0.75, and 1.00.

Four additive, non-recursive rules are evaluated:

1. `nearest_cross_source_union`: retain all original members and add the members of the nearest local candidate from each other generator source.
2. `nearest_cross_source_consensus`: use the anchor plus the nearest candidate from each other source, but add only events supported by at least two selected fragments.
3. `local_fragment_support2`: retain original members and add events appearing in at least two local fragments.
4. `local_source_support2`: retain original members and add events supported by at least two distinct generator sources locally.

No member may ever be removed. Added members are never reused to form neighbors, refit a model, regenerate a candidate, alter a centroid, or alter ranking. The hard/P19/P20 proposal identities remain frozen.

## Ranking firewall

The exact PR #839 selected order is rerun from its checksum-pinned source and must reproduce SHA-256:

`ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`

The baseline must reproduce recovery@25/50/100/500 = 22/40/75/159, 256 qualified showers, top-100 dominant precision 0.7645689180574315, and macro membership F1 0.17953659309876194. No membership outcome may trigger ranking reselection.

## Development gates

A membership variant passes only if all of the following hold on target-excluded GMN 2022/2023:

- recovery@100 >= 70;
- recovery@50 >= 38;
- top-100 dominant precision >= 0.65;
- qualified known showers >= 220;
- best-membership macro F1 improves by at least +0.02 over the fixed #839 baseline;
- annual all-shower mean F1 regresses by no more than 0.002 in either year and gains at least +0.005 on average;
- annual 4–9-member mean F1 regresses by no more than 0.005 in either year and improves on average.

A scientific PASS requires at least one rule to pass at two adjacent frozen radii. This avoids promoting an isolated favorable radius. Selection among passing variants prioritizes membership macro-F1 gain, worst-year overall F1 gain, sparse 4–9 gain, recovery@100, precision, then smaller membership inflation.

A failure is preserved as a no-go and does not authorize post-result threshold/radius changes.

## Data boundary

Only GMN 2022/2023 development data with solar longitude 20°–55° removed by the frozen parser may be used. SonotaCo 2013/2014, MAARSY 2020/2021 scientific data, OrbitTrace target information, and target-region events remain inaccessible.
