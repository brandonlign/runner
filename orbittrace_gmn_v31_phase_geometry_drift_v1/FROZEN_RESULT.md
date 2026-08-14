# Frozen result — GMN v31 phase–geometry drift recurrence v1

Binding run: `31762537747`  
Binding job: `94651733827`  
Execution head: `8f79796e3a2c060e729461ad8f45cbc20214cbf1`  
Artifact: `9205181114`  
Artifact digest: `sha256:46e8d63a1204eaa67b39ea206479c9bd0f6f07975696507a7bbc75f84d148823`

Frozen protocol commit: `910469ccd7b12e297f90e530fd7441b409786c11`  
Frozen protocol blob: `bbc10eccc2374f16fb069dca662f7abefb2c25f9`  
Frozen implementation commit: `7095b8451bd1a235564448443acfedabbe096b59`  
Frozen implementation blob: `d741f53ad5104e5d2cba51cadc4f88bc02a4d3af`

Verdict: **FAIL_GMN_V31_PHASE_GEOMETRY_DRIFT_V1**

All preregistered source, runtime, immutable-artifact, exact 23D reconstruction, centroid, fold, parent-margin, evaluator, and firewall checks passed. The first technically valid outcome is binding.

Exact v31 parent:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified = **95**

Frozen 24D phase–geometry drift fusion:

- @25 = **23**
- @50 = **41**
- @100 = **63**
- top-100 precision = **0.6991286221335805**
- MRR = **0.05005374761055788**
- qualified = **95**

Frozen local-only phase–geometry drift order:

- @25 = **22**
- @50 = **39**
- @100 = **60**
- top-100 precision = **0.6095251184668391**
- MRR = **0.03506405618036279**
- qualified = **95**

Gate result:

- @100 >66: **FAIL** (63)
- @50 >=41: **PASS** (41)
- @25 >=23: **PASS** (23)
- precision >= parent: **FAIL**
- MRR >= parent: **FAIL**
- qualified =95: **PASS**

This is a binding scientific failure and does **not** authorize SonotaCo access.

Frozen hashes:

- phase–geometry drift vector: `8488616bd11c84faa4855c6550749d7ec27b5ea43c8b24f0debaf083654d157f`
- candidate raw margin: `28b699980a75bb3bb8cb4d866bab2716d278d2f1685c395044fb4ee11a1d8646`
- candidate fused order: `1ff6d3f5b521c14673d4f81f290efcad484f8ba482e4bf51d58ce506b2ac5c18`

Feature distribution (provenance only):

- all families: min `0.030971197294662255`, median `0.7691933780975893`, max `7.853551849021535`
- positive families: min `0.030971197294662255`, median `0.6473391618606762`, max `7.853551849021535`
- nonpositive families: min `0.08672507736032535`, median `0.8539906660312928`, max `2.9949433524412825`

Scientific interpretation: positive families showed a somewhat smaller median annual drift discrepancy than nonpositive families, but appending the frozen scalar to exact v31 did not improve the preregistered ranking objective. It retained the short-depth gates while degrading @100, precision, and MRR. The method is therefore rejected rather than adjusted.

Permanent closure: do not rescue this outcome using axis-specific slopes, slope angles/cosines, magnitude ratios, intercepts, robust/ridge/shrinkage regression, phase clipping/windows, minimum-span thresholds, event or uncertainty weights, nonlinear/polynomial drift, alternate normalizations, sign flips, transforms, feature weights/subsets, metric/k/scaling/reference changes, or diversity/fusion changes selected from this result.

Protected solar longitude 20°–55° remained inaccessible. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, or DMS was accessed.