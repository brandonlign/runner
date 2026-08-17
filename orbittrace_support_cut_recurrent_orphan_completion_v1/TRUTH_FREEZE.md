# OrbitTrace support-cut recurrent-orphan completion v1 — conditional truth freeze

## Status

**FROZEN AFTER THE PREREGISTERED ZERO-LABEL STRUCTURAL PASS AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS CATALOGUE.**

This file activates only Stage 2 already authorized by `orbittrace_support_cut_recurrent_orphan_completion_v1/PROTOCOL.md`. It introduces no new scientific choice.

Authoritative Stage 1:

- workflow run: `32043362123`
- artifact: `9292356070`
- artifact digest: `sha256:56a4805cba55ef074af27eebde491362620057941711ed9f589914b25fcd506a`
- immutable serialized catalogue prelabel SHA-256: `278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a`
- structural result SHA-256: `38b68cf74dc3d69128beb484abd2af3a266c40987266d2941f4855a53a0ed374`
- structural verdict: `PASS_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL`

Every Stage-1 gate passed. No shower truth was used in Stage 1.

## Immutable endpoint

The truth evaluator may only score the exact serialized `successor_candidates` and `recurrent_candidates` order already contained in the prelabel above. It may not regenerate, reorder, filter, blend, rescore, truncate except to the already-frozen equal budget K, or otherwise alter either catalogue.

The exact ten gates are inherited unchanged from the parent protocol:

Fine `d=1024`:

1. successor qualified-total strictly greater than recurrent-EOM;
2. successor qualified matches nonlower in at least 6/8 annual panels;
3. successor mean MRR not lower;
4. successor mean top-100 dominant precision not lower;
5. successor mean median top-500 fragmentation not higher.

Coarse `d=128`:

6. successor qualified-total not lower;
7. successor qualified matches nonlower in at least 6/8 annual panels;
8. successor mean MRR not lower;
9. successor mean top-100 dominant precision not lower;
10. successor mean median top-500 fragmentation not higher.

All ten are mandatory. The first technically valid truth result is binding.

## No rescue

A valid truth failure permanently closes this exact recurrent-orphan completion catalogue. No overlap threshold, normalized overlap, Jaccard/F1 witness, orphan quota, partial orphan retention, rank fusion, source slot, global matching, alternate support-winner rule, append-order change, budget change, score blend, or gate relaxation is authorized after outcome.

## Firewall

Only target-excluded GMN 2022/2023 development truth may be accessed. Inclusive solar longitude `[20.0,55.0]` remains excluded. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS remain inaccessible.
