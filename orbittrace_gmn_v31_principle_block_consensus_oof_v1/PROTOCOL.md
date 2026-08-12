# OrbitTrace GMN v31-principle physical-block consensus OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 successor diagnostic** to the binding `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF` parent. It does not access SonotaCo, OrbitTrace target information, protected 20°–55° events, MAARSY, or DMS.

The successful parent uses one 23D intrinsic family representation composed, before truth, of three physically distinct blocks that were already fixed by construction:
- intrinsic structural: columns `0:10` (10 dimensions);
- event-cohesion: columns `10:17` (7 dimensions);
- centroid-neighborhood geometry: columns `17:23` (6 dimensions).

A single 23D Euclidean margin can be strong even when driven primarily by one block. A scientifically more robust family-recoverability signal would be supported across independent structural views rather than depending on one feature class. This successor therefore tests one fixed **three-block consensus** construction while preserving the exact parent labels, folds, nearest-reference rule, diversity, and final hard-order fusion.

The three blocks are not selected from outcomes; they are exactly the pre-existing blocks in the parent feature constructor. No SonotaCo result is used to choose them or the consensus rule.

## Immutable parent

Unchanged:
- exact 226 P19 hard families and memberships;
- immutable hard order;
- exact 23D intrinsic representation and column order;
- target-excluded GMN catalogue;
- recoverability reference definition;
- deterministic five-fold whole-shower groups;
- fold-training-only population z-standardization;
- `k=1` nearest positive and nearest nonpositive reference;
- ordinary Euclidean distance within each tested feature space;
- signed margin convention `d_nonpositive - d_positive`;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- one equal rank-sum fusion with immutable P19 hard order.

Binding parent controls that must reproduce exactly in the same execution before successor interpretation:
- full-23D OOF margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- recovered@100: `66`;
- recovered@50: `41`;
- top-100 dominant precision: `0.7229521515453452`;
- MRR: `0.050244164168646674`;
- qualified families: `95`.

## Sole scientific change: physical-block consensus margin

For every exact parent fold, first compute the parent training mean and population standard deviation independently for all 23 dimensions, with zero standard deviations replaced by 1 exactly as in the parent. Use that one parent z-transform. Then compute four OOF margins for every held-out family:

1. `m_full`: parent Euclidean nearest-reference margin using all 23 z-scored dimensions;
2. `m_struct`: same rule using only columns `0:10`;
3. `m_cohesion`: same rule using only columns `10:17`;
4. `m_neighbor`: same rule using only columns `17:23`.

All reference labels and `k=1` semantics are identical across the four views.

After all OOF margins have been constructed, define one deterministic scale for each block:

- `A_struct = median(abs(m_struct))`;
- `A_cohesion = median(abs(m_cohesion))`;
- `A_neighbor = median(abs(m_neighbor))`.

Require each to be finite and strictly positive. Define block-standardized signed margins:

- `u_struct = m_struct / A_struct`;
- `u_cohesion = m_cohesion / A_cohesion`;
- `u_neighbor = m_neighbor / A_neighbor`.

The sole consensus contrast is the elementwise median of those three equally weighted standardized margins:

`c = median(u_struct, u_cohesion, u_neighbor)`.

There is no minimum, maximum, mean, weighted mean, voting threshold, sign count, learned combiner, block deletion, or block search.

### Frozen unit preservation for unchanged diversity

Because the parent diversity routine subtracts a fixed proximity penalty directly from the score, the consensus must be restored to the parent's typical margin magnitude before diversity is applied.

Define:

- `A_full = median(abs(m_full))`;
- `A_consensus = median(abs(c))`;
- require both finite and strictly positive;
- `unit_factor = A_full / A_consensus`;
- sole successor score `m_consensus = c * unit_factor`.

This is a positive scalar multiplication after the consensus ordering is fixed. It cannot alter the pre-diversity consensus sign or ordering and is used only to preserve the parent score's typical absolute scale under the unchanged diversity penalty.

No alternative scale statistic, clipping, winsorization, epsilon, nonlinear transform, or calibration is allowed.

## Frozen post-score machinery

Apply exactly the parent `diversity_order` to `m_consensus` with `lambda=0.8`, `scale=1.0`, then exactly one equal rank-sum fusion with the immutable hard order. No fusion or diversity alternatives are evaluated.

## Binding gate

The first technically valid outcome is binding.

PASS requires the sole fused block-consensus order simultaneously to:
- recover **strictly more than 66** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact block-consensus successor. No block subset, alternate scale, alternate consensus, threshold, weight, k, metric, diversity, fusion, or post-result rescue is authorized.

A PASS establishes only a target-excluded GMN mechanism improvement and may motivate a separately frozen cross-dataset successor.

## Firewall

- blind exclusion `[20.0,55.0]` mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
