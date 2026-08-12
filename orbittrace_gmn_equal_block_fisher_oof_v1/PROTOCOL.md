# OrbitTrace GMN equal-physical-block Fisher OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor** to the binding `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF` method. It is frozen before outcome and uses no SonotaCo 2013/2014 result, OrbitTrace target information, protected 20°–55° target-region event, MAARSY, or DMS information to choose its mechanism.

The Fisher parent treats the exact 23D representation as one joint vector. That representation was fixed before truth as three physically distinct blocks of unequal dimensionality:
- structural: columns `0:10` (10 dimensions);
- cohesion: columns `10:17` (7 dimensions);
- centroid-neighborhood: columns `17:23` (6 dimensions).

The parent success establishes that a global linear recoverability direction exists. The failed QDA successor establishes that adding class-specific quadratic geometry does not improve it. This successor asks a different question: **does the Fisher signal become more robust when the three pre-existing physical views contribute equally, instead of allowing the highest-dimensional/correlated block to dominate the joint covariance solution?**

The block boundaries are inherited exactly from the parent feature construction and are not selected from any block-wise outcome. No block subset, block weight, or alternate consensus is evaluated.

## Authoritative parent

Binding parent: `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`.

Exact controls that must reproduce before successor interpretation:
- candidate count: 226;
- feature dimension: 23;
- feature SHA256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- hard-order SHA256: `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`;
- k=1 parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- scaled Fisher score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`;
- recovered@100: `69`;
- recovered@50: `41`;
- top-100 dominant precision: `0.7677499561973543`;
- MRR: `0.05055989766869564`;
- qualified families: `95`.

Use only the exact `PASS_GMN_DEVELOPMENT_FIXTURE_V1` cache and fail closed on all hashes and parent controls. The fixture is engineering-only and candidate generation/memberships remain immutable.

## Exact OOF setup

Use the exact fixture:
- 226×23 feature matrix;
- positive/nonpositive recoverability vector;
- deterministic five-fold whole-shower groups/folds;
- centroid matrix;
- hard families, truths, eligible recurrent-label universe, IDs, and hard order.

For each fold, fit the exact parent arithmetic mean and population standard deviation (`ddof=0`) on all 23 training dimensions, replacing only exactly-zero SD by `1.0`, and z-transform training and held-out rows. This one parent z-transform is used for both the joint-parent reconstruction and all block models.

## Exact Fisher parent reconstruction

Reconstruct the binding 23D Fisher parent exactly in every fold:
- positive and nonpositive class means;
- separate `LedoitWolf(assume_centered=False, store_precision=False)` covariances;
- equal-class pooled covariance `0.5*Sigma_pos + 0.5*Sigma_neg`;
- `w = solve(Sigma, mu_pos - mu_neg)`;
- equal-prior midpoint;
- raw held-out score `dot(x-midpoint,w)`;
- original parent unit preservation against the fixture k=1 OOF margin.

Require the reconstructed scaled Fisher score SHA256 and all 69-parent metrics above to match exactly before the block successor is interpreted.

## Sole scientific change: equal physical-block Fisher experts

Using the same fold z-space and exact recoverability classes, fit **three independent balanced shrinkage Fisher discriminants**, one on each frozen block:

- structural columns `0:10`;
- cohesion columns `10:17`;
- neighbor columns `17:23`.

For each block independently:
1. compute positive and nonpositive block means;
2. fit separate positive/nonpositive Ledoit-Wolf covariance matrices on the block training vectors;
3. form `0.5*Sigma_pos + 0.5*Sigma_neg`;
4. require finite, symmetric, positive-definite pooled covariance;
5. solve the block Fisher direction;
6. use the equal-prior block midpoint;
7. compute one raw held-out block score.

After strict OOF scoring of all 226 families, define for each block `b`:

`A_b = median(abs(score_b))`.

Require all three `A_b` values finite and strictly positive. Define scale-neutral block evidence:

`u_b = score_b / A_b`.

The sole combined block score is the **equal arithmetic mean**:

`c = (u_structural + u_cohesion + u_neighbor) / 3`.

There is no median/min/max combiner, block subset, block weighting, sign voting, learned stacking, or block-specific threshold.

### Frozen diversity-unit preservation

Because the unchanged diversity routine subtracts a fixed proximity penalty directly from score units, restore the combined score to the typical absolute scale of the exactly reconstructed Fisher parent:

- `A_parent = median(abs(fisher_scaled))`;
- `A_combined = median(abs(c))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_combined`;
- sole successor diversity input `c_scaled = c * unit_factor`.

This positive scalar multiplication cannot change the pre-diversity combined ordering or sign. No alternate scaling statistic or calibration is allowed.

## Frozen ranking and binding gate

Apply exactly the parent:
- centroid geometry;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- one equal rank-sum fusion with immutable P19 hard order.

The first technically valid outcome is binding.

PASS requires the sole fused equal-block Fisher order simultaneously to:
- recover **strictly more than 69** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7677499561973543`;
- MRR at least `0.05055989766869564`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact equal-block Fisher architecture. No block subset, weight, alternative consensus, covariance change, feature change, parent/block blend, score calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

A PASS is GMN target-excluded development only. A later cross-dataset transfer is not automatically authorized and should require a materially stronger GMN advance under separately frozen governance.

## Firewall

- blind exclusion `[20.0,55.0]` mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
