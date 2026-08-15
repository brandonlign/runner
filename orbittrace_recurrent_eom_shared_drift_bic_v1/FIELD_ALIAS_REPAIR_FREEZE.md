# Shared-drift BIC v1 — field-alias repair freeze

## Classification of first activation

Workflow run `31892425248`, artifact `9248944430`, stopped before `RECURRENT_EOM_SHARED_DRIFT_BIC_V1_PRELABEL.json` or `RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT.json` existed.

The zero-truth synthetic BIC audit passed. The exact binding recurrent-EOM evidence was verified. The scientific runner then parsed the complete target-excluded GMN 2022+2023 catalogue and reached physical-response extraction, where it raised:

`KeyError: 'sun_lon'`

The exact frozen parent normalizer returns normalized event dictionaries with keys:

- `sol`
- `lon`
- `lat`
- `vg`

where `lon` is the already-parsed Sun-centered longitude and `lat` is the already-parsed ecliptic latitude. The failed successor runner incorrectly tried to access the pre-normalization alias names `sun_lon` and `ecl_lat` after normalization.

This is classified as a **technical no-result**. No successor physical sufficient statistics, BIC values, shared-drift stability, successor selected nodes, prelabel catalogue, shower-truth evaluation, or scientific verdict were produced.

## Exact authorized repair

The clean retry may change exactly two normalized-dictionary field references in the frozen scientific runner:

1. `e["sun_lon"]` -> `e["lon"]`
2. `e["ecl_lat"]` -> `e["lat"]`

No other runner text, scientific source, protocol, physical coordinate definition, response set, predictor, OLS model, BIC formula, parameter count, identifiability rule, shared-model weight, recurrent-stability multiplication, HDBSCAN configuration, EOM extraction rule, ranking, metric, gate, or dataset may change.

The repair wrapper must assert that each old literal occurs exactly once and that no unapproved text replacement is made. The original frozen runner blob `bc03d41a6b6442c589bbb6f219ee7b7c8feb2bd7` remains preserved; the wrapper produces the mechanically repaired runtime copy only for the clean retry.

The first technically valid clean-retry GMN result remains binding under the original protocol blob `f8774a8cc34557822146816d61680b40c855487d`.