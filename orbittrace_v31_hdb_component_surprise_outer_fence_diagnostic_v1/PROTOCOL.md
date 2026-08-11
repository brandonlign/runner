# OrbitTrace v31 HDB component-surprise outer-fence diagnostic v1

## Scientific role

Post-result diagnostic only after binding v40 failed 2/4 and the joint nested HDB oracle diagnostic #1071 established that a single top-9 ⊂ top-11 HDB ordering can clear both exposed SonotaCo years with only a very small number of substitutions.

The diagnostic does **not** evaluate a successor, rerank, replacement rule, score fusion, or cutoff-aware selector. Its purpose is to test one new mechanism suggested by the failure mode of v39/v40: useful cross-route component evidence may exist only in a sparse extreme tail, while globally transferring or globally sorting by that evidence is too broad.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. A positive diagnostic result is not external validation.

## Frozen source material

The diagnostic consumes only two already-authoritative artifacts:

1. v40 binding development run `31455562054`, artifact `9087888653`, digest
   `sha256:f74cb12bd5b1c958720bd6f1cd5a2d373dc3398e354053ada7a130822505c5d3`.
   Only the HDB component-representative rows and their already-frozen exact-v31/component-evidence fields are used to define the extreme set.
2. #1072 component-closure diagnostic run `31455141716`, artifact `9087743465`, digest
   `sha256:8c45c00fd70300efb2f6f32bbb339141f8c34884ee5b1098c1bbb45ccf1a59cc`.
   This is loaded only **after** the extreme set has been written and frozen, and is used only for surfaced/missed recoverable-group diagnosis.

No OrbitTrace target data, target-region events, MAARSY, or DMS may be accessed.

## Phase 1: freeze the truth-blind extreme-surprise set

Before loading #1072 truth-aware diagnostic material, read the authoritative v40 result and require:

- binding verdict `FAIL_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT`;
- exact pretruth graph SHA `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact pretruth component SHA `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- exact HDB v31 fused-order SHA `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`;
- exactly 138 HDB route-component representatives.

For each HDB component representative `C`, define the single diagnostic quantity

`D(C) = representative_v31_percentile - component_evidence`.

Because the representative is the best HDB v31 member of its component and `component_evidence` is the best normalized v31 percentile over either route, `D(C) >= 0`. Larger values mean the physical component is ranked much better somewhere across the frozen cross-route component than HDB ranks its own best representative.

Using all 138 `D(C)` values, compute Q1 and Q3 with NumPy linear quantiles and `IQR = Q3-Q1`. Define the **Tukey outer fence**

`T = Q3 + 3*IQR`.

The frozen extreme-surprise set contains exactly those HDB components with `D(C) > T`.

This is a conventional robust outer-fence rule. The factor 3 is fixed before any surfaced/missed truth is loaded and is not searched. No alternative multiplier, MAD rule, percentile cutoff, top-k rule, rank window, budget, year, or route-specific threshold is evaluated.

The Phase-1 file must be written with `truth_accessed=false` before the #1072 artifact is downloaded.

## Phase 2: exposed diagnostic only

After the extreme set is frozen, load the authoritative #1072 component-closure diagnostic and preserve its exact annual recoverable-group rows.

For each year 2013 and 2014 separately, among the already-defined annual recoverable HDB strict groups:

- `surfaced` means the #1072 representative is already surfaced by the exact v31 HDB literature-budget prefix;
- `missed` means recoverable but not surfaced by that prefix;
- an annual group is `extreme` iff its frozen `component_id` is in the Phase-1 extreme-surprise component set.

Report, separately for surfaced and missed groups:

- count;
- number on extreme-surprise components;
- extreme fraction.

## Predeclared interpretation gate

The sparse extreme-surprise mechanism is considered diagnostically supported only if **both** years satisfy:

1. at least one missed recoverable HDB group lies on an extreme-surprise component; and
2. the extreme-surprise fraction among missed recoverable groups is strictly greater than the corresponding fraction among surfaced recoverable groups.

No minimum effect size beyond strict inequality is selected.

A PASS authorizes at most one separately frozen successor based on the exact outer-fence extreme set. It does not select a promotion position, replacement rule, number of corrections, budget-specific action, or any alternate threshold. A FAIL closes this exact Tukey-outer-fence component-surprise mechanism.

## Explicit non-search commitments

No:

- successor or total order;
- oracle family/group identity use;
- v40 rescue or altered v40 ordering;
- component evidence aggregation search;
- threshold multiplier search;
- percentile/MAD/top-k/rank-window alternative;
- route-, year-, or budget-specific rule;
- radius/metric/graph/component-definition search;
- candidate-generation or membership change;
- feature/model/k/scaling/annual-combiner/diversity/fusion/source-quota search;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- `target_information_access=false`.
- `target_region_events_accessed=false`.
- `maarsy_scientific_access=false`.
- `dms_scientific_access=false`.
