# Recurrent-EOM HDBSCAN v1 — GMN 2020/2021 archival temporal transfer result

**Classification: NEGATIVE — binding retrospective transfer failure.**

This result is the first technically valid recurrent-EOM HDBSCAN v1 outcome on target-excluded GMN 2020/2021 under the separately frozen retrospective protocol. GMN 2020/2021 is not pristine external validation because prior OrbitTrace work had already used these years. No result from this transfer may alter recurrent-EOM v1.

## Binding provenance

- protocol blob: `9b61a065678c070c141df74fa48277892841fffa`
- source-only transport audit run: `31830042638`
- source-only transport audit artifact: `9230300205`
- source-only transport audit digest: `sha256:7fc9a2bb9dc42f517b2d5049c0fa137861ec73fac58d33dbc4b90f537ab59db5`
- exact generated transfer runner git blob: `0a34d0cc5cf1d374158201d0c559a870cfb488de`
- exact generated transfer runner SHA-256: `92a19b4b7881519bd9b883e1a84d31ee3c5e81c6fd5640824db315ec24e2942a`
- binding execution run: `31830129499`
- binding artifact: `9230386230`
- binding artifact digest: `sha256:3573d2bf56e85f57c0ffbdf01c5bae91921ed7e7272d8f3cc4787b32cb292d0f`
- execution head: `07f7cd0caecb6e31aa446dd7f9a0050ab5e0977d`

The binding workflow completed successfully as an execution and passed the retrospective role/firewall checks. The inherited unrelated `orbittrace_fixed4_wrapper_saturation_audit.yml` push workflow also fired on the branch and failed immediately; it is not the registered recurrent-EOM transfer workflow and does not alter this result.

## Binding outcome

Exact verdict:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER`

Recurrent-EOM selected a different node set from vanilla EOM, so the mechanism was active.

### 2020

Vanilla HDBSCAN EOM parent:

- recovered @25: `21`
- recovered @50: `43`
- recovered @100: `76`
- recovered @500: `145`
- top-100 dominant precision: `0.6830540402353985`
- MRR: `0.030795340109872123`
- qualified matches: `161`
- median top-500 fragmentation: `1.0`

Recurrent-EOM successor:

- recovered @25: `21`
- recovered @50: `43`
- recovered @100: `76`
- recovered @500: `144`
- top-100 dominant precision: `0.6785455284703111`
- MRR: `0.031182021055282318`
- qualified matches: `157`
- median top-500 fragmentation: `1.0`

The frozen per-year gate failed because top-100 dominant precision was lower than the parent.

### 2021

Vanilla HDBSCAN EOM parent:

- recovered @25: `20`
- recovered @50: `43`
- recovered @100: `77`
- recovered @500: `161`
- top-100 dominant precision: `0.6945394546080069`
- MRR: `0.0278370491665274`
- qualified matches: `181`
- median top-500 fragmentation: `1.0`

Recurrent-EOM successor:

- recovered @25: `22`
- recovered @50: `44`
- recovered @100: `78`
- recovered @500: `158`
- top-100 dominant precision: `0.6825274413548328`
- MRR: `0.027976520311187948`
- qualified matches: `180`
- median top-500 fragmentation: `1.0`

The successor strictly improved recovered @25, @50 and @100 and slightly improved MRR, but the frozen per-year gate still failed because top-100 dominant precision was lower than the parent.

## Interpretation and closure

This is mixed evidence, but the preregistered gate was conjunctive and therefore the scientific classification is **NEGATIVE**. The result does not support relaxing the precision gate, changing the recurrent-stability combiner, adding a year weight, changing the speed scale, modifying HDBSCAN parameters, reranking the same candidates, or searching alternate metrics on 2020/2021. Those would be result-informed rescues and are not authorized.

The promoted 2022/2023 development result and exposed SonotaCo 2013/2014 4/4 v31-superiority result remain historical facts, but this retrospective transfer demonstrates that recurrent-EOM v1 is not uniformly superior to vanilla EOM across all archived GMN year pairs under the frozen gate.

## Firewall

- protected solar longitude `[20°,55°]` remained excluded
- `target_information_access=false`
- `target_region_events_accessed=false`
- `sonotaco_2013_2014_access=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `post_result_parameter_search=false`
