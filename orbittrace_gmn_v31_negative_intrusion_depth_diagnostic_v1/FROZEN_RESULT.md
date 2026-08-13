# Frozen result — GMN v31 negative-intrusion-depth diagnostic v1

Binding diagnostic workflow run: `31670457335`

Binding job: `94353798624`

Execution head: `2c100400069671ddfbb676d5c324cc7ee73a5ae9`

Frozen protocol commit: `f4aa049a6a85e90145309c0799e84407214d45e1`

Frozen implementation commit: `3b7bc563d49588d9e5ae0e78f4d7d9520bde390b`

Artifact:

- ID: `9169490828`
- digest: `sha256:7a27ebc776ddbdf6079d55bd90dbab59ae1f6e2b062c3c5a4d63878b0a8a5276`

Verdict: **PASS_GMN_V31_NEGATIVE_INTRUSION_DEPTH_DIAGNOSTIC_V1**

Predeclared top-100 constituent-absent outcome: **MULTIPLE_INTRUDERS_DOMINANT**

## Exact parent reproduction

The workflow passed the authoritative offline-package check and reproduced the exact v31 raw OOF margin SHA-256:

`f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

It also reproduced the frozen parent orders/metrics:

Hard:
- @25 = **21**
- @50 = **38**
- @100 = **59**
- top-100 dominant precision = **0.6884631112636006**
- MRR = **0.046734076055452344** within the workflow's fixed floating tolerance
- qualified labels = **95**

Exact fused v31:
- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646674** within the workflow's fixed floating tolerance
- qualified labels = **95**

No positive held-out family had an exact nearest-positive/nearest-nonpositive distance tie in this diagnostic (`distance_tie_positive_family_count = 0`).

## Binding top-100 intrusion-depth result

The previously frozen parent diagnostics were reproduced exactly before interpretation:

- fused top-100 misses = **29** qualified labels;
- no-positive-support subset = **25** labels;
- constituent-absent + sign-rejected subset = **21** labels.

For the exact **21 constituent-absent/sign-rejected labels**, using the minimum negative-intrusion count across each label's positive family representatives:

- `SINGLE_INTRUDER` (`min_I = 1`) = **4 / 21 = 19.0476%**;
- `MULTIPLE_INTRUDERS` (`min_I >= 2`) = **17 / 21 = 80.9524%**.

Exact complete histogram of `min_I`:

- 1: **4**
- 2: **8**
- 3: **1**
- 4: **1**
- 5: **2**
- 6: **1**
- 7: **1**
- 9: **1**
- 10: **1**
- 26: **1**

Five-number summary:

- min = **1**
- Q1 = **2**
- median = **2**
- Q3 = **5**
- max = **26**

This satisfies the preregistered `MULTIPLE_INTRUDERS_DOMINANT` definition.

## Broader top-100 context

For all **25** fused-missed labels with no positive-side v31 representative:

- single intruder = **5 / 25 = 20%**;
- multiple intruders = **20 / 25 = 80%**;
- median best intrusion count = **2**;
- Q1 = **2**;
- Q3 = **5**;
- max = **26**.

Exact histogram:

- 1: **5**
- 2: **8**
- 3: **1**
- 4: **2**
- 5: **3**
- 6: **2**
- 7: **1**
- 9: **1**
- 10: **1**
- 26: **1**

For all **29** fused top-100 misses:

- four labels have `min_I=0`, exactly matching the previously observed positive-support subset;
- five have `min_I=1`;
- twenty have `min_I>=2`;
- median `min_I=2`, Q1=1, Q3=5, max=26.

## Scientific interpretation

This diagnostic evaluates no new scientific score or rank. Its allowed conclusion is:

> The dominant v31 top-100 class-support failure is deeper than a single nearest-negative boundary intrusion. Even for the best positive representative of each of the exact 21 constituent-absent/sign-rejected qualified labels, **17/21** still have at least two nonpositive training references ahead of the nearest positive reference; the median best-case intrusion depth is two, and some labels are much more deeply embedded.

Combined with the two earlier frozen GMN parent diagnostics, the mechanism picture is now:

1. equal hard/local fusion is not the dominant bottleneck;
2. the hard top-100 misses do not merely have weak positive margins — all 21 constituent-absent labels have no positive-side v31 representative at all;
3. for 17 of those 21 labels, even the best representative is behind multiple nonpositive references, not just one.

Therefore another small boundary correction, nearest-pair calibration, fusion tweak, or single-reference reliability adjustment is poorly matched to the observed failure. The remaining problem is genuine overlap / insufficient positive-support representation in the frozen 23D family geometry.

This does not select a replacement representation or classifier. Existing closures remain binding, including global supervised metric learning, robust scaling, prototypes, segments/simplexes/hulls, neighbour-order rescue, reference editing, reverse-neighbour variants, empirical class-energy variants, calibration, diversity changes, and fusion changes.

## Governance

This diagnostic authorizes no intrusion-count classifier, threshold, penalty, reweighting, reference deletion, k search, density correction, class prior, representation subset, or rank change. It may not be used to tune a successor from the observed histogram.

Any future successor must be independently motivated as a genuinely different support/representation architecture, audited against the repository, and frozen before its first technically valid GMN result.

## Firewall

No SonotaCo 2013/2014 scientific data was accessed. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN events, raw event IDs, or hidden event-label mapping were accessed. No new scientific score or rank was evaluated and no successor was selected.
