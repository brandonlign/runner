# Recurrent-EOM support-attribution diagnostic v1 — binding result

## 🟢 POSITIVE DIAGNOSTIC — joint support bottleneck isolated

The first complete frozen zero-label diagnostic succeeded end-to-end in GitHub Actions run `31929557565` at execution head `ab5fb6e545ba606c3bcf33035c901d7a2862c647`.

- artifact: `9258902255`
- artifact digest: `sha256:018c44f5cddc2ed55694fd487384500c378236f8d505af12db511d7e83f39664`
- result SHA-256: `5efbd4c4eb61f66024de5770116576c7d3680e1547f9edcfa94703a83006ef49`
- exact predeclared attribution: `JOINT_SUPPORT_BOTTLENECK`

This is a structural diagnostic result only. It does not promote any HDBSCAN setting.

## Frozen activation summary

Across the exact eight small-scale GMN subsets that were already parent-inactive in PR #1272:

- lower only the condensation floor: `min_cluster_size=2, min_samples=10`
  - active `3/8`
  - activation rate `0.375`
- lower only core smoothing: `min_cluster_size=10, min_samples=2`
  - active `4/8`
  - activation rate `0.500`
- lower both simultaneously: `min_cluster_size=2, min_samples=2`
  - active `8/8`
  - activation rate `1.000`

The parent `10/10` configuration reproduced the immutable #1272 selected-node/membership outputs exactly and remained inactive in all `8/8` subsets.

## Scale-specific behavior

### denominator 128 — roughly 5.6k–5.9k events

Parent `10/10` was inactive in all four buckets.

`2/10`:

- bucket 0: active (`83 -> 80` ordinary/recurrent selected nodes; node symdiff `5`)
- bucket 1: active (`84 -> 83`; symdiff `3`)
- bucket 2: inactive (`82 = 82`; symdiff `0`)
- bucket 3: active (`87 -> 85`; symdiff `6`)

Activation: `3/4`.

`10/2`:

- bucket 0: active (`88 -> 83`; symdiff `9`)
- bucket 1: active (`90 -> 86`; symdiff `6`)
- bucket 2: active (`93 -> 90`; symdiff `7`)
- bucket 3: active (`91 -> 88`; symdiff `5`)

Activation: `4/4`.

`2/2` was active in all four buckets and generated much richer trees (`1,465–1,595` cluster nodes; `565–640` ordinary selected nodes).

Thus at the ~5.8k-event scale, fixed 10-neighbor core smoothing is the more consistent single-operation choke point, while the fixed 10-point condensation floor also contributes materially.

### denominator 1024 — roughly 677–766 events

Parent `10/10` was inactive in all four buckets.

Crucially, **neither single ablation was sufficient in any bucket**:

- `2/10`: inactive `0/4` activation;
- `10/2`: inactive `0/4` activation.

Only the joint `2/2` ablation restored recurrent extraction differences:

- bucket 0: ordinary/recurrent `78/67`, symdiff `19`
- bucket 1: `87/86`, symdiff `3`
- bucket 2: `96/92`, symdiff `12`
- bucket 3: `90/83`, symdiff `17`

Activation: `4/4`.

## Scientific interpretation

PR #1272 established that fixed HDBSCAN `10/10` is sufficient to make extraction-only recurrent-EOM structurally inert as accessible sample size falls. This diagnostic now shows that the smallest-sample failure is **joint**, not attributable to one knob alone.

At modestly small samples, reducing core-distance smoothing alone exposes enough alternative hierarchy structure for recurrent-EOM in all four deterministic replicates, while removing the condensation floor alone works in three of four. At the ~700-event scale, however, neither operation alone creates a hierarchy on which recurrence can alter the EOM cut. Both finite-support operations jointly suppress the relevant alternative structure.

Therefore the unresolved architecture problem is deeper than choosing a better `min_samples` or `min_cluster_size`. A future method must jointly handle:

1. finite-sample density resolution / neighborhood smoothing, and
2. finite-sample branch retention / pruning.

PR #1271 shows why simply lowering both support controls is not an acceptable scientific solution: a low-support hierarchy reconstructs/floods the catalogue and its uncalibrated local-BIC ranking failed early-budget precision/MRR. The positive lesson is that low-support geometry contains additional structure; the missing ingredient is **statistical calibration of which low-support splits are supported rather than chance structure**.

This result therefore motivates a distinct class of statistically calibrated multi-scale or split-significance cluster-tree estimators. It does not authorize any intermediate support value, `2/2` operational setting, or #1271 rescue.

## Closure

Per the frozen protocol:

- no intermediate support value may be tested as a continuation of this diagnostic;
- no HDBSCAN support setting may be selected from this result;
- no truth/performance evaluation of the ablation configurations is authorized;
- any future scientific successor must be independently motivated and frozen before its first technically valid outcome.

## Firewall

The binding workflow enforced:

- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `shower_truth_used=false`;
- `sonotaco_2013_2014_access=false`;
- `asfn_event_level_access=false`;
- `efn_event_level_access=false`;
- `amos_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `method_parameter_selection_from_result=false`;
- `intermediate_support_values_tested=false`.
