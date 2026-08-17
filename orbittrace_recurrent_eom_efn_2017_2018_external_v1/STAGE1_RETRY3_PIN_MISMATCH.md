# EFN Stage-1 live retry 3 — provenance pin mismatch

**Classification: engineering-only technical no-result. No EFN event query executed in this run.**

Run `31835755504` (job `94881578319`, head `a96a2486146f4b4dbfdf04e42aac66fbbde178f7`) stopped in the preaccess authorization step before `stage1_blind_receipt.py` was executed.

The sole mismatch was the Git blob asserted for the already-frozen solar-wrap repair JSON:

- workflow expected: `c6ed3fc90c45764c8101f62a993edb189502bb99`
- actual frozen `STAGE1_SOLAR_WRAP_REPAIR_FREEZE.json` blob: `3a4b0ccbd098944e2279d2f3bf9404a523b7ac68`

The frozen JSON content itself is unchanged and binds the successful synthetic repair audit run `31835619752`, artifact `9232358731`, digest `sha256:e0129742ff9e6578854015d091ff9c3bd1ee543b449c8c7c155d54b7d8c63b0e`.

Authorized repair: update only the workflow's asserted blob for `STAGE1_SOLAR_WRAP_REPAIR_FREEZE.json` to the actual Git blob above. Do not alter the Stage-1 ADQL, parser, modulo-360 normalization, inclusive protected interval, retained-ID logic, recurrent-EOM method, geometry mapping, labels, evaluator, or validation gate.

Firewall at failure:

- live EFN query executed in retry 3: false
- valid Stage-1 endpoint: false
- retained IDs frozen: false
- EFN geometry accessed: false
- EFN shower labels accessed: false
- target information accessed: false
- target-region physical values accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
- OrbitTrace target access: false
