# OrbitTrace v6 direct-finalize technical recovery protocol

## Classification

Technical recovery only. This protocol does not define, modify, tune, or replace any scientific rule in v3-primary catalogue v6.

The source fanout execution is GitHub Actions run `31282128101`. It completed the target-excluded pre-exact capture for both years and all twelve exact-rescore shards successfully. The 2022 replay later failed before a scientific verdict because regenerating the nearest-neighbor proposal path produced a different proposal-record identity at solar-longitude center 0°. That replay failure is an execution reproducibility problem, not a detector outcome.

## Authoritative scientific realization

For this frozen execution, the authoritative proposal realization is the original pre-exact capture from run `31282128101`, not a later attempt to regenerate nearest-neighbor/tie decisions.

The authoritative exact-score realization is the complete set of six exact-rescore artifacts per year from the same run, each already tied by SHA-256 to the corresponding pre-exact checkpoint and preserving the captured proposal-anchor order.

No proposal may be added, deleted, replaced, rescored approximately, regenerated from a different tie realization, or selected from the recovery outcome.

## Required recovery identities

Before any recovered component, family, label metric, gate, or verdict may be used:

1. exact frozen v6 source SHA-256 must be `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9` before the already-source-audited two-line implementation repair;
2. repaired source SHA-256 must be `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`;
3. exact event-row hashes must reproduce the pre-exact scan and calibration hashes for each year;
4. solar longitude 20°–55° must remain absent;
5. all six exact shard indices must exist for each year;
6. every exact shard must reference the exact corresponding pre-exact SHA and scan-row SHA;
7. exact center coverage must equal the captured center universe exactly once;
8. for every center, exact output proposal-anchor order must equal the authoritative captured proposal order;
9. `calibrate_year_v6` must be rerun from the exact same calibration-event rows and frozen deterministic year seed;
10. for **every captured proposal**, its stored pre-exact Brown and fixed4 proposal p-values must be reproduced to absolute tolerance `1e-15` by the fresh calibration before the saved exact output is consumed;
11. therefore the minimum exhaustive proposal-calibration identity checks are `287,722` for 2022 and `467,960` for 2023;
12. supported calibration bins must remain at least 30/year;
13. proposal cap must remain exactly 512/window and annual primary proposal budget exactly 36,864.

Any failed identity above is a technical/integrity no-result. It is not a scientific v6 failure and does not authorize P1.

## Exact post-rescore semantics

After all identities pass, recovery may only apply the exact frozen `scan_year_v6` tail to the saved exact records, in the original captured center/proposal order:

- Brown proposal p-value from `proposal_brown_score` and frozen `proposal_cal`;
- v3 p-value from `v3_score` and frozen `v3_cal`;
- fixed4 p-value from `fixed4_score` and frozen `fixed4_cal`;
- v3 detection iff `p_v3 <= 0.05`;
- rescue detection iff `p_fixed4 <= 1/129 + 1e-15`;
- unchanged primary and rescue anchor conflict keys;
- unchanged per-bin anchor cap;
- exact repaired calls to `component_records_track_v6` for `v3` and `fixed4_rescue`;
- unchanged family construction, evaluation, gates, reporting, and verdict through the repaired `main()` via checkpoint replay.

No new floating-point scientific formula is introduced.

## Unavailable non-scientific diagnostics

Fanout-v2 did not serialize four counts that are calculated before the globally deduplicated exact proposal list:

- `prefilter_candidates`;
- `proposal_candidates_scored`;
- `primary_proposals_selected_before_dedup`;
- `rescue_proposals_selected_before_dedup`.

Exact-source audit performed before recovery activation confirms each of these field names occurs only at audit-dictionary construction in the frozen v6 source; none is read by component construction, family construction, ranking, known-shower evaluation, scientific gates, integrity gates, report formatting, or the final verdict.

Recovery therefore records these four diagnostics explicitly as unavailable/null rather than fabricating them from a different nearest-neighbor replay realization. All scientifically operative and gate-relevant fields are exact or reconstructed from authoritative captured/exact outputs.

## Allowed result

Only after all recovery integrity checks pass may the unchanged repaired main emit:

- `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`; or
- `FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`.

A PASS follows the already-frozen Sugar/HDBSCAN matched-literature adjudication. A scientific FAIL activates the already-frozen P1 successor. A technical/integrity recovery failure activates neither.

## Target firewall

No OrbitTrace target coordinates, members, identity, previous target rank, target-containing output, or event in solar longitude 20°–55° may enter this recovery or determine whether it is accepted.
