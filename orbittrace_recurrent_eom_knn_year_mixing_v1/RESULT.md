# Recurrent-EOM local-kNN year-mixing v1 — binding result

## 🔴 NEGATIVE — scientific FAIL

The first technically valid target-excluded GMN 2022+2023 endpoint completed successfully in workflow run `31891899265` at frozen execution head `943d17d263be135b339b4a25b17867f01c5efd2e`.

Artifact: `9248792084`.
Artifact digest: `sha256:c27ca53a2bf639b444aacda1107b64acd59885a69805f5712725c9c9994ba82e`.
Binding prelabel SHA-256: `f65f22bb31111516eded8e4e0e80d59496f58ef76ad017663ce191b957397b64`.
Binding result SHA-256: `5ac9b5da6c059cf43b6eac7d9b2bd29221ac70e08ab56244825260218bdc7a93`.

Exact verdict:

`FAIL_RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT`

The method was genuinely active while preserving the exact 2,097 recurrent-EOM membership sets. The complete rank-order Spearman correlation with recurrent-EOM was `0.9990265783414136`; top-25 membership overlap was `24/25`, top-50 `50/50`, top-100 `99/100`, and top-500 `492/500`.

The local-mixing signal itself was nondegenerate across the fixed candidate population:

- enrichment minimum `0.0`;
- median `1.0`;
- mean `0.9656827652469699`;
- maximum `1.35`;
- median directed cross-year edge fraction `0.4666666666666667`;
- one-year candidates `30`;
- total directed within-candidate kNN edges `2,473,730`.

### 2022

Recurrent-EOM -> local-kNN mixing:

- recovered@25: `22 -> 22`;
- recovered@50: `45 -> 45`;
- recovered@100: `89 -> 89`;
- recovered@500: `193 -> 192` (reporting only);
- qualified matches: `236 -> 236`;
- top-100 dominant precision: `0.7856486012780942 -> 0.7844773501689549` — regression;
- MRR: `0.022498269587309373 -> 0.0225205620495306` — improvement;
- median top-500 fragmentation: `1.0 -> 1.0`.

### 2023

- recovered@25: `23 -> 23`;
- recovered@50: `46 -> 46`;
- recovered@100: `89 -> 89`;
- recovered@500: `192 -> 192`;
- qualified matches: `244 -> 244`;
- top-100 dominant precision: `0.7867680236864514 -> 0.7864944674554483` — regression;
- MRR: `0.0220239288966045 -> 0.0220352158991392` — improvement;
- median top-500 fragmentation: `1.0 -> 1.0`.

The frozen gate fails for two independent reasons: there is no strict recovered@100 improvement in either year, and top-100 dominant precision regresses in both years. The small MRR gains do not rescue those failures.

## Interpretation and closure

Graph-local annual intermixing contains some rank information, but multiplying recurrent stability by the raw fixed-count local-kNN mixing enrichment does not improve fixed-budget recovery and slightly reduces top-100 purity. This exact rank-only mechanism is permanently closed.

Per the pre-outcome protocol, do not rescue this result with another k, mutual-neighbor filtering, graph symmetrization, edge weights, transforms, caps, pseudocounts, exponents, additive blends, rank fusion, thresholds, or HDBSCAN changes.

Recurrent-EOM HDBSCAN v1 remains the parent/paper method. No SonotaCo benchmark is activated for this failed successor.

Protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo, AMOS, MAARSY and DMS remained inaccessible to this scientific selection.