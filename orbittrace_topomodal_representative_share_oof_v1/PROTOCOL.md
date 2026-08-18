# OrbitTrace TopoModal representative-share OOF v1 — frozen protocol

## Status and scientific role

**FROZEN BEFORE IMPLEMENTATION AND BEFORE THE FIRST OUTCOME FOR THIS SUCCESSOR.**

This is a new target-excluded GMN 2022/2023 development experiment authorized after the earlier TopoModal MRR investigation was resumed. It does **not** retroactively alter the frozen #1263/AMOS endpoint or convert already-exposed GMN development data into a pristine external validation set. A PASS here would establish a better development method and require a separately reserved untouched external validation before any broad literature-superiority claim.

The mechanism is independently motivated by two already-existing OrbitTrace results that predate this experiment:

1. TopoModal supervised antichain OOF v1 on the #1284 hierarchy passed 8/10 gates, improving recovery and precision but failing only conditional MRR at both sparse scales; its supervised targets were raw per-fragment annual F1.
2. GMN representative-share ranking v1 (#1194) prospectively improved recovered@50, recovered@100, top-100 precision, and MRR on a different 4,504-family universe by forcing all fragments of one recoverable shower to share one unit of target mass rather than rewarding every good fragment independently.

The narrow question here is therefore whether **representative-share supervision**, not a new feature/model/ranker hyperparameter, can prevent TopoModal fragments of the same shower from all receiving high utility and thereby repair early ordering while preserving TopoModal's recovery advantage.

## 1. Immutable upstream candidate/feature freeze

Do not regenerate or modify the TopoModal hierarchy, features, Recurrent-EOM comparator, panel universes, or memberships.

Use the exact immutable pretruth artifact from the binding TopoModal supervised antichain OOF v1 run:

- run: `32062821745`
- artifact ID: `9298954965`
- artifact name: `orbittrace-topomodal-supervised-antichain-oof-v1`
- artifact ZIP digest: `sha256:0ec9bad1e6cb4db152e6aca30b7d3e324b158b8494b1c22162ba6f43c8d9baa8`
- `TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH.json` SHA-256: `22ee242d16e73c553d0e2041e55a8d938963c504a824797e92119d15b4bab7ba`

The pretruth must retain:

- schema `ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1_PRETRUTH`;
- exact eight `ORBITTRACE_SCALE_STRESS_V1` panels: denominators 128 and 1024, buckets 0–3;
- exact #1284 physical-6D ToMATo hierarchy candidates, support >= 4;
- exact 16-dimensional label-free feature rows;
- exact Recurrent-EOM comparator memberships and candidate counts;
- protected inclusive solar-longitude exclusion `[20.0,55.0]` before all scientific inputs;
- no target information, SonotaCo, AMOS, MAARSY, DMS, ASFN, or EFN event-level access.

Any byte mismatch is a technical stop, not permission to rebuild the pretruth.

## 2. Frozen label/group semantics

Open only the already-exposed target-excluded GMN 2022/2023 shower map after the exact pretruth hash passes.

For every candidate, reproduce **exactly** the prior supervised-antichain group assignment:

- compute candidate-vs-label F1 separately in 2022 and 2023;
- choose the label by descending `(min annual F1, mean annual F1, max annual F1)`, then lexicographically smallest label;
- if maximum annual F1 is zero, group is `NEG/<denominator>/<bucket>/<family_hash>` and both targets are zero;
- otherwise the global cross-validation group is `SHOWER/<label>`.

The same shower label must remain in one outer fold across both scales and all buckets. Use the **same fold salt as supervised antichain OOF v1**:

`ORBITTRACE_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1|`

so the sole scientific change is the target, not the train/test partition.

## 3. Sole scientific change: panelwise representative-share annual targets

For each panel `P=(denominator,bucket)`, shower group `G`, candidate `i` assigned to `G`, and year `y`, let `f_i,y` be the exact annual F1 reproduced above.

Define

`S_P,G,y = sum_j f_j,y`

over all candidates `j` in the same panel assigned to the same shower group `G`.

The frozen regression target is

`r_i,y = f_i,y / S_P,G,y` if `S_P,G,y > 0`, otherwise `0`.

NEG candidates have `r_i,2022 = r_i,2023 = 0`.

Thus each recoverable shower contributes at most one unit of target mass **per panel and per year**, apportioned directly in proportion to the same raw F1 used by the failed predecessor. This mirrors the previously successful #1194 representative-share principle while respecting that the eight sparse panels are separate ranking problems.

No winner-only target, exponent, temperature, rank transform, clipping, additive constant, group-size term, cross-panel normalization, score blend, raw-F1 interpolation, or alternative target is allowed.

## 4. Frozen learner and nested OOF

Everything except the target remains identical to TopoModal supervised antichain OOF v1:

- exact 16-D feature map from the immutable pretruth;
- exact #839 ExtraTrees model implementation and grouped weights;
- exact three capacities: `baseline_d4_l5`, `medium_d8_l3`, `high_unbounded_l2`;
- exact five whole-shower outer folds and four-fold inner OOF within each outer-training split;
- fit separate 2022 and 2023 regressors;
- combined utility is `min(pred_2022,pred_2023)`;
- inner capacity criterion remains the predecessor's full-list group-level NDCG, but with the frozen representative-share annual targets as relevance;
- no feature/model/hyperparameter search.

## 5. Frozen antichain and ordering

Use the exact predecessor maximum-weight tree recursion without modification:

- node value = `max(0, OOF utility)`;
- child value = sum of recursively optimal eligible child values;
- select the node iff node value is positive and >= child value; equality favors the parent;
- otherwise select the union of child optima.

Selected candidates must be pairwise event-disjoint exact #1284 hierarchy nodes with support >= 4.

Rank only by:

1. descending OOF utility;
2. ascending `family_hash`.

No diversity penalty, overlap post-processing, parent protection, Recurrent rank fusion, score calibration, threshold, quota, budget-specific reranking, or post-hoc ordering rule is allowed.

## 6. Equal-budget evaluation

For every panel, the selected antichain must contain at least the exact Recurrent-EOM comparator candidate count. Otherwise the experiment is a binding scientific FAIL.

Evaluate both methods at exactly that Recurrent-EOM candidate count separately for 2022 and 2023 using the unchanged predecessor evaluator.

Report both MRR definitions:

### Historical conditional MRR
Use the inherited `parent.metrics(...)["mrr"]` unchanged. This is retained because the project historically gated on it.

### Zero-filled eligible-query MRR
For each annual panel, use the inherited `first_rank_by_label` map and exact eligible-label set. Define reciprocal rank `1/r` for an eligible shower recovered first at rank `r`, and `0` for an eligible shower not recovered. Average over **all eligible showers in that annual panel**.

No previously closed method is reclassified using this metric. It is an additional prospective gate here.

## 7. Binding 12-gate endpoint

Fine scale (`d=1024`) must pass all six:

1. qualified total strictly greater than Recurrent-EOM;
2. qualified nonloss in at least 6/8 bucket-year panels;
3. historical conditional mean MRR >= Recurrent-EOM;
4. zero-filled eligible-query mean MRR >= Recurrent-EOM;
5. mean top-100 dominant precision >= Recurrent-EOM;
6. mean median fragmentation <= Recurrent-EOM.

Coarse scale (`d=128`) must pass all six:

7. qualified total >= Recurrent-EOM;
8. qualified nonloss in at least 6/8 bucket-year panels;
9. historical conditional mean MRR >= Recurrent-EOM;
10. zero-filled eligible-query mean MRR >= Recurrent-EOM;
11. mean top-100 dominant precision >= Recurrent-EOM;
12. mean median fragmentation <= Recurrent-EOM.

`PASS_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1` requires capacity PASS in all eight panels and all 12 gates. Any other technically valid result is `FAIL_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1`.

## 8. Closure and firewall

The first technically valid result is binding for this exact mechanism. A FAIL permanently closes this exact representative-share TopoModal OOF architecture; do not tune the target, folds, features, capacities, model, antichain, ranking, budgets, or gates as a rescue.

This experiment is target-excluded GMN development only. It does not authorize SonotaCo, AMOS, protected-region, OrbitTrace-target, MAARSY, DMS, ASFN, or EFN event-level access, and it does not supersede the separately frozen AMOS endpoint. No merge is authorized.