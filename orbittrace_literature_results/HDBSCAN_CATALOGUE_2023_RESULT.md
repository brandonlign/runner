# SonotaCo 2023 HDBSCAN one-shot transfer

The frozen catalogue-scale HDBSCAN configuration transferred successfully to the independent SonotaCo 2023 replacement catalogue.

- workflow run: `31072548443`;
- artifact: `8956177186`;
- artifact digest: `sha256:230319166d2de757fbe709eecb0d904f258f0e45a93c8dcdd31c104f05c38169`;
- result SHA-256: `9c26bfa64af8102f5c1a5faf62ca419e274fc402172128a6a00498a068f53714`;
- verdict: `PASS_SONOTACO_2023_HDBSCAN_ONE_SHOT_TRANSFER`;
- all 16 frozen-input, parser, package, parameter, quality-filter and execution gates passed.

The first attempted workflow stopped before any data access because source-part checksums incorrectly assumed trailing newlines and the transfer runner recorded scikit-learn 1.5.2 instead of the exact successful 2025 environment's 1.9.0. Those transport/environment records were corrected before the parser or 2023 archive was accessed. No HDBSCAN scientific parameter changed.

## Primary frozen-configuration transfer

- 24,923 quality-filtered events;
- 14 reference showers retaining at least 100 members;
- 13 HDBSCAN clusters;
- noise fraction 0.584079;
- NMI 0.743023;
- ARI 0.745363;
- silhouette excluding noise 0.690320;
- 11/14 showers with matched F1 above 0.5;
- 8/14 above 0.8;
- mean/median matched shower F1 0.651696/0.844851.

## Identical-parameter all-label coverage audit

- 25,889 quality-filtered events and 67 reference showers;
- 14 HDBSCAN clusters;
- noise fraction 0.593650;
- NMI 0.694069;
- ARI 0.695559;
- matched-shower mean F1 by annual size:
  - 4–9: 0.000000;
  - 10–24: 0.005310;
  - 25–49: 0.000000;
  - 50–99: 0.174118;
  - 100+: 0.649272.

## Replication judgment

The 2023 result closely reproduces the 2025 pattern. HDBSCAN is strong for large catalogue showers but has essentially no useful recovery for annual showers below roughly 50 members when the published minimum cluster size of 100 is transferred unchanged. This supports a task-specific comparison rather than a universal ranking: HDBSCAN remains the appropriate large-catalogue baseline, while the fixed-4° detector's claimed contribution is sparse four-to-twelve-member episode recognition.

The pre-existing solar-longitude interval 20°–55° remained excluded before label access, so this run did not inspect or score OrbitTrace and is not a blind OrbitTrace rediscovery test.
