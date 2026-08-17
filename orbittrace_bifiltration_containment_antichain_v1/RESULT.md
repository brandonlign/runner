# OrbitTrace bifiltration containment-antichain v1 — binding zero-label result

## Verdict
`FAIL_BIFILTRATION_CONTAINMENT_ANTICHAIN_V1_STRUCTURAL` — closed before truth.

Binding run: `32041031850`
Artifact: `9291953018`
Artifact digest: `sha256:21753f313c23e67baf991262fac7bb35553c7692fa251f5b4f18ab4db1336b27`
Execution commit: `b979f2c1d08cde46ecb52293df1d6ff1ffe0f627`

No shower truth, OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.

## What worked
- top-K strict-containment pairs were reduced to zero in all 8 panels;
- top-K unique-event coverage was nonlower in all 8 panels;
- pooled top-K unique-event coverage increased from `1889` to `3120`.

## Binding failures
- capacity gate failed: fine `d=1024,b=0` retained only `6` antichain candidates for recurrent budget `K=8`;
- mean cross-scale Jaccard was `0.5579197999397274` vs recurrent-EOM `0.6183584075451847`;
- antichain cross-scale Jaccard was below recurrent in all four buckets (`0/4` nonlower).

Therefore no GMN truth endpoint is authorized for this exact selector. Do not rescue with an overlap threshold, quota, alternative greedy direction/order, area exponent, support multiplier, or relaxed capacity/coherence gate.

## Interpretation
Exact containment explains much of the persistence-area list's redundancy, but deleting all comparable candidates is too aggressive under fine thinning and harms cross-scale stability. The bifiltration generator remains useful as an evidence source, but this result argues against forcing its complete candidate universe into a standalone antichain catalogue. A distinct successor may instead apply the two-density evidence to a candidate set whose nonredundant extraction and capacity are already established independently.