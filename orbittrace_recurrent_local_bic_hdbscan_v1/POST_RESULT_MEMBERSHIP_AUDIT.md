# Recurrent local-BIC HDBSCAN v1 — post-result membership audit

**Role: interpretation correction only. No method change, rerun, truth-guided threshold, successor activation, or protected/external data access.**

This audit compares only the already-frozen binding pretruth membership payloads from:

- promoted recurrent-EOM GMN run `31827903547`, prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`;
- recurrent local-BIC GMN run `31926875888`, prelabel SHA-256 `fd400043e1356b4db7d85c1d97b5384f24f8643d0854af4fb559462c7a2ce355`.

No shower labels or truth identities are required for the comparison below.

## Exact membership overlap

The promoted recurrent-EOM catalogue contains `2,097` exact member sets. The recurrent local-BIC catalogue contains `4,371` exact member sets.

Only **1 exact membership** is shared between the two catalogues:

- recurrent-EOM rank `350`;
- local-BIC rank `327`;
- member count `36`.

Therefore:

- recurrent-EOM-only exact memberships: **2,096**;
- local-BIC-only exact memberships: **4,370**;
- exact set overlap: **1 / 2,097** parent memberships.

## Interpretation correction

The binding scientific metrics remain unchanged: qualified known-shower matches increased `236 -> 259` in 2022 and `244 -> 267` in 2023, while the frozen promotion gate failed because early-budget recovery/precision/MRR did not all preserve the parent.

However, those gains must **not** be described as merely adding weak branches beneath an otherwise preserved 10/10 hierarchy. Changing the HDBSCAN support from `10/10` to `8/4` reconstructs essentially the entire selected membership catalogue. The experiment therefore jointly demonstrates that a lower-support density hierarchy can produce a broader truth-recoverable catalogue, and that this exact reconstructed hierarchy/local-BIC combination does not preserve the incumbent's early-ranking quality.

The data do **not** isolate whether the additional qualified matches arise from newly exposed weak branches, changed boundaries of previously represented showers, fragmentation/merging changes, or a combination of those mechanisms. Any claim that the old hierarchy simply "hid 23 showers" would be stronger than the frozen evidence supports.

This correction narrows the scientific interpretation only. The exact recurrent local-BIC architecture remains permanently closed under its original no-rescue rule.