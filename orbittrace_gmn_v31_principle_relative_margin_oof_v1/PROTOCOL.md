# OrbitTrace GMN v31-principle local-scale-relative margin OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 successor diagnostic** to the binding `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF` parent. It does not access SonotaCo, OrbitTrace target information, protected 20°–55° events, MAARSY, or DMS.

The parent demonstrated that strict whole-shower OOF nearest-positive / nearest-nonpositive family geometry adds useful ranking signal. Its raw margin is `d_nonpositive - d_positive`. That absolute gap can be influenced by local feature-space density: the same raw difference can represent strong separation when both reference distances are small, or weak separation when both are large. This successor tests one parameter-free correction: **normalize the signed reference gap by the candidate's own local reference-distance scale**, then restore the parent score's typical physical scale before applying the already-frozen diversity machinery.

This motivation and formula are frozen before outcome. No SonotaCo result is used to choose the formula.

## Immutable parent

Candidate universe, memberships, hard order, 23D intrinsic representation, five whole-shower folds, recoverability reference definition, k=1 Euclidean reference distances, diversity (`lambda=0.8`, `scale=1.0`), and equal rank-sum fusion with the immutable P19 hard order are all unchanged.

Binding parent controls:
- OOF raw-margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- recovered@100: `66`
- recovered@50: `41`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified families: `95`

The same execution must reproduce those parent controls exactly before the successor is considered technically valid.

## Sole scientific change: local-scale-relative margin

For every held-out family under the exact parent OOF folds, compute the same two distances:
- `d_pos`: Euclidean distance to the single nearest positive training reference;
- `d_neg`: Euclidean distance to the single nearest nonpositive training reference.

Define candidate local reference scale:

`local_scale = (d_pos + d_neg) / 2`.

Fail closed if any `local_scale <= 0` or is nonfinite. No epsilon, clipping, or floor is introduced.

Define dimensionless relative contrast:

`relative_contrast = (d_neg - d_pos) / local_scale`.

After all OOF families have been scored, define one deterministic global rescaling constant:

`global_scale = median(local_scale over all 226 held-out families)`.

The sole successor score is:

`relative_margin = relative_contrast * global_scale`.

This makes the score responsive to **relative** positive/nonpositive separation while restoring the typical distance scale of the parent margin so the unchanged diversity penalty is not implicitly reweighted merely by a units change.

There is no alternative denominator, mean/quantile global scale, clipping, winsorization, transform, exponent, epsilon, or score calibration.

## Frozen post-score machinery

Use exactly the parent:
- centroid geometry;
- diversity order with `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- one equal rank-sum fusion with the immutable hard order.

The relative-margin diversified order is diagnostic; the equal-rank fused order is the sole promotion candidate.

## Binding gate

The first technically valid result is binding.

PASS requires the sole fused relative-margin order simultaneously to:
- recover strictly more than `66` qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact local-scale-relative successor. No alternate normalization, denominator, rescaling, k, metric, feature, scaling, diversity, fusion, threshold, or post-result rescue is authorized.

A PASS would establish only a target-excluded GMN mechanism improvement and may motivate a separately frozen cross-dataset successor. It does not authorize SonotaCo tuning.

## Firewall

- blind exclusion `[20.0,55.0]` remains mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
