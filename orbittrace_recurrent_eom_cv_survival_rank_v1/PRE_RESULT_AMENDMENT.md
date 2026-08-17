# Pre-result amendment — immutable parent + label-free CV gate

## Why this amendment exists

The first activation (`31995044205`) stopped before producing either `RECURRENT_EOM_CV_SURVIVAL_RANK_V1_PRELABEL.json` or `RECURRENT_EOM_CV_SURVIVAL_RANK_V1_RESULT.json`. It reconstructed only 2,079 recurrent-EOM candidates from the current GMN source, while the promoted recurrent-EOM parent is immutably 2,097 candidates. The run therefore failed closed before the successor ranking or any truth endpoint existed.

This is a reproducibility/input-drift problem, not a scientific outcome. The current GMN source must not replace the exact historical development corpus silently.

## Immutable replacement inputs

The scientific score itself is unchanged from `PROTOCOL.md`.

Full parent is now read only from the exact prelabel artifact of the already-binding density-synchronous development run `31852836840`, artifact `9238142199`:

- artifact digest: `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`;
- `DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_PRELABEL.json` SHA-256: `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- recurrent-EOM parent candidate count: `2,097`;
- recurrent-EOM parent ordered-membership SHA-256: `b903f2a4b653ef240043d2d6a2cfe6163b62ecf2d837bddf727249e92e467b01`.

Only `parent_candidates` and parent provenance fields are permitted from that artifact. Its density-synchronous successor candidates/result are forbidden inputs.

The ten perturbation inputs remain exactly the recurrent-EOM **parent** prelabels from PR #1265 / run `31859724335`. No fold result metric, density-synchronous successor output, or shower truth is permitted.

## Label-free leave-one-fold-out gate

Because the exact 2,097-parent historical corpus can no longer be reconstructed from the live GMN source, this amendment also removes GMN shower truth from successor selection entirely.

For every immutable full parent candidate `C`, compute the already-frozen ten Jaccard survival values `J_f(C)` exactly as specified in `PROTOCOL.md`.

For each held-out fold `f`, form a training-only survival estimate

`survival_-f(C) = mean_{g != f} J_g(C)`

and score

`S_cv,-f(C) = recurrent_stability(C) * survival_-f(C)`.

Rank all 2,097 immutable parent candidates by the exact frozen tie rule, without using `J_f(C)`. Evaluate that held-out ranking only by the mean held-out `J_f` among the top `K = 25, 50, 100` candidates. These K values are inherited from the established recurrent-EOM ranking endpoints and are not tuned here.

The exact parent ranking is evaluated on the same held-out `J_f` values and K values.

`PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_LABEL_FREE_CV` requires all of:

1. all 2,097 exact parent memberships are preserved and the full ten-fold successor order differs from the parent;
2. across the ten held-out folds, the successor's **mean** held-out top-25, top-50, and top-100 Jaccard are each >= the parent's corresponding mean;
3. the successor's **median** fold-level top-100 held-out Jaccard is >= the parent's median;
4. successor top-100 held-out Jaccard is strictly higher than parent in at least `6/10` folds;
5. aggregate mean held-out top-100 Jaccard is strictly higher than parent.

Otherwise the exact CV-survival ranker fails and is closed. No alternate K, fold weighting, Jaccard transform, exponent, score blend, threshold, or second CV rule is authorized from the result.

## Consequence of a PASS

A PASS is evidence of improved **resampling-stable ranking**, not shower-recovery superiority. It authorizes exactly one separately frozen matched comparison on the already-exposed SonotaCo development benchmark. It does not authorize AMOS or any pristine endpoint.

## Superseded execution paths

The live-GMN workflows/runners are retained as technical provenance only and are not valid scientific endpoints for this successor. Any run that reconstructs 2,079 rather than the exact 2,097 immutable parent must fail closed.

Protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo, AMOS, ASFN/EFN labels, MAARSY and DMS remain inaccessible during this label-free CV selection.