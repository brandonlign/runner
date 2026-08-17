# Annual-density bifiltration GMN ranking v1 — engineering repair 1

## Status

**ENGINEERING-ONLY REPAIR FROZEN BEFORE ANY TECHNICALLY VALID GMN TRUTH RESULT.**

This repair does not change the frozen annual-density bifiltration candidate universe, membership, persistence-area ranking, equal-budget K, comparator, truth labels, metrics, ten promotion gates, physical geometry, annual density fields, threshold grid, or protected-data boundary.

## Prior technical no-result

The original frozen endpoint ran as GitHub Actions run `32037435314` from execution commit `3c309c83186894e4acd63b55b18249476dbffd5c`.

Its prelabel job completed successfully and sealed the intended target-excluded GMN endpoint package:

- prelabel artifact ID: `9291169452`
- artifact digest: `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`
- candidate-source SHA-256: `63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`
- structural-result SHA-256: `d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7`

The evaluate job then stopped on the first bifiltration candidate before a result file or promotion verdict existed:

`KeyError: 'family_id'`

The frozen bifiltration rows use `family_hash` as their stable identity and contain the required `event_ids`, but the generic recurrent evaluator expects every candidate dict to contain a `family_id` field.

## Why this is semantically inert

The exact frozen recurrent evaluator source blob remains `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`.

Its `metrics(...)` function copies `pooled_f['family_id']` into a temporary annual dict, then calls `truth(...)`. The `truth(...)` function never reads `family_id`; every scientific quantity is computed only from `event_ids` and the sealed annual truth mapping. Therefore candidate identity text cannot affect F1, positivity, dominant precision, recovered counts, first rank, MRR, or fragmentation.

Repair 1 performs exactly one adapter operation on bifiltration candidates immediately before calling the unchanged `metrics(...)` function:

`family_id = 'BIF/' + family_hash`

No event ID, candidate order, rank, persistence area, support, budget, or truth value is modified. The adapter is deterministic and one-to-one with the already-frozen membership hash.

## Binding inputs for repair 1

Repair 1 must download and verify the exact successful prelabel artifact from run `32037435314`; it must not regenerate the prelabel candidate package.

Required SHA-256:

- original prelabel JSON: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`
- original protocol blob: `05d29d197ec77a9571deb1df2d6adbb7944e6dc3`
- original evaluator blob: `31cce36ba7b43f09451f1a556ef46f52277cab16`
- sparse evaluator blob: `752df8212ce601227f6e9170b0fe994ba06b515d`
- recurrent wrapper blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- GMN utility SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- v8 support artifact SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`

The repaired evaluator must assert that every bifiltration candidate lacks no `family_hash`, preserve its `event_ids` unchanged, and create only the adapter `family_id` field in memory.

## Binding scientific contract

The scientific contract remains exactly the original `PROTOCOL.md`:

- target-excluded GMN 2022/2023 only;
- protected inclusive solar longitude `[20°,55°]` inaccessible;
- SonotaCo inaccessible;
- exact frozen bifiltration candidate order: persistence area descending, member count descending, membership SHA-256 ascending;
- equal budget K equals complete recurrent-EOM candidate count per pooled subset;
- exact 16 annual truth panels;
- exact ten sparse promotion gates;
- PASS only if all ten pass.

The first technically valid repaired execution is binding. A scientific FAIL closes the frozen persistence-area-ranked bifiltration v1 lane exactly as preregistered. No post-result reranking, threshold change, score blend, parameter search, or second scientific repair is authorized.
