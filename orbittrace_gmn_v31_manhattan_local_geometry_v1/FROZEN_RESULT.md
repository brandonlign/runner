# Frozen result — GMN v31 Manhattan local geometry v1

Binding workflow run: `31667901629`

Execution head: `0dd32748df465e7d046854d1d6bcdc5aead0d059`

Frozen protocol commit: `12d204f46ef57fb175c059b19a1b3fe84c72154b`

Frozen implementation commit: `f846ddce62055f4ed5e7b0a9f5aa31f1bb10f3cd`

Verdict: **FAIL_GMN_V31_MANHATTAN_LOCAL_GEOMETRY_V1**

## Provenance and engineering gates

All pre-science gates passed:

- analytic Manhattan engineering self-tests passed;
- exact diversity/evaluator source hash passed;
- authoritative offline-package manifest hash passed;
- 226x23 feature matrix and 226x8 centroid matrix hashes passed;
- parent raw Euclidean OOF margin reproduced exactly at `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- exact v31 parent metrics reproduced;
- all firewall assertions passed.

Artifact:

- ID: `9168619318`
- digest: `sha256:f4f4ebe54f4cfaf127c03737bb9d78a0877202a95484da1a7493604722869699`

## Binding candidate metrics

Exact v31 parent:

- recovered@25 = **23**
- recovered@50 = **41**
- recovered@100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified matches = **95**

Frozen Manhattan equal-rank-fused candidate:

- recovered@25 = **24**
- recovered@50 = **40**
- recovered@100 = **63**
- top-100 dominant precision = **0.7084596100311319**
- MRR = **0.05034362656980003**
- qualified matches = **95**

Local-only Manhattan diagnostic:

- recovered@25 = **23**
- recovered@50 = **42**
- recovered@100 = **59**
- top-100 dominant precision = **0.6153179820528062**
- MRR = **0.0484555838881013**
- qualified matches = **95**

Metric-unit preservation was applied exactly as frozen:

- parent median absolute Euclidean margin = `0.4460321881586118`
- raw Manhattan median absolute margin = `1.3957999255604507`
- fixed unit factor = `0.3195530963934663`
- raw Manhattan margin SHA-256 = `a68593b51f5d4afad7857a8285d2c841ec081b48e334ec3b625641637483c35c`
- scaled Manhattan margin SHA-256 = `1ee2a34d159ce7a2f5e5351085ff5784462d82e4b24f58e1f98c2d1fd5ecdcbd`

## Binding gate result

Passed:

- recovered@25 not below parent;
- MRR not below parent;
- qualified count identical.

Failed:

- recovered@100 must be >66: **63**;
- recovered@50 must be >=41: **40**;
- top-100 precision must be >=0.7229521515453452: **0.7084596100311319**.

This is a binding scientific failure. It does not authorize SonotaCo access for this successor.

## Closure

The exact Manhattan mechanism is permanently closed. Do not rescue it with:

- fractional `p` or any `p` search;
- `L_infinity`;
- weighted Manhattan distance;
- L1/L2 blends;
- alternate unit normalization;
- robust/MAD scaling;
- feature subsets or block norms;
- k-neighbor variants;
- threshold/calibration variants;
- result-informed diversity or fusion changes.

The limited @25/MRR improvements are diagnostic only and do not override the frozen primary promotion gate.

## Firewall

No SonotaCo 2013/2014 scientific outcome was accessed. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN event rows, raw event IDs, or raw hidden-label event mapping were accessed by this offline successor.
