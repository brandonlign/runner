# HDBSCAN catalogue-track evaluation

## Frozen literature implementation

This track applies the Peña-Asensio–Ferrari (2025) catalogue configuration separately from the 128-event sparse-episode benchmark:

- unstandardized six-component GEO vector;
- `hdbscan==0.8.44`;
- Euclidean metric;
- `min_cluster_size=100`;
- package-default `min_samples`;
- `eom` cluster selection;
- published quality filters;
- no parameter selection from either result.

## Results

| Corpus | Events | Reference showers ≥100 | Clusters | Noise fraction | NMI | ARI | F1 > .5 | F1 > .8 | Mean F1 | Median F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SonotaCo 2025 | 18,939 | 13 | 11 | 0.622208 | 0.747578 | 0.763809 | 11/13 | 6/13 | 0.704556 | 0.794074 |
| SonotaCo 2023 one-shot | 26,332 | 17 | 15 | 0.583397 | 0.737825 | 0.735615 | 13/17 | 9/17 | 0.632686 | 0.829599 |

The independent transfer closely reproduced the development-corpus catalogue metrics without changing a parameter.

## Frozen size boundary

All-shower coverage audits used identical HDBSCAN parameters and were not relabelled as faithful reproductions of the paper's ≥100-member reference analysis.

| Reference size | 2025 mean F1 | 2023 mean F1 |
|---|---:|---:|
| 4–9 | 0.000000 | 0.000000 |
| 10–24 | 0.000000 | 0.002438 |
| 25–49 | 0.030769 | 0.000000 |
| 50–99 | 0.267677 | 0.159130 |
| 100+ | 0.707397 | 0.626944 |

## Independent judgment

The published HDBSCAN configuration is reproducibly effective for large catalogue populations, but it is not a sparse-stream detector under these frozen transfers. Its near-zero recovery below 50 members in both years supports a complementary role for OrbitTrace's fixed-4° sparse-episode method. These tracks answer different questions and must not be presented as a direct overall win by either method.

The HDBSCAN results do not establish blind catalogue-wide OrbitTrace rediscovery, and the sparse-episode results do not establish superiority over HDBSCAN on large showers.

## Provenance

- 2025 workflow: `31071589912`
- 2025 artifact: `8955917326`
- 2025 artifact digest: `sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`
- 2023 workflow: `31076062060`
- 2023 artifact: `8957554613`
- 2023 artifact digest: `sha256:cc00d20f0f5e70bd30338755f77567960ea8e600417bd080a7474119ebbdc804`
- 2023 result SHA-256: `fb82fd8edb005b24d646acab9969a5c57fea6c749d9c10fafceb558321992585`
- 2023 report SHA-256: `f3ddfb24e930722b465c9ba36351c8568925d3cbbd7c6d64a978afd0ecb0712b`

The two 2023 parser repairs occurred before any cluster or score was produced: the annual file has 46 fields rather than the preregistered 43, and its validated header names required reassignment to `csv.DictReader.fieldnames` after whitespace normalization. Neither repair changed an event, threshold, feature, parameter, label rule, seed, or metric.
