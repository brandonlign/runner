# Frozen result — GMN v31 reverse-1NN slack local geometry v1

Binding scientific workflow run: `31669771949`

Binding job: `94351805812`

Binding execution head: `1838a211ac89c6cc3e2b2a4c7d4883fcf1f2a355`

Frozen scientific protocol commit: `f672e3062b59889d2ef3193812f6355c221b8b3e`

Initial implementation commit: `ffb1a9eb8c938e02a6398795c77395884c675a8a`

Pre-science engineering-only fixture repair: `1838a211ac89c6cc3e2b2a4c7d4883fcf1f2a355`

Verdict: **FAIL_GMN_V31_REVERSE1NN_SLACK_V1**

## Pre-science engineering history

The initial workflow run `31669662370` failed at the synthetic analytic self-test before the authoritative GMN package was downloaded and before any scientific score was computed. The fixture comment intended to test a sparse reference beating a closer dense reference under reverse-1NN slack, but its coordinates made the sparse reference itself closer. This was a hand-constructed unit-test error, not a scientific outcome.

The sole repair changed the synthetic fixture from `[0,2,10], z=7` to `[0,1,10], z=5`, yielding exact label-blind training radii `[1,1,9]`, query slacks `[-4,-3,4]`, and the intended condition that the dense reference is closer in ordinary distance while the sparse reference has larger reverse slack. The frozen scientific formula, package, representation, folds, score, unit preservation, diversity, fusion, evaluator, and promotion gate were unchanged.

Run `31669771949` then passed:

- exact runtime/source compilation;
- exact ranker/evaluator source hash;
- corrected analytic reverse-1NN engineering self-test (`PASS_REVERSE1NN_SLACK_ENGINEERING_SELF_TESTS`);
- authoritative offline package digest/hash/shape/firewall checks (`PASS_AUTHORITATIVE_OFFLINE_PACKAGE_BEFORE_REVERSE1NN_SLACK`);
- exact parent raw OOF margin reproduction;
- exact v31 parent fused metric reproduction;
- all result/firewall enforcement checks.

Therefore `31669771949` is the first technically valid scientific execution and its outcome is binding.

## Artifact

- artifact ID: `9169262085`
- digest: `sha256:f1fcb47b4e03f828f5a47445a0da032d6f1aedbf74d36085d8506a89244c0a33`
- raw reverse-margin SHA-256: `7cd972465127714a45b3f48ffdbc09a637fc799af22e8b26aa25ce455b9fcf2b`
- scaled reverse-margin SHA-256: `5c6cb4c7dece59d4381785ba9719852e766054390406e396c3d900ffa309515e`

Frozen unit preservation:

- parent median absolute margin = `0.4460321881586118`
- reverse median absolute margin = `0.48531834079672265`
- unit factor = `0.9190507563064343`

## Binding candidate metrics

Exact v31 parent:

- recovered@25 = **23**
- recovered@50 = **41**
- recovered@100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified matches = **95**

Frozen reverse-1NN-slack equal-rank-fused candidate:

- recovered@25 = **25**
- recovered@50 = **44**
- recovered@100 = **65**
- top-100 dominant precision = **0.7163120164846726**
- MRR = **0.05113140129019792**
- qualified matches = **95**

Frozen reverse-1NN diversified local-only diagnostic:

- recovered@25 = **23**
- recovered@50 = **41**
- recovered@100 = **63**
- top-100 dominant precision = **0.6572453025430682**
- MRR = **0.0399865753848719**
- qualified matches = **95**

## Binding promotion-gate result

Passed:

- recovered@25 not below v31: **25 >= 23**;
- recovered@50 not below v31: **44 >= 41**;
- MRR not below v31: **0.05113140129019792 >= 0.050244164168646674**;
- qualified count identical: **95**.

Failed:

- recovered@100 must be strictly greater than 66: **65**;
- top-100 dominant precision must be at least 0.7229521515453452: **0.7163120164846726**.

Because every frozen gate is binding, the method is a scientific **FAIL** despite the real early-budget and MRR improvements. It does not authorize SonotaCo access.

## Scientific interpretation

The parameter-free reverse-neighbour support architecture produced a meaningful redistribution of ranking strength: relative to exact v31 fusion, it recovered **+2** labels by rank 25, **+3** by rank 50, and increased MRR, while losing **1** label by rank 100 and slightly reducing top-100 dominant precision.

This is evidence that label-blind local support radii can alter the v31 failure geometry in a useful way at early ranks. However, the preregistered primary criterion is broader top-100 recovery with no degradation in precision/MRR/early budgets. The method did not satisfy that criterion and therefore cannot be promoted or transferred to exposed SonotaCo.

The result must not be used to search a radius multiplier, reverse-neighbour order, same-class radius, clipped penetration, count score, slack aggregation, blend, or fusion change.

## Closure

The exact reverse-1NN-slack lane is permanently closed. In particular, do not rescue it with:

- reverse `k>1`;
- same-class or opposite-class nearest-neighbour radii;
- any radius multiplier, shrinkage, floor, exponent, or threshold;
- reverse-neighbour count scores;
- count/slack blends;
- clipped/positive-part penetration scores;
- sum/mean/median/kernel aggregation over reverse supports;
- parent-margin/reverse-margin blends;
- result-informed reference deletion, relabeling, pruning, or weighting;
- metric, feature, scaling, class-calibration, diversity, or fusion changes derived from this outcome.

Any future successor must use a genuinely independent class-support/representation mechanism, survive the repository duplicate/governance audit, and be frozen before first valid outcome.

## Firewall

No SonotaCo 2013/2014 scientific outcome was accessed for this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN event rows, raw event IDs, or raw hidden-label event mapping were accessed by this offline successor.
