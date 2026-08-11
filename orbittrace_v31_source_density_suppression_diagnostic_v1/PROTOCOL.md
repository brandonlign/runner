# OrbitTrace v31 proposal-source density suppression diagnostic v1

## Scientific role

Post-v60 exposed-development **mechanism diagnostic only**. No new candidate order, source quota, source-normalized ranker, or literature panel is evaluated.

Exact v31 remains the parent. The immutable #950 HDB universe is the union of three already-frozen candidate proposal mechanisms with strongly unequal cardinalities:

- `hard`: 19 families;
- `p19`: 54 families;
- `p20`: 156 families.

The proposal-source field is immutable pretruth metadata and is already part of the fixed #950 payload. This diagnostic asks one narrow question: **are annual-recoverable HDB groups missed by exact v31 represented by families that rank substantially better within their own proposal source than they rank in the pooled 229-family universe, compared with groups v31 already surfaces?**

A PASS is only evidence for source-density suppression. It does not authorize quotas, source-specific budgets, source weights, or a source-normalized successor automatically.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Frozen rank/source vector before #1046 status

Before authoritative #1046 surfaced/missed status is restored, reconstruct the exact v31 HDB fused order under immutable #950/#839/v31 provenance.

The exact v31 fused-order SHA-256 must be

`85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`.

Use the immutable #950 `sources` vector aligned exactly to `family_ids`. Require the source universe and counts to be exactly:

`{"hard":19,"p19":54,"p20":156}`.

For each HDB family i define:

- `r(i)` = exact v31 fused rank, 1..229;
- `p_global(i) = (r(i)-1)/(229-1)`;
- `s(i)` = immutable proposal source;
- `r_s(i)` = rank of i among families with the same source when sorted by `(r(i), family_id)`;
- `n_s` = fixed candidate count for that source;
- `p_source(i) = (r_s(i)-1)/(n_s-1)`;
- `A(i) = p_global(i) - p_source(i)`.

All source counts exceed one, so no singleton fallback exists.

Positive `A(i)` means the family ranks better relative to candidates produced by its own proposal mechanism than it does in the pooled universe; equivalently, pooled competition suppresses it relative to its source-local standing.

Freeze the complete 229-family vector containing only family ID, immutable source, v31 rank, global percentile, within-source rank, within-source percentile, and `A(i)` before #1046 status is available.

No shower label, annual recoverability, surfaced/missed flag, literature budget, oracle identity, or #1046 row may enter this vector.

## Status source after freeze

Only after the complete source-density vector is frozen, restore authoritative #1046:

- run `31451236076`;
- artifact `9086399760`;
- artifact digest `sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69`;
- result SHA-256 `e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758`;
- verdict `PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC`;
- role `POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED`.

Use exactly #1046's already-frozen `first_recoverable_family_id_by_v31_fused_rank` for each annual candidate-recoverable shower group. No alternate representative is allowed.

Expected populations:

- 2013: 18 candidate-recoverable groups = 9 surfaced + 9 recoverable-but-missed;
- 2014: 19 candidate-recoverable groups = 9 surfaced + 10 recoverable-but-missed.

Any mismatch fails closed.

## Sole statistic and gate

For each year separately, attach `A(i)` from the frozen vector to each #1046 fixed first-recoverable family.

Compare only:

- median source advantage A among recoverable-but-missed groups;
- median source advantage A among v31-surfaced-recoverable groups.

PASS requires both strict conditions in both years:

1. missed-recoverable median `A > 0`;
2. missed-recoverable median `A` is strictly greater than surfaced-recoverable median `A`.

All four inequalities must pass. Empty strata fail closed.

There is no source selection, source-wise subgroup test, chi-square test, p-value, AUC, effect-size threshold, source count threshold, top-k, rank window, budget action, or second statistic.

## Interpretation boundary

If PASS: conclude only that fixed proposal-source density disproportionately suppresses missed recoverable HDB groups in both exposed years. Any source-normalized successor must be separately frozen as one complete route-general rule before panel evaluation.

If FAIL: close the exact source-density suppression mechanism. Do not rescue it by selecting one source post hoc, source quotas, source-specific budgets, source weights, source-specific rank windows, source count exponents, source-specific scaling, or outcome-conditioned source treatment.

## Explicit non-search commitments

No:

- source quota or source-specific budget;
- source weighting/exponent;
- candidate order or literature panel evaluation;
- alternate within-source percentile definition;
- source-wise outcome subset selection;
- feature/metric/k/scaling/threshold/annual-combiner/diversity/fusion/model/component/topology/cross-route search;
- alternate #1046 representative;
- budget/year/rank-window rule;
- oracle identity;
- successor selection;
- post-result second source-density diagnostic.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
