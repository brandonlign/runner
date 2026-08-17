# Annual-density bifiltration GMN ranking v1 — engineering repair 1

## Status

**ENGINEERING-ONLY REPAIR FROZEN BEFORE ANY TECHNICALLY VALID SCIENTIFIC RESULT.**

The scientific protocol in `PROTOCOL.md` is unchanged.

## Prior execution

Workflow run `32037435314` completed the entire prelabel job successfully and sealed the endpoint prelabel before the evaluation job opened the already-authorized target-excluded GMN shower mapping.

The evaluation then terminated before result serialization and before the ten-gate contract could be enforced:

`KeyError: 'family_id'`

The exception occurred when the generic frozen Recurrent-EOM `metrics(...)` adapter received a bifiltration candidate row. The bifiltration prelabel stores `family_hash`, `event_ids`, `member_count`, `persistence_area`, `rank`, and `threshold_cell_count`, but not the adapter-only `family_id` key.

No `BIFILTRATION_GMN_RANKING_V1_RESULT.json` was produced by that attempt, no PASS/FAIL scientific verdict existed, and no outcome-informed scientific choice is made by this repair.

## Why the repair is scientifically inert

The frozen parent evaluator's `metrics(...)` creates an annual candidate containing `family_id` and annual-intersected `event_ids`, then calls `truth(...)`. The frozen `truth(...)` implementation reads only `event_ids`; it never reads `family_id` when computing overlap, precision, recall, F1, positivity, dominant precision, recovered ranks, fragmentation, or MRR.

Therefore the sole repair is:

- for each already-frozen bifiltration row, copy the row;
- set `family_id = family_hash`;
- pass that copy to the unchanged frozen metric implementation.

`family_hash` is already the immutable SHA-256 of the candidate membership and is already used as the frozen deterministic identity/tie-break in the preregistered candidate order.

The repair changes no event membership, candidate count, candidate rank, persistence area, equal budget K, annual universe, label mapping, metric definition, aggregation, promotion gate, firewall, or external-data access.

## Strong provenance lock

The prior successful prelabel artifact from run `32037435314`, artifact `9291169452`, has ZIP digest:

`sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`

Its exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 is:

`95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`

The repaired evaluator must refuse to score any prelabel whose bytes do not match that exact SHA-256. The workflow also verifies the same hash before evaluation.

## Binding rule

The first technically valid result produced after this interface-only repair is binding under the unchanged frozen protocol. A scientific FAIL closes the persistence-area-ranked bifiltration v1 lane exactly as preregistered; it does not authorize reranking or parameter rescue.
