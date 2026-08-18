# Recurrent-EOM direct GMN literature benchmark v1 — binding result

## Verdict

`PASS_RECURRENT_EOM_GMN_LITERATURE_4_OF_4`

Binding workflow run: `32152924956`

Binding artifact: `9330778578` (`orbittrace-recurrent-eom-gmn-literature-direct-v1-binding`)

Artifact digest: `sha256:b25c4eb22b7c3810b3b79828a2b53862dab949b00bf4b431b57238abb2fb9cd1`

Sealed pretruth artifact: `9330668301`

Pretruth artifact digest: `sha256:fe73592d766cab1a38eeb146813f33c327b1144e0849b9381238f8c91057c2c7`

Pretruth JSON SHA-256: `f52371ba1a302d57a4050b380c2a744a3be560fee0916b28ba10efbdf20e8351`

Result JSON SHA-256: `20dd97323813f168da57383fe27dbd9685e68ddacd9b2ca1b9b31040c1cf1c4c`

Activation SHA: `1625859affdcca35b03a9750ba5de21d81872223`. The workflow explicitly checked out the branch and therefore recorded checkout SHA `74089b9cfe101f89a788c9c3eaa8d7aa9f8cb06e` after a read-only observer-workflow commit; the frozen protocol, comparator builder, truth evaluator, activation marker, and scientific inputs were unchanged between those SHAs.

The initial run `32152452771` was a technical no-result before geometry/pretruth/truth because the frozen `wavelet_episode_comparator.py` directory was missing from `PYTHONPATH`. The retry changed only that import path and pinned the comparator blob `493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8`.

## Common target-excluded GMN comparison

All methods were evaluated on the same GMN 2022/2023 accessible event universe with inclusive solar longitude `[20,55]` excluded before method construction. Literature catalogues were SHA-sealed before known-shower truth was opened. Eligible showers required at least four accessible annual members; comparison used maximum-F1 Hungarian one-to-one assignment.

### 2022

- Recurrent-EOM: macro-F1 `0.45881483985272825`; recovered F1>0.5 `170`.
- Sugar 2017 portable central-value DBSCAN core: macro-F1 `0.15607673680944167`; recovered F1>0.5 `51`.
- Peña-Asensio & Ferrari 2025 GEO HDBSCAN/EOM/100: macro-F1 `0.11783144148783989`; recovered F1>0.5 `43`.

Both pair gates PASS.

### 2023

- Recurrent-EOM: macro-F1 `0.46935685954079237`; recovered F1>0.5 `178`.
- Sugar 2017 portable central-value DBSCAN core: macro-F1 `0.18674791207442026`; recovered F1>0.5 `59`.
- Peña-Asensio & Ferrari 2025 GEO HDBSCAN/EOM/100: macro-F1 `0.13235618973750005`; recovered F1>0.5 `57`.

Both pair gates PASS.

## Interpretation

Recurrent-EOM passes all four preregistered GMN year-by-literature pair gates, with large margins in both macro-F1 and recovered-showers count. This is independent confirmation, on the main target-excluded GMN development universe, of the direction already seen in the exposed SonotaCo matched-literature benchmark.

This benchmark does not define a head-to-head MRR because the published comparator catalogues are unordered. It also does not reproduce Sugar et al.'s full 1000-resample uncertainty-retained master procedure; the Sugar comparator is explicitly the portable deterministic central-value DBSCAN core frozen in the protocol. Therefore the supported claim is superiority to these two frozen published clustering baselines under the common GMN evaluation, not superiority to every possible literature implementation.

Protected OrbitTrace target information/events and AMOS, MAARSY, DMS, ASFN/EFN event-level data were not accessed.