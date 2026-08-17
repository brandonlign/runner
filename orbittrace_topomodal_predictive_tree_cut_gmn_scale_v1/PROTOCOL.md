# OrbitTrace TopoModal Predictive Tree Cut v1 — target-excluded GMN scale/generalization protocol

## Scientific role

This is the separately preregistered target-excluded GMN scale/generalization test authorized by the frozen Predictive Tree Cut v1 protocol after its exposed SonotaCo HDBSCAN-development PASS.

It is **not** a pristine external validation endpoint and is **not** permission to tune Predictive Tree Cut from GMN outcomes. GMN 2022/2023 is permanent development data. SonotaCo 2013/2014 must not be accessed in this endpoint.

The exact selector architecture is inherited unchanged from `agent/orbittrace-topomodal-predictive-tree-cut-v1`:

- annual projection of a pooled fixed-scale TopoModal hierarchy;
- support floor 4 after annual restriction;
- the fixed physical radius-1 graph at 5° solar / 4° radiant / 10% speed scales;
- deterministic XOR edge split using salt `ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1|`;
- degree-preserving Poisson held-out predictive gain;
- the same antichain dynamic program;
- rank by held-out predictive gain, then annual-membership hash.

No score, edge split, support, radius, physical scale, DP rule, tie rule, or ranking change is authorized.

## Frozen source lineage

Predictive Tree Cut v1 source:

- source branch head at preregistration: `8196f3c80be1fff4498696c02c84f38945d79712`
- `orbittrace_topomodal_predictive_tree_cut_v1/run_pretruth.py` Git blob: `9bc98c6430bc9ed897b8ae81d7d9814e70050a61`
- SonotaCo development result is already exposed and is not read by this endpoint.

Fixed-scale TopoModal / GMN sparse infrastructure:

- exact sparse-recovery source commit: `312b1b718ae105813de242355142a74e7d377d65`
- `orbittrace_topomodal_sparse_recovery_v1/run_development.py` Git blob: `752df8212ce601227f6e9170b0fe994ba06b515d`
- exact zero-label structural source result: run `31955621864`, artifact `9265889512`, result SHA-256 `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`
- frozen GMN utility SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- frozen pooled-year-centroid support artifact SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`
- recurrent-EOM implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

## Exact GMN panel set

Use only target-excluded GMN 2022 and 2023 events from the same frozen parser/runtime used by the authoritative TopoModal scale-stress experiments.

Protected solar longitude `[20°,55°]` remains excluded inclusively before candidate construction.

Use exactly eight pooled deterministic subsets:

- denominators `128` and `1024`;
- buckets `0,1,2,3`;
- event selection is the already-frozen `SHA256('ORBITTRACE_SCALE_STRESS_V1|' + event_id) mod denominator == bucket` rule.

For each pooled subset, rebuild the exact fixed-scale TopoModal hierarchy and exact recurrent-EOM comparator. Before Predictive Tree Cut can run, both candidate memberships must reproduce the authoritative zero-label structural artifact byte-for-byte at the structural-row level.

For each subset and each year independently, project the pooled TopoModal hierarchy to the annual event universe exactly as Predictive Tree Cut v1 specifies, then apply the unchanged selector.

This yields 16 annual truth panels after pretruth freezing: `2 scales × 4 buckets × 2 years`.

## Pretruth structural gates

Truth must not be used unless every subset/year satisfies all of the following:

1. all frozen source/input hashes match;
2. protected-region firewall is intact;
3. exact TopoModal and recurrent-EOM pooled memberships reproduce the authoritative structural result;
4. annual projected TopoModal memberships are laminar and uniquely parented after exact deduplication;
5. the fixed physical graph and both deterministic edge splits are nonempty;
6. Predictive Tree Cut output is a disjoint antichain with finite strictly positive scores;
7. Predictive Tree Cut contains at least as many selected annual candidates as the pooled recurrent-EOM reporting budget `K = recurrent candidate count` for that subset;
8. no shower label or target information enters candidate construction or ranking.

Any failure here is a binding **pretruth structural failure** for this exact scale/generalization endpoint. Do not alter the selector or budget to rescue it.

## Exact equal-budget evaluation

After all pretruth outputs are hash-frozen, open only the already-exposed GMN development truth through the same frozen runtime.

For every subset/year panel:

- comparator = first `K` recurrent-EOM candidates, where `K` is the complete recurrent candidate count for that pooled subset;
- successor = first `K` annual Predictive Tree Cut candidates;
- evaluate with the same frozen GMN metrics used by the TopoModal sparse-recovery experiment.

Record qualified matches, recovered@25, recovered@50, recovered@100, recovered@500, MRR, top-100 dominant precision, and median top-500 fragmentation.

## Frozen promotion gate

Aggregate separately over the eight annual panels at each scale.

For denominator `1024` (fine sparse scale), all five must pass:

1. successor qualified-match total is **strictly greater** than recurrent-EOM;
2. successor qualified matches are nonlower in at least `6/8` panels;
3. mean MRR is not lower;
4. mean top-100 dominant precision is not lower;
5. mean median-fragmentation is not higher.

For denominator `128` (coarse sparse scale), the same five gates apply, including **strictly greater** qualified-match total.

All ten gates are mandatory.

Exact PASS verdict:

`PASS_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_GENERALIZATION`

Any technically valid evaluated result failing one or more gates is:

`FAIL_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_GMN_SCALE_GENERALIZATION`

A PASS would establish that the unchanged selector generalizes from exposed SonotaCo development to the independent target-excluded GMN scale-stress construction while fixing the prior TopoModal early-ordering failure at both scales. It would still **not** establish pristine external validation or superiority to the full-GMN density-synchronous recurrent-EOM champion; that would require a separately frozen endpoint if scientifically and computationally justified.

A FAIL permanently closes this exact Predictive Tree Cut v1 scale/generalization lane. No alternate split, salt, fold count, null model, support, score transform, DP tie, ranking blend, budget exception, scale-specific exception, or SonotaCo-informed rescue is authorized.

## Firewall

Forbidden throughout:

- protected solar longitude `[20°,55°]`;
- OrbitTrace target information/events;
- SonotaCo 2013/2014 event rows or truth;
- ASFN/EFN event rows;
- AMOS;
- MAARSY;
- DMS;
- any pristine external endpoint;
- post-result parameter search.
