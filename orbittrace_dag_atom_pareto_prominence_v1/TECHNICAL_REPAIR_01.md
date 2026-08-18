# DAG-atom Pareto-prominence v1 — Technical Repair 01

## Classification of run 32188889835

Run `32188889835` is a **technical no-result**, not `PASS_DAG_ATOM_PARETO_PROMINENCE_V1` and not `FAIL_DAG_ATOM_PARETO_PROMINENCE_V1`.

The zero-label pretruth job completed successfully and sealed:

- pretruth artifact `9343467987` (`orbittrace-dag-atom-pareto-prominence-v1-pretruth`);
- artifact digest `sha256:07323d69ad40e102cbdf3189d272c323de0893e32fbec361f01eec7e437281f6`;
- prelabel SHA-256 `8621c48ec179cc808b64bcd1b4a19f2af12dd38ef01ab9ae32cdc4c38dc67d7f`;
- pretruth SHA-256 `e17ace61a139598dec69243f2489fc9f8c48831c90bb2c86c1c224628fb6c169`;
- verdict `PASS_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH` with all 12 gates true.

The conditional truth job then loaded the exact frozen target-excluded truth runtime and historical comparator, but failed on the **first successor metric call** before any successor metric, scale aggregate, promotion gate, verdict, or result file existed:

`KeyError: 'family_id'`

The traceback is at `orbittrace_recurrent_eom_hdbscan_v1/run_development.py:173` where the legacy `metrics()` adapter constructs a temporary annual row containing:

- `family_id = pooled_f['family_id']`;
- `event_ids = ...`.

The downstream `truth()` function uses only `event_ids` to compute counts, precision, recall, overlap, F1, and positive-match status. It does not use `family_id`. Thus the missing field is an evaluator-interface identifier, not a scientific input.

Truth labels were loaded by the runtime before this exception, and the first d=64 comparator metric was computed in memory immediately before the failing successor call. No comparator value was printed, persisted, used for a decision, or exposed to method construction. No successor metric was produced. The frozen candidates, order, comparator, 17 gates, and all parameters were already committed before this run.

## Sole repair

Technical Repair 01 adds one compatibility adapter around the exact frozen recurrent-EOM evaluator:

- if a pooled candidate already has `family_id`, pass it unchanged;
- if it lacks `family_id`, require it to be a frozen DAG atom with `atom_hash`, copy the row, and set `family_id = 'DAGATOM1:' + atom_hash`;
- call the exact frozen `metrics()` implementation unchanged.

The adapter does **not** alter:

- `event_ids` or any candidate membership;
- successor order or Pareto layer;
- recurrent or TopoModal provenance;
- candidate budget K;
- comparator identity/order;
- annual event universe;
- eligibility, precision, overlap, recovery, MRR, fragmentation, or one-to-one truth semantics;
- any of the 17 frozen gates;
- protected-region, target, or external-data authorization.

Because `family_id` is unused by the truth calculation after the temporary annual row is constructed, this repair is semantically neutral to every scientific metric.

## Retry governance

The successful pretruth artifact from run `32188889835` is immutable and is reused directly. It is not regenerated after truth access.

Exactly one clean truth retry is authorized through the compatibility adapter. The original protocol (`7e586325...`), builder (`441bec6a...`), truth evaluator (`b2a07da8...`), sealed prelabel, ranking, comparators, and gates remain unchanged.

The first retry that reaches a complete binding truth JSON under these unchanged scientific rules is binding. No other repair, threshold, filter, rank change, or rescue is authorized from this technical failure.
