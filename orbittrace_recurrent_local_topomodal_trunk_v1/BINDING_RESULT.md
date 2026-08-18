# Recurrent local TopoModal trunk v1 — binding GMN result

## 🔴 Binding verdict

`FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`

The first technically valid truth execution completed successfully in GitHub Actions run `32191925070` at execution head `94a65b82fb53585656640f246acde6b278b4a194`.

- pretruth artifact: `9344855777`, `orbittrace-recurrent-local-topomodal-trunk-v1-prelabel-exact-row`
- pretruth artifact digest: `sha256:d163bacb40709b9b6e7d15d870623308a6d5ccf2d4d62872e6162ac16ecaaa1b`
- sealed prelabel SHA-256: `a7b860704c7a688e4dd2a5dd1e38d9a03719b147bc373ee785d446e84a6ff380`
- binding result artifact: `9344977327`, `orbittrace-recurrent-local-topomodal-trunk-v1-binding-exact-row`
- binding result artifact digest: `sha256:4aab68fb99c76f077235696c7679f5129563ab3f76797913c5cc5af78320ccfd`
- binding result JSON SHA-256: `e0670b736cdbde0261693bd576f272599200b7656740c524cbac4eb5601f754d`
- frozen gates passed: **15 / 16**
- frozen catalogue slots changed: **305 / 2,094**

The pretruth stage completed and hash-sealed all 2,094 fixed-rank successor memberships before shower truth. The truth job then rebound the sealed pretruth and completed the unchanged 16-gate evaluator. No technical repair or rerun is authorized or needed.

## Exact annual outcomes

### 2022 — all seven annual gates PASS

Density-synchronous parent → local-trunk successor:

- full-catalogue qualified recovery: `236 → 242`
- recovered @25: `22 → 23`
- recovered @50: `45 → 47`
- recovered @100: `89 → 90`
- recovered @500: `192 → 196` *(reported, not a frozen promotion gate)*
- top-100 dominant precision: `0.7873334042799703 → 0.7922827253376370`
- reciprocal-rank mass: `5.3112680671961465 → 5.402517292930741`
- zero-filled eligible-query MRR: `0.01479461857157701 → 0.01504879468782936`
- median top-500 fragmentation: `1.0 → 1.0`

### 2023 — six of seven annual gates PASS

Density-synchronous parent → local-trunk successor:

- full-catalogue qualified recovery: `244 → 247`
- recovered @25: `23 → 23`
- recovered @50: `46 → 46`
- recovered @100: `90 → 90`
- recovered @500: `191 → 193` *(reported, not a frozen promotion gate)*
- top-100 dominant precision: **`0.7898245986099988 → 0.7898042123909221` — FAIL**
- reciprocal-rank mass: `5.375389517185777 → 5.382515334549499`
- zero-filled eligible-query MRR: `0.014686856604332724 → 0.01470632605068169`
- median top-500 fragmentation: `1.0 → 1.0`

The sole failed frozen gate is 2023 `top100_precision_not_lower`. The absolute precision change is approximately `-0.0000203862190767`. The gate was exact no-regression and is not relaxed because the other metrics improved.

Both global gates passed:

- representation mechanism active: PASS (`305` slots changed)
- strict zero-filled eligible-query MRR improvement in at least one year: PASS (in fact higher in both years)

Historical conditional MRR decreased because the successor recovered more showers and the denominator of that conditional statistic increased; it was explicitly diagnostic only. The binding retrieval statistic was the predeclared zero-filled eligible-query MRR, which improved in both years.

## Scientific interpretation and closure

The result is a scientifically useful near-miss, not a promotion. Local topological erosion materially improved recovery and zero-filled retrieval while preserving fragmentation, but the exact frozen rule introduced a tiny top-100 precision regression in 2023. Because all 16 gates were mandatory, the method fails.

The exact `largest strict dominant-mode trunk` rule is permanently closed under the frozen protocol. Do not rescue it after outcome by changing the local radius, physical scales, annual support floor, anchor definition, hierarchy rule, retained trunk depth, parent subset, rank handling, precision gate, retrieval metric, or any result-informed selector.

The conditional local-trunk matched-capacity literature audit and conditional local-trunk AMOS endpoint were frozen before this outcome but require exact `PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`; they therefore close without scientific execution.

Protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed by this binding experiment. No post-result parameter search was performed.
