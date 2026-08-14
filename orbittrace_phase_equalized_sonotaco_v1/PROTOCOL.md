# Phase-intensity-equalized recurrent-EOM v1 — dormant SonotaCo parent benchmark

## Status

This protocol is frozen **before the first technically valid GMN 2022/2023 outcome of phase-intensity-equalized recurrent-EOM v1 is known**.

It is a dormant contingency only. It may be activated if and only if the exact frozen GMN development endpoint returns:

`PASS_PHASE_EQUALIZED_RECURRENT_EOM_V1_GMN_DEVELOPMENT`.

A GMN FAIL permanently closes this protocol without scientific execution. No SonotaCo scientific value may be accessed by this branch before a GMN PASS.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. Protected OrbitTrace `[20°,55°]`, target information/events, MAARSY, and DMS remain inaccessible.

## Frozen successor

Use the exact pre-outcome phase-equalized method:

- scientific protocol Git blob `ff509b57fd2139406e823497a85468017414dcca`;
- phase transform Git blob `6577d900814b8c79aad355bdb05d426204f20d4a`;
- recurrent-EOM implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean, EOM, epsilon 0, `allow_single_cluster=False`;
- pooled two-year hierarchy;
- after inclusive `[20,55]` exclusion, pooled accessible solar longitude is mapped by the exact empirical mid-distribution transform on the fixed 325-degree accessible arc;
- all non-phase GEO6 coordinates remain unchanged;
- annual normalized EOM contribution and recurrent minimum combiner remain exact parent semantics;
- candidate ranking remains recurrent stability, ordinary stability, member count, deterministic family ID.

No SonotaCo value may alter the transform, origin, tie rule, pooling, HDBSCAN settings, recurrent-EOM extraction, or ranking.

## Frozen SonotaCo inputs and evaluation

If activated after a GMN PASS, reuse exactly the already-established label-free SonotaCo preparation and truth/evaluation artifacts from the recurrent-EOM benchmark, with no new row eligibility or preprocessing.

Label-free preparation artifact:

- artifact `9050107352`, `orbittrace-final-sonotaco-label-free-preparation-v2`;
- digest `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Exact routes/panels:

- Sugar 2013: 18,638 accessible events, comparator budget 34;
- Sugar 2014: 15,400 accessible events, comparator budget 46;
- HDBSCAN 2013: 16,028 accessible events, comparator budget 11;
- HDBSCAN 2014: 13,283 accessible events, comparator budget 9.

For each route, pool 2013+2014 label-free events, construct the exact pooled empirical phase transform **from that route's pooled accessible raw solar longitudes only**, fit the unchanged successor hierarchy, compute recurrent-EOM selection/ranking, and freeze the complete candidate payload before truth/v31/recurrent-parent result access.

After the complete successor pretruth payload is SHA-frozen, use exact truth/evaluation artifact `9069505548` and the same established Hungarian maximum-F1 one-to-one assignment semantics as v22-v31/recurrent-EOM:

1. restrict pooled candidate memberships to the panel-year truth IDs;
2. retain exact frozen pooled candidate rank order;
3. truncate to that panel's fixed comparator budget;
4. include all truth showers with at least four events;
5. compute shower-by-candidate F1 matrix;
6. Hungarian maximum-F1 one-to-one assignment;
7. report macro-F1 and number of assigned showers with F1 > 0.5.

No candidate insertion, deletion, reranking, annualization, split/merge, threshold change, or budget change is allowed after truth access.

## Exact recurrent-EOM parent controls

The promoted recurrent-EOM SonotaCo benchmark is binding run `31829200215`, artifact `9230008341`, artifact digest `sha256:a0eb8aafc88f3e963a3e788294f1a82bcc6612c26b587f5e12861a579486d110`.

Exact parent controls:

| Route | Year | recurrent-EOM macro-F1 | recurrent-EOM recovered F1>0.5 |
|---|---:|---:|---:|
| Sugar | 2013 | 0.3752906816 | 23 |
| Sugar | 2014 | 0.4377312230 | 24 |
| HDBSCAN | 2013 | 0.1914598192 | 11 |
| HDBSCAN | 2014 | 0.1685878550 | 9 |

These values must be verified from the immutable recurrent-EOM result artifact before interpretation; the table is not an authorization to reconstruct or alter the parent.

## Frozen promotion gate against the current parent

The phase-equalized successor may replace recurrent-EOM as the development parent only if **all four** SonotaCo panels satisfy:

1. successor macro-F1 >= exact recurrent-EOM macro-F1; and
2. successor recovered F1>0.5 >= exact recurrent-EOM recovered count.

In addition, across the four panels the successor must show at least one strict improvement:

3. macro-F1 strictly greater than recurrent-EOM on at least one panel **or** recovered F1>0.5 strictly greater on at least one panel.

Pass token:

`PASS_PHASE_EQUALIZED_SONOTACO_RECURRENT_PARENT_SUPERIORITY_V1`

Otherwise:

`FAIL_PHASE_EQUALIZED_SONOTACO_RECURRENT_PARENT_SUPERIORITY_V1`.

Because recurrent-EOM already beat v31/literature on all four panels, satisfying the all-panel no-regression gate preserves those demonstrated exposed-development wins. Literature/v31 comparisons may be reported descriptively but cannot weaken the direct parent gate above.

## No rescue

After the first technically valid SonotaCo endpoint, do not change/search the phase transform, pooled/per-year choice, CDF tie rule, HDBSCAN settings, recurrent-EOM rule, ranking, budgets, row eligibility, truth semantics, or evaluation metric. A valid FAIL closes this successor.

## Firewall

Any future result must state:

- `sonotaco_role='EXPOSED_DEVELOPMENT_ONLY'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
