# Authoritative GMN v31 offline development package v1

Status: **PASS — engineering/provenance package only**.

Authoritative build:

- GitHub Actions run `31663453082`
- job `94332964236`
- execution commit `7938571236e2029e8b7b9079ef38d6a89293e919`
- artifact `9167087908`
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`
- artifact size `75130` bytes

The exporter executed the exact passed GMN v31 parent and reproduced:

- candidate count: 226
- feature dimension: 23
- prelabel SHA-256: `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`
- feature matrix SHA-256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- parent raw OOF margin SHA-256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- recovered@25/@50/@100: `23 / 41 / 66`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified matches: 95

Exported family-level package:

- `GMN_V31_OFFLINE_X.npy`: exact 226x23 parent intrinsic representation, SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- `GMN_V31_OFFLINE_CENTROIDS.npy`: exact 226x8 parent centroid matrix, SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`
- `GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1.json`: manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`
- eligible development labels: 355
- positive families: 111
- fold counts: `0:52, 1:44, 2:46, 3:43, 4:41`

Firewall/schema enforcement passed. The package exports no raw GMN event rows, raw event IDs, or raw hidden-label mapping, and contains no SonotaCo 2013/2014, OrbitTrace target-region, MAARSY, or DMS scientific data. Protected solar longitude 20°–55° remained excluded before the exact parent representation/truth summaries were produced.

This package is **not** a new scientific result and evaluates no successor. It is the authoritative deterministic GMN 2022+2023 target-excluded v31 development package for future already-frozen v31-family successor experiments. Any successor must still be scientifically motivated and frozen before its first technically valid outcome.
