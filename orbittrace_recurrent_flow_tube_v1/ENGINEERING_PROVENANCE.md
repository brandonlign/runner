# RFT v1 engineering provenance

## Pre-result workflow attempt

Workflow run `31508263091` did **not** reach a scientific GMN 2022 result.

All frozen RFT source/protocol pins and frozen support-artifact checks passed. Execution then stopped before catalogue loading/evaluation because the established frozen catalogue-v3 runtime had not been decoded into `/tmp/run_wavelet_catalogue_v3_development.py`.

Observed exception:

`RuntimeError: frozen catalogue-v3 runtime was not decoded`

This is an engineering/runtime setup failure only. It exposed no RFT performance result and therefore does not count as the first valid GMN 2022 scientific outcome.

The repair was registered separately in PR #1203 by restoring the exact existing runtime decode/audit step and exact frozen runtime SHA-256 `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`.

No RFT scientific constant, protocol rule, candidate rule, score, metric, gate, or ablation changed. Frozen science remains:

- protocol blob `515362e69bec642a891e44dfd87dce9693942574`
- development source blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`

Firewall state throughout the failed attempt:

- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `sonotaco_2013_2014_access=false`
- `gmn_2023_access=false`
