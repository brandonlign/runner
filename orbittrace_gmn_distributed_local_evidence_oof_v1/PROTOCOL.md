# OrbitTrace GMN distributed local-evidence OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor diagnostic**. It starts from the same fixed 226-family universe and 23D intrinsic representation as the binding `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF` parent, but it changes the scoring mechanism at an architectural level.

The prior successful parent asks which single positive and single nonpositive reference are nearest to a held-out family. Four separately frozen small transformations of that score (annual-min, local-scale-relative, shrinkage-Mahalanobis, and physical-block consensus) failed their binding improvement gates and are closed. Further micro-transformations of the k=1 margin are therefore prohibited.

This successor instead asks a different statistical question: **does the held-out family's local neighborhood as a whole carry more class-balanced evidence for recoverable families than for nonrecoverable families?** It uses all OOF training references through one fixed radial evidence kernel rather than selecting a nearest reference from each class.

No SonotaCo data or result is used to choose this mechanism.

## Immutable scientific inputs

Unchanged from the successful parent:
- exact 226 P19 hard families and memberships;
- immutable P19 hard order;
- exact target-excluded GMN 2022/2023 catalogue;
- exact 23D intrinsic family representation (10 structural + 7 cohesion + 6 centroid-neighbor dimensions);
- exact recoverability reference target;
- exact deterministic five-fold whole-shower grouping;
- fold-training-only mean and population-standard-deviation z-transform, with only zero SD replaced by 1;
- exact centroid geometry used by the fixed diversity stage;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID ties;
- exactly one final equal rank-sum fusion with immutable hard order.

The execution must reproduce the binding parent full-space k=1 Euclidean OOF margin and metrics before the distributed-evidence candidate is interpreted:
- parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- recovered@100: `66`;
- recovered@50: `41`;
- top-100 dominant precision: `0.7229521515453452`;
- MRR: `0.050244164168646674`;
- qualified families: `95`.

## Distributed local-evidence mechanism

For each exact parent fold:

1. Construct the exact parent training and held-out z-vectors in all 23 dimensions.
2. Using **training vectors only and no recoverability labels**, compute each training vector's ordinary Euclidean distance to its nearest *other* training vector.
3. Define the sole fold bandwidth `h` as the median of those nearest-neighbor distances.
4. Require `h` finite and strictly positive. No epsilon, floor, clipping, bandwidth multiplier, or fallback is allowed.
5. For a held-out vector `x`, compute ordinary Euclidean distance `d_i` to every training reference.
6. Define each reference's fixed Gaussian log evidence

   `ell_i = -0.5 * (d_i / h)^2`.

7. Split those log evidences only now by the exact parent training recoverability class.
8. Compute class-balanced log evidence using a numerically stable log-mean-exp separately for positive and nonpositive training references:

   `L_pos = log(mean(exp(ell_i)))` over positive references;

   `L_neg = log(mean(exp(ell_i)))` over nonpositive references.

9. The sole raw candidate score is

   `e = L_pos - L_neg`.

Using means rather than sums removes training-fold class-count imbalance from the score. The common Gaussian normalization constant cancels in the log ratio because both classes use the same 23D space and the same fold bandwidth.

There is no class-prior term, k-neighbor truncation, compact kernel, alternate kernel, alternate bandwidth statistic, bandwidth search, supervised bandwidth, adaptive per-class bandwidth, temperature, clipping, or evidence calibration.

## Frozen score-unit preservation

The fixed diversity routine subtracts its proximity penalty directly from the score, so raw log-evidence units cannot be passed into it without changing the effective diversity weight.

After all OOF scores are complete, define:
- `A_parent = median(abs(parent_margin))`;
- `A_evidence = median(abs(e))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_evidence`;
- sole diversity input `e_scaled = e * unit_factor`.

This is a positive scalar multiplication only. It cannot alter the distributed-evidence score's sign or pre-diversity ordering. No alternative scale statistic or transform is evaluated.

## Frozen ranking and gate

Apply the exact parent diversity to `e_scaled`, then exactly one equal rank-sum fusion with immutable hard order.

The first technically valid outcome is binding.

PASS requires the sole fused distributed-evidence order simultaneously to:
- recover **strictly more than 66** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact distributed-evidence mechanism. No kernel, bandwidth, prior, truncation, scaling, diversity, fusion, or post-result rescue is authorized.

A PASS establishes only a target-excluded GMN mechanism improvement and may motivate a separately frozen transfer or validation protocol; it does not authorize SonotaCo tuning.

## Firewall

- blind exclusion `[20.0,55.0]` mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
