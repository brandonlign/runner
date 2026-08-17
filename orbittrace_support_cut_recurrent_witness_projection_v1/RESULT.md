# OrbitTrace support-cut recurrent-witness projection v1 — binding structural result

## Verdict
`FAIL_SUPPORT_CUT_RECURRENT_WITNESS_PROJECTION_V1_STRUCTURAL` — closed before truth.

## Binding provenance
- workflow run `32042992098`
- first attempt job `95425501501`: GitHub artifact-service failure before method execution
- valid attempt job `95425623265`
- execution commit `78c9126fa5f099f8a49feadb78e87ca7296dbf85`
- binding artifact `9292297190`
- artifact digest `sha256:f9ac8d7ff70aceaf93357401a2b09a642ed4574fd2f3316ca855ce5dda1e1f18`

No shower truth, OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.

## Structural result
Passed:
- candidate capacity in all 8 panels;
- output pairwise disjointness in all 8 panels;
- witness-rank nonexpansion;
- cross-scale mean best-Jaccard `0.8182347460632067` versus recurrent-EOM `0.6183584075451847`;
- cross-scale nonlower in 4/4 buckets.

Bucketwise projection vs recurrent coherence:
- b0 `0.9030610400363799` vs `0.5606386581636582`
- b1 `0.7053231372269999` vs `0.7051612903225806`
- b2 `0.8835535859673791` vs `0.5504761904761905`
- b3 `0.780001221022068` vs `0.6571574912183094`

Failed exactly:
- `topk_parent_witnessable_all_8`.

Top-K recurrent witnessability:
- d128,b0 22/29
- d128,b1 27/35
- d128,b2 29/38
- d128,b3 27/33
- d1024,b0 7/8
- d1024,b1 5/5
- d1024,b2 4/6
- d1024,b3 8/9

No duplicate recurrent witnesses occurred in any panel.

## Interpretation and closure
The projection architecture strongly improves cross-scale coherence and preserves support-cut disjointness/rank nonexpansion, but support-cut has no event representation at all for a nontrivial fraction of recurrent-EOM candidates. Therefore exact witness projection alone cannot structurally guarantee preservation of every early recurrent representation.

This exact mechanism is closed before truth. Do not relax the witnessability gate or rescue with Jaccard/F1/normalized-overlap witnesses, global matching, overlap thresholds, quotas, rank fusion, or slot rules.

A distinct architecture may retain an exact recurrent candidate only when its event set has zero overlap with the entire support-cut catalogue; such a candidate is by construction outside the support-cut representation language and disjoint from every support-cut candidate. That completion is not authorized here and requires a separately frozen protocol and zero-label gate.