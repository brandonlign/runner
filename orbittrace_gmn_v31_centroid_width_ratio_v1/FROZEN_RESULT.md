# OrbitTrace GMN v31 centroid-width ratio v1 — binding result

## Verdict

🔴 `FAIL_GMN_V31_CENTROID_WIDTH_RATIO_V1`

The first technically valid outcome failed exactly one preregistered promotion gate: recovered@100 did not strictly exceed the v31 parent. This successor is permanently closed and does not authorize SonotaCo access.

## Frozen provenance

- pre-outcome protocol commit: `0f426dd9a22e5fb5f81f5213215b9c8016fabce7`
- authoritative offline package artifact: `9167087908`
- exact parent feature SHA-256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- exact parent margin SHA-256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- local frozen-evaluator script SHA-256: `624e3a1b6162d3d1bba32156f8c0a8b69a45a1d5489bd247da284b265a0a72c9`
- binding result JSON SHA-256: `31af9a496baa4da9f515d8a3afe80e84004e92733516b69e86c0d7ac3b9a69fa`
- added ratio vector SHA-256: `e22771dc0ffcf5e7e02f0f577e2acacc47cb3e7f77ed36eccacfa546445270c6`
- candidate 24D matrix SHA-256: `9a75fed2b6da2dc50d2888ca8d4f69de3fc65844937a1b5088c499caf9015f62`
- candidate OOF margin SHA-256: `98f5f4fa6c2e824af014ab099a35b04a493ae9b86411626a87ce9d34d860daa6`
- candidate local order SHA-256: `7abc67cd56e7c862ed5788a7b285fa9e28282861533f8befe66ae9a03a85a192`
- candidate fused order SHA-256: `fdbf50bc449829cfa08b7d57d3b02487a8bf0ed0e49947e7d4dbe73fbd2b7d16`

The evaluator first reproduced the exact v31 23D matrix and exact parent margin hash, then reproduced the hard and fused parent controls before evaluating the sole appended coordinate.

## Sole frozen coordinate

`centroid_width_ratio = X[:,9] / X[:,16]`

where exact v31 coordinate 9 is `centroid_crossyear_distance` and coordinate 16 is `year_q90_distance_max`. All 226 denominators were finite and strictly positive in the pre-outcome label-free feasibility check, so no epsilon/fallback/filter was used.

Ratio distribution (descriptive provenance only): min `0.027089801121311596`, median `0.442726330088645`, max `3.192249177662037`.

## Binding metrics

Exact v31 fused parent:
- recovered@25: `23`
- recovered@50: `41`
- recovered@100: `66`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674` (floating reproduction differed only at machine-roundoff scale in the local metric calculation)
- qualified matches: `95`

Centroid-width ratio candidate:
- recovered@25: **`23`** — preserved
- recovered@50: **`42`** — improved by 1
- recovered@100: **`66`** — unchanged, therefore FAIL
- top-100 dominant precision: **`0.7244872392646434`** — improved
- MRR: **`0.05026875409070269`** — improved
- qualified matches: **`95`** — preserved

Gate status:
- @100 strictly better: **FAIL**
- @25 not worse: PASS
- @50 not worse: PASS
- top-100 precision not worse: PASS
- MRR not worse: PASS
- qualified count identical: PASS

The candidate moved the ranking in a mildly favorable direction but did not create the required additional recovered label inside the top 100. Under the frozen all-gates rule this is a scientific failure, not a near-pass eligible for rescue.

## Closure

Do not retry inverse/log/sqrt/square/rank/percentile transforms, alternate width denominators, additive/difference/product variants of the same coordinates, per-axis displacement, fitted drift, activity displacement, thresholds, weights, feature subsets, metric/k/scaling/diversity/fusion changes, rank windows, or blends with other successors. The complete no-rescue list in `PROTOCOL.md` remains binding.

No SonotaCo benchmark is authorized by this result.

## Firewall

The binding calculation used only the frozen offline 226-family package. It accessed no raw event rows and records:
- SonotaCo 2013/2014 access: false
- protected target-region event access: false
- OrbitTrace target information access: false
- MAARSY scientific access: false
- DMS scientific access: false
