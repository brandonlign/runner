# OrbitTrace v31 same-route reference-interference diagnostic v1

## Scientific role

Post-v59 exposed-development **mechanism diagnostic only**. No candidate order, successor, or literature panel is evaluated.

Exact v31 remains the parent. Its strict-OOF local geometry is trained on one stacked Sugar+HDB table: fold scaling and annual positive/nonpositive reference pools both contain families from both routes. That cross-route pooling has never been isolated as a scientific variable. v37 changed fold coverage but explicitly retained the cross-route pool; v39-v58 changed other mechanisms.

This diagnostic asks one narrow question: **for annual-recoverable HDB groups that v31 misses, does removing Sugar families from the nearest-reference pool improve the exact local margin more than it improves the groups v31 already surfaces?**

This is not a same-route ranker. Same-route margins are frozen for all 229 HDB candidates before surfaced/missed status is attached and are used only as a counterfactual mechanism statistic.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Immutable parent

Use exact v31 source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da`, immutable #950 payload/memberships/features/centroids, immutable #839 ranker source, and immutable exposed truth artifact.

Exact v31 controls must reproduce first:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

The exact v31 HDB internal identities must also reproduce:

- annual-margin 2013 SHA-256 `99520a9f07b7cf188002fb79ba03592ffda8724f43c8adfeb97541f038ffdb19`;
- annual-margin 2014 SHA-256 `d989def64913d7d9807c6d2433642fdde5e29d031d315ddff5a8353668f19d00`;
- combined-margin SHA-256 `647e81df101ba7b0e511e618004dc2f01fae166cc78d55461f02a9c811650e7d`;
- local/diversity order SHA-256 `9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595`;
- final fused order SHA-256 `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`.

Any mismatch is an engineering/provenance failure and yields no diagnostic result.

## Exact counterfactual definition

Reconstruct exact v31's stacked Sugar+HDB strict whole-shower deterministic five-fold OOF geometry.

For each fold:

1. fit the **exact v31 stacked-route** training mean and population standard deviation across all 71 features, with zero std -> `1.0`;
2. transform both training and held-out families with that exact stacked-route scaler;
3. construct the exact annual family-level quality targets and annual positive predicate `F1_y > 0.5`;
4. for every held-out HDB family, compute the exact mixed-route nearest-positive and nearest-nonpositive distances from all fold-training Sugar+HDB families;
5. using the **same standardized coordinates, same fold and same annual labels**, recompute only the nearest-reference search after restricting eligible references to fold-training HDB families.

Thus scaling, features, folds, metric, k, target semantics and held-out family are identical. The sole counterfactual change is the source route allowed in the reference pool.

For year `y`:

- `M_mixed,y = d_nonpositive,mixed - d_positive,mixed`;
- `M_hdb,y = d_nonpositive,HDB-only - d_positive,HDB-only`;
- `Delta_y = M_hdb,y - M_mixed,y`.

Positive `Delta_y` means removing Sugar references improves that HDB family's annual local margin.

Every fold/year must have at least one HDB-only positive and one HDB-only nonpositive training reference or the diagnostic fails closed.

## Freeze before surfaced/missed status

Before authoritative #1046 is restored, freeze one complete 229-family HDB vector containing only:

- family ID and exact v31 fused rank;
- for 2013 and 2014 separately: mixed `d_positive`, mixed `d_nonpositive`, mixed margin, HDB-only `d_positive`, HDB-only `d_nonpositive`, HDB-only margin, and `Delta_y`;
- immutable route/fold provenance needed to reproduce those values.

The mixed annual-margin arrays must hash to exact v31 identities before the vector is accepted.

No #1046 shower label, surfaced/missed flag, recoverable-group identity, literature budget, oracle identity or annual candidate outcome may enter this frozen vector.

## Status source after freeze

Only after the complete counterfactual vector is frozen, restore authoritative #1046:

- run `31451236076`;
- artifact `9086399760`;
- artifact digest `sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69`;
- result SHA-256 `e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758`;
- verdict `PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC`;
- role `POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED`.

Use exactly #1046's already-frozen `first_recoverable_family_id_by_v31_fused_rank` for each annual candidate-recoverable shower group. Do not choose another representative.

Expected populations:

- 2013: 18 candidate-recoverable groups = 9 surfaced + 9 recoverable-but-missed;
- 2014: 19 candidate-recoverable groups = 9 surfaced + 10 recoverable-but-missed.

Any mismatch fails closed.

## Sole diagnostic statistic and gate

For each year separately, attach the frozen `Delta_y` of #1046's fixed first-recoverable family.

Compare only:

- median `Delta_y` among recoverable-but-missed groups;
- median `Delta_y` among v31-surfaced-recoverable groups.

PASS requires **both** strict conditions in **both** years:

1. missed-recoverable median `Delta_y > 0`;
2. missed-recoverable median `Delta_y` is strictly greater than surfaced-recoverable median `Delta_y`.

All four inequalities must pass. Empty strata fail closed.

No p-value, AUC, correlation, distance cutoff, route-count threshold, effect-size cutoff, top-k, rank window or second statistic is selected.

## Interpretation boundary

If PASS: conclude only that cross-route reference interference is a reproducible mechanism disproportionately suppressing missed HDB recoverables. A same-route-reference successor would still require a separate complete preregistration and one frozen route-general order before any panel result.

If FAIL: close the exact route-pool-interference mechanism. Do not rescue it by keeping Sugar positives but removing Sugar negatives, vice versa; route weights; route-specific scaling; per-year source rules; source quotas; reference-distance cutoffs; or outcome-conditioned source selection.

## Explicit non-search commitments

No:

- candidate order or score evaluated;
- literature panel evaluation of the HDB-only counterfactual;
- route weight/quota or partial source removal;
- separate positive/negative source rule;
- route-specific scaling;
- feature/metric/k/threshold/annual-combiner/diversity/fusion/model/component/topology search;
- alternate #1046 representative;
- budget/year/rank-window rule;
- oracle identity;
- successor selection;
- post-result second route-pool diagnostic.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
