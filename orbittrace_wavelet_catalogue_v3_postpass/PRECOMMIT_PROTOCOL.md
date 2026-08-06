# OrbitTrace post-development blind sequence

This directory is preparatory only. Nothing here loads GMN 2024–2026, restores solar longitude 20°–55°, evaluates OrbitTrace, or changes the frozen detector.

## Entry gate

No held-out catalogue may be opened unless a preserved development result from frozen source commit `f930664025250c9861683bef5bdeb0c6d19a4231` has:

- verdict `PASS_WAVELET_CATALOGUE_V3_DEVELOPMENT`;
- years exactly `2022, 2023`;
- blind exclusion exactly `20.0, 55.0`;
- fixed4 rescue threshold exactly `1/129`;
- fixed4-only detections kept outside the wavelet ranking;
- every reported development gate equal to `true`;
- an immutable SHA-256 digest recorded before validation begins.

## Phase 1: target-excluded validation

After the entry gate passes, clone the exact frozen scientific source and run only GMN 2024–2025 with solar longitude 20°–55° removed before label normalization. Candidate generation, exact rescoring, components, family linking, and ranking remain label-free.

Use the same predeclared validation standards as development:

- at least 30 supported Mondrian bins per year;
- at least 50 recurrent wavelet-ranked families;
- top-100 known-shower recovery at least 80% of the fixed4 baseline on the same validation panel;
- top-100 dominant-label precision at least 0.50;
- qualified known-shower matches at least 60% of the fixed4 baseline.

A validation failure is preserved and ends the blind-discovery sequence. No tuning on 2024–2025 is allowed.

## Phase 2: complete blind catalogue search

Only after validation passes and the method is frozen again:

1. Run the complete target-free catalogue search with the 20°–55° interval restored.
2. Do not load OrbitTrace coordinates, activity interval, member identities, orbit, or canonical artefacts.
3. Save the full ranked wavelet catalogue and separate fixed4 rescue queue.
4. Record candidate members, yearly components, scores, ranks, and SHA-256 digests.
5. Lock the catalogue commit and digest before any reveal code can run.

## Phase 3: reveal

The reveal is a separate process that consumes only the locked catalogue and the independently preserved OrbitTrace reference bundle. It reports:

- catalogue rank;
- activity agreement;
- radiant and velocity agreement;
- recurrence by year;
- orbital agreement;
- member overlap, precision, and recall;
- significance and competing candidates.

A methodology-driven blind discovery or independent blind rediscovery claim is allowed only if an OrbitTrace-consistent candidate was generated and ranked in the locked catalogue before reveal. The historical exploratory HDBSCAN chronology remains unchanged.
