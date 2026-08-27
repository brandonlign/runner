# OrbitTrace support-cut × bifiltration internal-mass v1 — prospective GMN truth endpoint

## Status
**FROZEN AFTER ZERO-LABEL STRUCTURAL PASS AND BEFORE THIS METHOD'S FIRST SHOWER-TRUTH RESULT.**

The structural source run `32041661731` passed all six frozen zero-label gates. Its ranked candidate prelabel is immutable:
- artifact `9292071213` (`orbittrace-support-cut-bifiltration-internal-mass-v1`)
- `SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json` SHA-256 `7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`
- structural verdict `PASS_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_STRUCTURAL`
- structural cross-scale mean-best-Jaccard `0.7867133741773226` versus recurrent-EOM `0.6183584075451847`, with 4/4 bucket wins.

This endpoint may **only evaluate** that prelabel. It may not reconstruct, rerank, filter, repair, or enrich the candidates.

## Frozen method
Candidate extraction is the complete pairwise-disjoint TopoModal support-resolved cut. Candidate ordering is frozen in the prelabel as:
1. internal two-density persistence mass `M_2D` descending, where `M_2D(S)=(1/|S|) sum_{B subseteq S}|B|A(B)` over the already-frozen annual-density bifiltration components;
2. inherited support-cut modal contrast descending only for exact `M_2D` ties;
3. family hash ascending.

No score recomputation is permitted in this truth endpoint. Verify rank continuity and monotonic lexicographic order from the stored fields only.

## Data and firewall
Use only target-excluded GMN 2022/2023 development truth. The candidate prelabel already contains the exact annual event-ID universes for all eight deterministic panels. The inclusive protected solar-longitude interval `[20°,55°]` remains excluded upstream and must not enter evaluation.

Forbidden:
- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014;
- ASFN/EFN event-level data;
- AMOS, MAARSY, DMS;
- any post-result method/rank/gate change.

## Equal budgets
Use the exact stored recurrent-EOM K in each subset and truncate both successor and recurrent lists to K:
- d=128 buckets 0..3: K=`29,35,38,33`;
- d=1024 buckets 0..3: K=`8,5,6,9`.

No budget exception or min(selected,parent) reinterpretation is allowed because the structural stage already verified successor capacity >= K in all eight panels.

## Evaluation
For each subset and each year 2022/2023, use the inherited recurrent-EOM known-shower metric function on the exact stored annual event universe. Record qualified matches, MRR, top-100 dominant precision, fragmentation, and recovered@25/@50/@100/@500.

Aggregate over the 8 annual panels at each scale.

## Binding ten-gate promotion contract
All ten must pass.

Fine d=1024:
1. qualified total strictly greater than recurrent-EOM;
2. qualified recovery nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

Coarse d=128:
6. qualified total not lower;
7. qualified recovery nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

Verdict is `PASS_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN` iff all ten are true; otherwise `FAIL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN`.

The first technically valid result is binding. A valid FAIL closes internal-mass v1. No area/support transform, ancestor evidence, maximum-component evidence, modal-contrast blend, alternative tie order, positive-score filter, quota, K change, metric change, or follow-up tuning is authorized from the truth result.

A PASS would establish a target-excluded GMN development successor to recurrent-EOM and would authorize only the already-governed next portability stage on exposed development data; it would **not** authorize protected external access or a promotion claim beyond the tested panels.