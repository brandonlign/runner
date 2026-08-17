# OrbitTrace annual-density bifiltration GMN ranking v1 — evaluator repair 1

## Status
Engineering-only post-truth repair. The original evaluation run `32037435314` opened the sealed GMN development truth and then raised `KeyError: 'family_id'` before any bifiltration successor metric or scientific verdict was emitted. The immutable prelabel artifact from that run is retained unchanged: artifact `9291169452`, `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

## Authorized repair
The frozen bifiltration rows contain `family_hash` and `event_ids`; the inherited `parent.metrics()` interface additionally requires a `family_id` key, but its scoring logic uses only `event_ids` and merely copies `family_id` into an intermediate row.

Repair exactly this schema mismatch by making a shallow copy of each already-frozen bifiltration candidate and assigning:

`family_id = "BIF1_" + family_hash`

No event membership, candidate order, persistence area, member count, equal-budget K, annual universe, truth mapping, metric definition, aggregation, gate, threshold, tie-break, or comparator may change. The adapter may not filter, add, remove, merge, split, or reorder candidates.

## Inputs frozen before repair
- Original protocol blob: `05d29d197ec77a9571deb1df2d6adbb7944e6dc3`
- Original prelabel artifact ID: `9291169452`
- Original prelabel SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`
- Bifiltration candidate pretruth SHA-256: `63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`
- Structural result SHA-256: `d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7`
- Recurrent-EOM metric source blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- Sparse evaluation source blob: `752df8212ce601227f6e9170b0fe994ba06b515d`

## Binding interpretation
This repaired endpoint is the continuation of the already-opened truth endpoint, not a new scientific attempt. Its PASS/FAIL under the original frozen gates is binding for persistence-area ranking. No score redesign, blend, support multiplier, route-specific exception, budget exception, or second ranking rescue is authorized from the outcome.