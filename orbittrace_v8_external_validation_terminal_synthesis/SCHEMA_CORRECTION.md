# Terminal synthesis artifact-schema correction

Frozen **before the first terminal-synthesis execution** and before any new data access.

The terminal protocol text used the descriptive AMOR string `INCONCLUSIVE_V8_AMOR_1996_1998_EXTERNAL_POWER`. Inspection of the already-frozen final AMOR runner source and its completed Actions log establishes that the exact serialized verdict is instead:

`INCONCLUSIVE_V8_AMOR_EXTERNAL_POWER`

The panel, run, artifact, N=19, Q=19, power interpretation, scientific meaning, and decision rule are unchanged. This is only an exact artifact-schema correction.

For minimal artifact access, the synthesis is additionally pinned to these exact result files and must not recursively scan auxiliary result JSONs:

- v8: `pooled_year_centroid_v8_development.json`
- SAAMER 2020/2021: `saamer_external_validation.json`
- SAAMER 2022/2023: `saamer_2022_2023_external_validation.json`
- AMOR: `v8_amor_1996_1998_external_validation.json`
- UKMON: `ukmon_2020_2021_freshness_adjudication.json`
- Harvard: `harvard_1968_1969_recurrence_eligibility.json`
- FRIPON: `fripon_2018_2019_integrity_stop.json`
- Hissar: `hissar_v8_coverage_eligibility.json`

No scientific gate, method parameter, panel status, or target boundary is changed by this correction.
