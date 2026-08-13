# Frozen result — GMN v31 margin-sign bottleneck diagnostic v1

Binding diagnostic run: `31669297064`

Binding job: `94350445150`

Execution head: `1613763fd89f9b9bf1346e4535f797e28cd1a97a`

Frozen protocol commit: `fd3abbf6cb4d655b796c63ac7a8d103e6262b5e5`

Frozen implementation commit: `3f5580f8f8bcd4d22395f00f9e765e7954d10657`

Artifact:

- ID: `9169106224`
- digest: `sha256:adbd484032096dd20841a22be2d2a1e89477a7a165ab1020c6c3bd5ca586a8a6`

Verdict: **PASS_GMN_V31_MARGIN_SIGN_BOTTLENECK_DIAGNOSTIC_V1**

Predeclared top-100 constituent-absent outcome: **SIGN_REJECTION_DOMINANT**

## Exact parent controls reproduced

Hard order:

- @25 = **21**
- @50 = **38**
- @100 = **59**
- top-100 dominant precision = **0.6884631112636006**
- MRR = **0.04673407605545236**
- qualified labels = **95**

Diversified v31 local order:

- @25 = **21**
- @50 = **39**
- @100 = **63**
- top-100 dominant precision = **0.6204548749848309**
- MRR = **0.03662109750246032**
- qualified labels = **95**

Exact fused v31:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646695**
- qualified labels = **95**

The complete recomputed raw v31 margin vector reproduced the frozen SHA-256 exactly:

`f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

## Binding top-100 result

The exact fused v31 order misses **29** of the 95 qualified labels at top 100.

Using only the parent raw local margin `d_nonpositive - d_positive` and its natural zero boundary:

- `ALL_NONPOSITIVE`: **25 / 29 = 86.2069%**;
- `ALL_POSITIVE`: **4 / 29 = 13.7931%**;
- `MIXED`: **0 / 29 = 0%**.

Therefore:

- any positive-side representative = **4 / 29 = 13.7931%**;
- no positive-side representative = **25 / 29 = 86.2069%**.

For the 29 fused misses, the best representative raw-margin distribution is itself negative:

- median maximum margin = **−0.48184349143520033**;
- 25th percentile maximum margin = **−0.6486126944054629**;
- 75th percentile maximum margin = **−0.16811915871841343**.

The diversified local constituent places only **4** of the 29 misses inside the top 100, and those four are exactly the four labels with positive-side raw support:

- local inside 100 + any positive support = **4**;
- local inside 100 + no positive support = **0**;
- local outside 100 + any positive support = **0**;
- local outside 100 + no positive support = **25**.

## Strongest predeclared cross-diagnostic result

The previous frozen constituent-bottleneck diagnostic identified **21** of the 29 top-100 fused misses as `CONSTITUENT_ABSENT`: neither hard nor diversified-local constituent places the label inside the top 100.

This diagnostic reproduced that exact `21` count before interpretation.

Among those **21 constituent-absent labels**:

- `ALL_NONPOSITIVE` = **21**;
- `ALL_POSITIVE` = **0**;
- `MIXED` = **0**;
- any positive-side representative = **0 / 21 = 0%**;
- no positive-side representative = **21 / 21 = 100%**.

That is the binding `SIGN_REJECTION_DOMINANT` outcome.

## Lower-budget context fixed by protocol

At top 50, fused v31 misses 54 qualified labels:

- no positive-side representative = **32 / 54 = 59.2593%**;
- any positive-side representative = **22 / 54 = 40.7407%**;
- median maximum margin = **−0.14341038150368657**.

At top 25, fused v31 misses 72 qualified labels:

- no positive-side representative = **33 / 72 = 45.8333%**;
- any positive-side representative = **39 / 72 = 54.1667%**;
- median maximum margin = **+0.07253392412210324**.

## Scientific interpretation

This diagnostic does not evaluate any new rank or successor. Its allowed conclusion is:

> The dominant unresolved top-100 failure is not that equal fusion suppresses a basically correct local signal, and not merely that positive-side v31 evidence is ranked too weakly. For every one of the 21 labels that is absent from both frozen top-100 constituents, every positive representative lies on the nonpositive side of v31's own nearest-positive-versus-nearest-nonpositive boundary. Across all 29 top-100 misses, 25 labels have no positive-side representative at all.

Therefore the main remaining mechanism problem is **positive-class support / representation generalization**. A future method that merely recalibrates, reweights, or refines the existing scalar v31 margin is poorly aligned with the observed failure mode; the hard misses require the underlying class-support geometry or representation to change enough that genuinely positive held-out families are no longer systematically closer to nonpositive references.

This does **not** authorize a specific representation, interpolation, metric, prototype, k, density, calibration, or global classifier. Existing closures remain binding, including failed group prototypes, nearest-feature segments, multi-neighbour support, robust scaling, Mahalanobis/LFDA/global metric directions, positive-support/one-class scoring, reference editing, and exact-NPC fallback restrictions.

## Governance

No successor was selected by this diagnostic. In particular, do not use these results to tune:

- a nonzero margin threshold;
- class-distance calibration;
- hard/local fusion weights;
- diversity strength;
- k or neighbour aggregation;
- positive/reference editing;
- segment/simplex/hull rescue variants;
- global supervised metric weights;
- feature subsets or block weights.

Any future successor must be motivated independently as a genuine class-support/representation architecture, audited against the closed repository, and frozen before first valid GMN outcome.

## Firewall

No SonotaCo 2013/2014 scientific data was accessed. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN events, raw event IDs, or hidden event-label mapping were accessed. No new score or scientific rank was evaluated and no successor was selected.
