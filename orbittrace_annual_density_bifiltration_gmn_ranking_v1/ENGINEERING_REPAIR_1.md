# Annual-density bifiltration GMN ranking v1 — engineering repair 1

## Status

**FROZEN BEFORE THE REPAIRED SCIENTIFIC EVALUATION.**

This is an execution/interface repair only. It does not change the frozen annual-density bifiltration candidate universe, persistence-area order, memberships, equal-budget K values, recurrent-EOM comparator, truth metric, ten promotion gates, protected-region firewall, or any scientific parameter.

## Original technically invalid run

The first endpoint attempt was GitHub Actions run `32037435314` at execution commit `3c309c83186894e4acd63b55b18249476dbffd5c`.

Its prelabel stage completed successfully and uploaded:

- prelabel artifact ID `9291169452`;
- artifact digest `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`;
- `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

The evaluate job then stopped before producing `BIFILTRATION_GMN_RANKING_V1_RESULT.json` with:

`KeyError: 'family_id'`

at the generic recurrent-EOM `metrics()` adapter. The frozen bifiltration rows contain `event_ids`, `family_hash`, rank, persistence area, and member count but no legacy `family_id` display/identity field.

## Why the repair is scientifically inert

The pinned recurrent-EOM evaluator source blob is `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`.

Inside `metrics()`, `family_id` is copied into a temporary annual candidate dictionary. The immediately-called `truth()` function never reads `family_id`; all matching, qualification, precision, recall, fragmentation, and reciprocal-rank calculations depend on `event_ids` plus the fixed eligible-label mapping. Therefore supplying a deterministic identity string cannot alter any scientific metric.

No metric outcome from the failed attempt was emitted or used to choose this repair. The repair is determined solely by the exception and the pinned evaluator source.

## Exact repair

Use the already-frozen prelabel bytes from artifact `9291169452`; do not regenerate candidates.

For each bifiltration candidate in `(denominator, bucket, rank)` order, add exactly:

`family_id = "BIF_D{denominator}_B{bucket}_R{rank}_{family_hash}"`

No existing field is changed. Recurrent-EOM rows are unchanged.

The repair script must verify before truth that, after removing only `family_id`, the repaired prelabel is exactly identical to the original scientific payload, including:

- all event memberships;
- all candidate ranks and order;
- all family hashes;
- all persistence areas/member counts;
- all equal-budget K values;
- all recurrent-EOM comparator rows;
- all firewall flags.

Pinned hashes from the zero-truth repair construction:

- repair script SHA-256: `2796ab9e91a9a04f2b1431969a11fc984c645b9bf454b240daa5744e9dc712fc`;
- repair script Git blob: `4032dd3a0c9634af5a583ba7fc472b536f7960cd`;
- repaired prelabel SHA-256: `d410b75c29d5262d8526873c61fbac4005547383f38d673bcb95771761c0850c`.

## Binding rule

The first technically valid repaired evaluation using this exact adapter and the original frozen prelabel is binding. The original ten gates and verdict strings from `PROTOCOL.md` remain unchanged. No reranking, alternate bifiltration slice, parameter change, metric change, or second scientific rescue is authorized.
