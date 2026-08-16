# OrbitTrace recurrent-EOM support-attribution diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It is not a successor method and cannot select or promote any HDBSCAN parameter.

PR #1272 established that exact recurrent-EOM HDBSCAN `min_cluster_size=10, min_samples=10` becomes mechanism-inactive as the same target-excluded GMN geometry is deterministically reduced to small-survey sample sizes. HDBSCAN has two distinct finite-support mechanisms hidden inside the shorthand `10/10`:

1. `min_samples` controls the core-distance / mutual-reachability smoothing used to build the hierarchy;
2. `min_cluster_size` controls condensation and removes branches smaller than the fixed support count.

This diagnostic isolates which of those two operations is sufficient to account for the observed structural inertia. It uses **no shower truth and no external event rows**.

The diagnostic deliberately uses only the algorithmic lower endpoint `2` as an extreme ablation. `2` is not a proposed scientific setting and may not become one after the outcome. No intermediate support value is tested.

## 1. Parent, data, and firewall

Scientific parent: selected recurrent-EOM HDBSCAN v1, branch head `0248177a2b4dc1f7a0969931d835097d3e86c06f`.

Use only target-excluded GMN 2022+2023 geometry under exact parent GEO6 normalization. The inclusive protected interval `[20.0,55.0]` is removed before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic or decision;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any promotion, ranking, or performance evaluation of the ablation settings;
- any intermediate `min_samples` / `min_cluster_size` value after outcome.

## 2. Exact deterministic subsets

Reuse exactly the frozen hash definition from PR #1272:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Retain event `eid` for denominator `d`, bucket `b` iff:

`H(eid) mod d == b`.

Run only the already-defined small-scale anchor subsets:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

No new salt, denominator, bucket, random seed, scale, or replicate is authorized.

These eight subsets were already structurally parent-inactive in the binding #1272 result. Their exact parent 10/10 outputs must reproduce before any ablation result is accepted.

## 3. Frozen four-setting factorial ablation

For each of the eight subsets, fit exactly four HDBSCAN configurations on the same GEO6 points:

| code | min_cluster_size | min_samples | role |
|---|---:|---:|---|
| `PARENT_10_10` | 10 | 10 | exact control |
| `CONDENSATION_MIN_2_10` | 2 | 10 | remove only fixed 10-point condensation floor |
| `CORE_MIN_10_2` | 10 | 2 | remove only fixed 10-neighbor core smoothing |
| `BOTH_MIN_2_2` | 2 | 2 | extreme joint ablation |

All other parent semantics remain exact:

- GEO6;
- Euclidean distance;
- one pooled fit over the retained 2022+2023 rows;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=false`;
- exact ordinary EOM extraction;
- exact recurrent-EOM annual normalized alive-mass extraction.

No BIC, significance score, recurrence rerank, local exposure term, density-sync term, membership expansion, or new geometry is permitted.

## 4. Zero-label outputs

For each subset/configuration persist only:

- pooled/annual sample counts;
- condensed-tree row count;
- unique cluster-node count;
- ordinary selected-node count;
- recurrent selected-node count;
- ordinary/recurrent selected-node symmetric difference;
- selected-node Jaccard;
- `mechanism_active`;
- selected ordinary/recurrent membership hashes;
- count of exact ordinary/recurrent membership intersections;
- count of hierarchy nodes with positive recurrent quality;
- count of hierarchy nodes with positive contribution in both years.

No recovery, F1, precision, MRR, known-shower assignment, comparator, literature metric, or target statistic may be computed.

## 5. Parent reproduction

The exact eight `PARENT_10_10` outputs are frozen from #1272 and must reproduce at least:

- d=128, b=0..3: all `mechanism_active=false`;
- d=1024, b=0..3: all `mechanism_active=false`.

Exact selected-node counts and hashes must also be read from the immutable #1272 result artifact and reproduced before accepting the ablation summary.

## 6. Predeclared attribution

For each ablation configuration define its `activation_rate` across all eight frozen parent-inactive subsets as the fraction with `mechanism_active=true`.

Let:

- `C` = activation rate for `CONDENSATION_MIN_2_10`;
- `K` = activation rate for `CORE_MIN_10_2`;
- `B` = activation rate for `BOTH_MIN_2_2`.

The sole categorical attribution is frozen as:

1. `CONDENSATION_DOMINANT_INERTIA` if `C >= 0.75` and `K <= 0.25`;
2. `CORE_SMOOTHING_DOMINANT_INERTIA` if `K >= 0.75` and `C <= 0.25`;
3. `EITHER_SINGLE_ABLATION_SUFFICIENT` if `C >= 0.75` and `K >= 0.75`;
4. `JOINT_SUPPORT_BOTTLENECK` if `C < 0.75`, `K < 0.75`, and `B >= 0.75`;
5. otherwise `MIXED_SUPPORT_ATTRIBUTION`.

This attribution concerns only why recurrent extraction can become identical to ordinary extraction. It does **not** say which configuration is scientifically better and cannot authorize a new support setting.

The relative increase in hierarchy nodes / selected branches under each ablation is descriptive evidence only.

## 7. Relationship to PR #1271

PR #1271 is a permanently failed scientific successor that jointly changed support to `8/4` and introduced a local-BIC quality/ranking architecture. Its exact architecture and any support/BIC/ranking rescue remain closed.

This diagnostic does not evaluate 8/4, BIC, truth, recovery, precision, or ranking. The lower endpoint `2` is used only as an extreme structural ablation to attribute #1272's already-established inertia. No result from this diagnostic may be used to claim that `2` is an appropriate operational support.

## 8. Closure

After the first technically valid complete run:

- preserve the exact result and categorical attribution;
- do not test intermediate support values;
- do not select an HDBSCAN setting from the result;
- do not rerun with new subsets or salts;
- any future method must be independently motivated and frozen before its first technically valid outcome.
