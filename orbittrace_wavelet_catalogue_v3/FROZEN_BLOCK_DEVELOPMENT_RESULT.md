# Frozen OrbitTrace wavelet catalogue v3 block-runtime development result

Authoritative workflow run: `31184978022`

Authoritative job: `92887138450`

Authoritative artifact: `orbittrace-wavelet-catalogue-v3-block-development` (`8997946355`)

Artifact digest: `sha256:3b9107d9d1abff190660e23e824cb63c80d6dbde478c658a81960b90e94da18f`

Evaluated execution commit: `08566a75d0506b9f8a417c398921e319f9731402`

Frozen scientific source SHA-256: `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`

Verdict: **`FAIL_WAVELET_CATALOGUE_V3_DEVELOPMENT`**

## Authoritative development metrics

- development years: **2022, 2023** only;
- eligible known-shower labels: **355**;
- exact retained anchors: **67,584**;
- single-year components: **132**;
- recurrent wavelet families: **23**;
- fixed4 rescue-only recurrent families: **0**;
- recovered known showers at top 100: **14** (frozen fixed4 baseline **61**);
- recovered known showers at top 500: **14** (fixed4 **90**);
- qualified known-shower matches: **14** (fixed4 **90**);
- MRR: **0.21374845392702532** (fixed4 **0.04768980412577584**);
- median rank: **8.5** (fixed4 **61.0**);
- macro F1: **0.6879019101665687** (fixed4 **0.1671102524400389**);
- top-100 dominant precision: **0.6240219257620858** (fixed4 **0.6809376504699393**).

## Gates

Passed:

- wavelet parameters frozen;
- blind interval removed before label normalization;
- exact development years;
- at least 30 supported calibration bins/year;
- top-100 dominant precision >= 0.50.

Failed:

- at least 50 wavelet families (**23** observed);
- top-100 recovery >= 80% of fixed4 (**14** vs required >= **48.8**);
- qualified matches >= 60% of fixed4 (**14** vs required >= **54**).

The block runtime itself passed its independent equivalence freeze before this run. Therefore this is a **scientific catalogue-architecture failure**, not a runtime/infrastructure failure.

No 2024–2026 catalogue and no OrbitTrace target interval were opened. This result does not authorize held-out catalogue access. Any successor must be separately named and developed from the now-exposed 2022–2023 development artifact.

Key output hashes from the authoritative artifact:

- `wavelet_catalogue_v3_development.json`: `8ce6cc9fc7144bfce4d1df66f482aff3265838a395a066da332728387861079a`
- `wavelet_catalogue_v3_families.json.gz`: `f694582637eb8b9e4fd21a99825e258a419efe99d0a522c9c99efca153daf95c`
- `wavelet_catalogue_v3_anchors.jsonl.gz`: `f953f853cd3a74337cd1b9260354725206d1eec7afffc731ca93a818ec066b3f`
- `WAVELET_CATALOGUE_V3_DEVELOPMENT.md`: `3fd777902d420e984675b2a011f62b276a8971be881de46806f2991388adb7d0`
