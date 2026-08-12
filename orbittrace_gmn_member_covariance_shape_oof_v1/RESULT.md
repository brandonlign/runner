# OrbitTrace GMN member-covariance shape OOF v1 — binding result

Verdict: **`FAIL_GMN_MEMBER_COVARIANCE_SHAPE_OOF_V1`**.

## Binding provenance

- protocol frozen before implementation/outcome: commit `80aa52cde942eeb0909fbb7cf8a234c002e4f20f`, Git blob `a3d9c3aac54480ea2fb6654e1873b602ac26f60b`;
- original implementation commit: `83f8d535f47b4c80d775015d4624b2e0313571d3`;
- first execution `31623987180`: **technical no-result** because a non-scientific bitwise parent-feature SHA guard rejected the hosted-runner floating array before any 40D candidate result was produced;
- technical-only guard repair: `f32303e69bc1e0fba29deff6eddcb9d33c413eff`; scientific feature definitions, target, model, folds, weights, diversity, evaluation, and binding gates were unchanged;
- repaired workflow pin commit / binding execution commit: `efae097b8c09909f7e5df34f28d5d0d973da7c23`;
- first technically valid scientific run: `31624453260`;
- artifact ID: `9152655794`;
- artifact digest: `sha256:b5ab51fd1bd82717734586457021aaee6463e90fcf74b5d072146e8d437442f6`.

All immutable inputs, exact #1194 source, target vector, grouped weights, parent OOF metrics/order, firewall assertions, schema checks, and artifact upload passed. The first run never reached candidate evaluation and is not a scientific outcome. Run `31624453260` is therefore the binding first valid outcome.

## Exact comparison

| metric | #1194 parent | 40D member-covariance candidate |
|---|---:|---:|
| recovered @25 | 22 | 21 |
| recovered @50 | 43 | 43 |
| recovered @100 | 80 | 80 |
| recovered @500 | 171 | 171 |
| top-100 dominant precision | 0.8075287489258385 | 0.8022763400443974 |
| MRR | 0.02016666446026534 | 0.01971516214819495 |
| qualified matches | 256 | 256 |

Candidate OOF order SHA-256: `5a4edf5fb177b512d422e2fcd57b58da271e0448aef60ee2eb03b75915044e9e`.

Frozen six-feature block SHA-256: `bdcda42d40fdc5182737301d3ae66f2b9a688c90a1fa8539ea23e75afcda9746`.

40D candidate feature SHA-256 on the binding runner: `af33e3dadb858c65827214446542bad786aa6a5aaeed93bdb5b98e4f88b3f9fa`.

## Binding gates

PASS:

- recovered@50 >= 43;
- recovered@500 >= 171;
- qualified matches == 256.

FAIL:

- recovered@100 > 80;
- recovered@25 >= 22;
- top-100 precision >= parent;
- MRR >= parent.

## Scientific interpretation

The joint second-order shape of the within-family member cloud, summarized by the preregistered scatter/anisotropy/spectral-entropy/year-balance/covariance-alignment/drift-to-scatter block, changed the strict-OOF ordering but did **not** recover any additional shower at top 100. It slightly degraded the earliest budget, top-100 precision, and MRR.

Therefore the #1194 80/100 gap is not resolved by this fixed low-order covariance-shape augmentation. The representative-share oracle result remains the key positive diagnostic: the exact target/diversity combination can reach 100/100 if predicted perfectly, so representation separability remains the broader bottleneck even though this particular second-order representation failed.

## Closure

This exact member-covariance-shape augmentation is permanently closed. Do **not** rescue it with alternate physical scales, centering, covariance estimators, shrinkage, robust covariance, `ddof`, epsilon, eigenvalue handling, feature subsets/transforms, per-source variants, estimator changes, ExtraTrees retuning, target/weight/fold/diversity changes, or parent blending.

A genuinely different higher-order or learned family representation may be considered only under a separately motivated and frozen protocol. No SonotaCo-guided successor design and no protected-target application is authorized by this result.
