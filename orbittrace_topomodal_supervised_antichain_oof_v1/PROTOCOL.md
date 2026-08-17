# OrbitTrace TopoModal supervised antichain OOF v1 — frozen protocol

## Status and scientific role

**FROZEN BEFORE IMPLEMENTATION AND BEFORE THE FIRST SCIENTIFIC ENDPOINT FOR THIS SUCCESSOR.**

This is one separately named successor experiment motivated by two already-binding facts:

1. `topomodal support-resolved cut v1` preserved substantially more qualified streams and much higher precision than recurrent-EOM at both sparse scales, but failed only its two MRR gates; and
2. historical v29 nested-capacity OOF ranking was run on the older v17/v19 URC/HDBSCAN/Sugar proposal universe, not the later #1284 physical-6D ToMATo hierarchy.

This experiment therefore asks one narrow question: **can a rigorously whole-shower-cross-fitted supervised utility model select and prioritize a non-overlapping antichain from the unchanged #1284 TopoModal hierarchy well enough to preserve its recovery/precision advantage while repairing MRR?**

It is not a rescue of the closed support-resolved cut. The support-resolved recursion and its emitted catalogue are not reused. The immutable source universe is the complete eligible #1284 hierarchy itself.

A failure permanently closes this exact supervised TopoModal antichain mechanism. No feature, capacity, fold, target, score, DP, threshold, tie-break, or gate may be changed as a v1 rescue.

## 1. Firewall and immutable data

Use only target-excluded GMN 2022+2023 development data and exactly the eight frozen `ORBITTRACE_SCALE_STRESS_V1` sparse panels:

- denominators `128` and `1024`;
- buckets `0,1,2,3`;
- `H(eid)=uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Inclusive solar longitude `[20.0,55.0]` is removed upstream before geometry, features, hierarchy construction, labels, model fitting, ranking, or evaluation.

Before any shower truth is used, reproduce byte-for-byte the authoritative #1284 hierarchy structural result from run `31955621864`, SHA-256 `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`, including every panel's eligible membership set. Reproduce the same recurrent-EOM comparator memberships used by the support-resolved experiment.

Forbidden in this experiment: OrbitTrace target information/events, SonotaCo scientific access, ASFN/EFN event-level access, AMOS scientific access, MAARSY, DMS, protected-region events, station metadata, orbit elements, uncertainty metadata, HDBSCAN overlap as a feature, and any post-result feature/model search.

## 2. Immutable TopoModal hierarchy

Use unchanged #1284 geometry and hierarchy:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`;
- physical six-dimensional embedding;
- symmetric Euclidean `cKDTree` radius graph `r=1.0`, including self;
- `rho_i = |N_i| / n`, including self;
- GUDHI `3.12.0` manual ToMATo;
- complete leaf/internal/root hierarchy;
- candidate eligibility iff exact hierarchy-node support is at least `4`.

No membership is generated, expanded, merged, split, trimmed, or moved by the supervised model.

## 3. Frozen label-free feature map

For every eligible hierarchy node `C`, compute exactly these 16 features before truth. No absolute solar longitude, radiant coordinate, velocity centroid, event ID, bucket ID, denominator ID, prior rank, HDBSCAN quantity, or truth-derived quantity is included.

Let `n=|C|`, `N` be panel size, `n22/n23` be annual supports, `peak` the inherited active-mode peak density, and `outside` the parent merge level (`0` for a connected-component root). Let `contrast=max(0, peak-outside)`. Let `rho` be the frozen radius-count density. Let `depth` be edges from the component root and `max_depth` the maximum node depth in that panel. For an internal node with children of supports `a,b`, let `lo=min(a,b)`, `hi=max(a,b)`; leaf child features are zero.

Feature order is exactly:

1. `log1p(n)`;
2. `n / N`;
3. `log1p(min(n22,n23))`;
4. `min(n22,n23) / max(n22,n23)` if the maximum is positive, else `0`;
5. `min(n22,n23) / n`;
6. `peak`;
7. `outside`;
8. `contrast`;
9. `contrast / max(peak,1e-15)`;
10. mean `rho` over members;
11. median `rho` over members;
12. root indicator;
13. leaf indicator;
14. `depth / max(max_depth,1)`;
15. `lo / hi` for an internal node, else `0`;
16. `lo / n` for an internal node, else `0`.

All features must be finite. The feature matrix, candidate memberships, parent/child relations, annual supports, comparator memberships, panel universes, source hashes, and firewall flags are written to one immutable pretruth JSON and SHA-256 sealed before the supervised stage opens shower truth.

## 4. Frozen supervised target and whole-shower grouping

The supervised stage may use only the already-exposed target-excluded GMN shower map outside `[20°,55°]`.

For each candidate and each eligible known-shower label, compute its ordinary membership F1 separately in 2022 and 2023 using the parent evaluator's annual eligible-shower support counts. If a label is ineligible in a year, its F1 for that year is exactly zero.

Choose one deterministic group label for the candidate by maximizing, in order:

