# Frozen result — GMN v31 empirical class energy score v1

Binding scientific workflow run: `31670145186`

Binding job: `94352899881`

Execution head: `8476628f55244022c705c60269914abc8a5b8b24`

Frozen protocol commit: `29d2bb9643c43a794ddf69898556f9f40f9d5ca6`

Frozen implementation commit: `cb197b93fc66fc59ef67193d9f89fb9b3b6a52d6`

Verdict: **FAIL_GMN_V31_CLASS_ENERGY_SCORE_V1**

## Provenance and engineering gates

The first workflow execution was technically valid and binding. It passed:

- exact runtime/source compilation;
- exact ranker/evaluator source verification;
- analytic empirical energy-score self-tests (`PASS_CLASS_ENERGY_SCORE_ENGINEERING_SELF_TESTS`);
- authoritative offline-package verification (`PASS_AUTHORITATIVE_OFFLINE_PACKAGE_BEFORE_CLASS_ENERGY_SCORE`);
- exact 226x23 feature and 226x8 centroid hashes;
- exact five strict whole-shower OOF folds;
- exact parent raw Euclidean OOF margin reproduction at `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- exact v31 parent fused metric reproduction;
- all result/firewall assertions.

Artifact:

- ID: `9169387906`
- digest: `sha256:7bbe5496079dc18f953090570fad674a48cb2444481932afe02a9494d3ca7ea5`
- raw energy-margin SHA-256: `bace682d89c47ef7756c750eebb4a828dfc69b116b0226c572f2c1b0d12ed692`
- scaled energy-margin SHA-256: `9203268a8588aea175bf199f82d9a1f194ad879a4601ecac17d6afec86356595`

Frozen unit preservation:

- parent median absolute margin = `0.4460321881586118`
- fixed unit factor = `0.8553090216997754`
- therefore raw energy-score median absolute margin = approximately `0.5214866` (the exact value remains in the preserved result artifact; no alternate scaling is authorized).

## Binding candidate metrics

Exact v31 parent:

- recovered@25 = **23**
- recovered@50 = **41**
- recovered@100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified matches = **95**

Frozen empirical class-energy equal-rank-fused candidate:

- recovered@25 = **22**
- recovered@50 = **42**
- recovered@100 = **66**
- top-100 dominant precision = **0.7506878621129492**
- MRR = **0.0471404938260375**
- qualified matches = **95**

Diversified class-energy local-only diagnostic:

- recovered@25 = **21**
- recovered@50 = **43**
- recovered@100 = **63**
- MRR = **0.045128344465730344**
- qualified matches = **95**

## Binding promotion-gate result

Passed:

- recovered@50 not below v31: **42 >= 41**;
- top-100 dominant precision not below v31: **0.7506878621129492 > 0.7229521515453452**;
- qualified count identical: **95**.

Failed:

- recovered@100 must be strictly greater than 66: **66**, no improvement;
- recovered@25 must be at least 23: **22**;
- MRR must be at least `0.050244164168646674`: **0.0471404938260375**.

This is therefore a binding scientific **FAIL**. It does not authorize SonotaCo access.

## Scientific interpretation

The parameter-free empirical class-distribution score changed the ranking in a coherent but insufficient way. It produced substantially higher top-100 dominant precision and one additional recovery by rank 50, showing that full-class distribution compatibility can suppress some false-positive families more effectively than exact v31. However, it did **not** add a qualified label by rank 100, and it worsened both early @25 coverage and MRR.

The preregistered hypothesis was that distribution-level class support could rescue positive families for which no individually nearest positive prototype exists. Under the binding promotion criterion, that mechanism did not broaden top-100 recovery beyond v31. The purity increase cannot rescue the failed primary and preservation gates.

This result does not overturn the earlier GMN parent diagnostics: v31's residual top-100 misses are still a class-support/representation problem. It shows only that this exact **global empirical energy-score solution** is not sufficient under the frozen constraints.

## Closure

The exact empirical class-energy lane is permanently closed. Do not rescue it with:

- alternate distance exponents, squared distance or fractional powers;
- U-statistic or bias-corrected pairwise dispersion;
- class priors or class-size weighting;
- MMD kernels or bandwidth search;
- Wasserstein/optimal-transport class distances;
- energy-score thresholds or calibration;
- class subsets, archetypes, clusters or mixture decomposition derived from this result;
- blends with v31 nearest-reference margin or reverse-neighbour scores;
- reference weighting/deletion/relabeling;
- feature, metric, scaling, covariance, diversity or fusion changes informed by this outcome.

Any future successor must use a genuinely independent support/representation architecture and be frozen before its first technically valid outcome.

## Firewall

No SonotaCo 2013/2014 scientific outcome was accessed. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY and DMS remained inaccessible. No raw GMN event rows, event IDs or hidden event-label mapping were accessed by this offline successor.