1. `min(F1_2022,F1_2023)`;
2. mean annual F1;
3. maximum annual F1;
4. lexicographically smallest label for an exact numerical tie.

If the winning label has maximum annual F1 equal to zero, the candidate is a negative. Otherwise its group is `SHOWER/<label>` and its two regression targets are that label's exact `F1_2022` and `F1_2023`. Negatives have both targets zero and group `NEG/<denominator>/<bucket>/<family_hash>`.

The same shower label has one group globally across both sparse scales and all four buckets. Thus every fragment/version assigned to that shower is held out together.

## 5. Deterministic five-fold OOF

Group fold is fixed as

`uint64_be(SHA256('ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1|' + group)[0:8]) mod 5`.

All candidates from a group are in exactly one outer fold. No held-out group's targets enter its own model fit or capacity selection.

Use the frozen #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990` only for its `model()` ExtraTrees implementation and `grouped_weights(...)`. The feature map is the 16-D TopoModal map above, not the nonportable 71-D URC representation.

Exactly v29's three capacities are eligible:

1. `baseline_d4_l5`: `max_depth=4`, `min_samples_leaf=5`;
2. `medium_d8_l3`: `max_depth=8`, `min_samples_leaf=3`;
3. `high_unbounded_l2`: `max_depth=None`, `min_samples_leaf=2`.

All other `model()` parameters remain unchanged. No fourth capacity, estimator count, random seed, model class, target transform, feature subset, or score blend is authorized.

Within each outer fold, choose capacity using only the four outer-training fold IDs as four-fold inner OOF. Fit separate annual regressors. Combine inner predictions by `min(pred_2022,pred_2023)`. Capacity criterion is exactly v29's full-list group-level NDCG:

- predicted group score = maximum combined prediction among that group's candidates;
- group relevance = maximum `min(F1_2022,F1_2023)` among that group's candidates;
- gain `2^relevance - 1`;
- discount `1/log2(rank+2)`;
- stable group ID tie-break;
- exact capacity tie preference: baseline, then medium, then high.

Refit the selected capacity on all outer-training candidates separately for 2022 and 2023 and predict only the untouched outer fold. The complete OOF utility is `min(pred_2022,pred_2023)`.

## 6. Learned antichain selector

The OOF utility changes no membership. For each panel, apply one deterministic maximum-weight tree recursion independently to every frozen TopoModal component root.

For eligible node `C`:

- node value = `max(0, OOF_utility(C))`;
- child value = sum of each eligible immediate child's recursively optimal value; an ineligible child contributes zero and cannot be selected.

Select the current node iff its node value is strictly positive and is greater than or equal to the child value. Otherwise select the union of child optima. The equality tie therefore favors the parent exactly when its value is positive.

The union over roots is the complete supervised antichain. It must be pairwise disjoint and contain only exact #1284 nodes of support at least 4.

Rank selected nodes only by:

1. descending OOF utility;
2. ascending `family_hash`.

No threshold other than positivity, target candidate count, diversity penalty, rank fusion, modal-contrast blend, support-resolved recursion, or post-hoc overlap rule is allowed.

## 7. Comparator, budget, and binding sparse-GMN gate

For each panel require the supervised antichain candidate count to be at least the exact recurrent-EOM comparator count. Capacity failure in any panel is a binding scientific FAIL; do not reduce the benchmark budget to rescue it.

With that requirement satisfied, evaluate both methods at exactly the recurrent-EOM candidate count for that panel, using the unchanged support-resolved evaluator semantics separately in 2022 and 2023.

Aggregate exactly the same ten gates as support-resolved cut v1:

Fine (`d=1024`):

1. successor qualified total strictly greater than comparator;
2. qualified nonloss in at least 6/8 bucket-year panels;
3. mean MRR at least comparator;
4. mean top-100 dominant precision at least comparator;
5. mean median-fragmentation no higher than comparator.

Coarse (`d=128`):

6. successor qualified total at least comparator;
7. qualified nonloss in at least 6/8 bucket-year panels;
8. mean MRR at least comparator;
9. mean top-100 dominant precision at least comparator;
10. mean median-fragmentation no higher than comparator.

`PASS_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1` requires candidate-capacity PASS in all eight panels and all ten numerical gates. Any other technically valid result is `FAIL_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1`.

This is a sparse target-excluded GMN development gate only. It does not promote the method over the current full-GMN champion. A PASS would authorize a separately preregistered full-GMN scaling/comparison step before any SonotaCo access.

## 8. Closure

The first technically valid result is binding.

- FAIL permanently closes supervised TopoModal antichain OOF v1. No feature additions/removals, score blends, alternate targets, fold salts/counts, capacity changes, DP changes, thresholds, support changes, or reranking rescues.
- PASS freezes the exact mechanism for a separately preregistered full-GMN scaling test. SonotaCo remains inaccessible until the required GMN progression is satisfied.

At all times protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo, AMOS, MAARSY, and DMS remain inaccessible to this run.