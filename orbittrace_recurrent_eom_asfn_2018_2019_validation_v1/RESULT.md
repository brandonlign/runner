# Recurrent-EOM HDBSCAN v1 — binding NASA ASFN 2018/2019 pristine validation result

## 🔴 NEGATIVE scientific result

Promoted recurrent-EOM HDBSCAN v1 **failed** its frozen pristine cross-survey NASA All Sky Fireball Network (ASFN) 2018/2019 validation gate against vanilla HDBSCAN EOM on the identical pooled ASFN hierarchy.

This is the first technically valid ASFN scientific endpoint under the frozen protocol and is therefore binding. No ASFN-specific rescue is authorized.

## Binding provenance

- binding workflow run: `31850437866`;
- binding artifact: `9237338312`;
- artifact digest: `sha256:cebe8abd80899c5cfb27758f373f11882a309e501f2c22775881df0184fa83b6`;
- binding execution commit: `6f5fb2babf4c868fc931a08723f61f174190d9cf`;
- validation-result SHA-256: `10e38eb2eb850ca50c5759c2389ccfe8d48c83ff57729b5f9227a42d9c3a2f7e`;
- prelabel SHA-256: `de30f2ff46e6d4570f62e0adf120f77738ba73e350a075ee39ca054f17dcfd4c`;
- exact archive SHA-256: `c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`;
- verdict: `FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`.

The prior attempts remain technical no-results only:

- `31834974219`: original parser stopped at the hash-prefixed header before HDBSCAN/prelabel/labels/metrics;
- `31850281138`: NASA HTTPS connection timed out after transferring zero bytes, so the scientific runner was never invoked.

The exact hash-header wrapper then passed the separately frozen synthetic-only semantic audit (`31850078483`, artifact `9237225355`, result SHA-256 `212a52b402187d0bc20c85dc50ba9d0b6b52cbe5126398d9ca7b6b87ffa49ff2`). The binding run used the same frozen scientific runner through that wrapper and changed only bounded network transport tolerance to obtain the already-pinned archive.

## Frozen external sample

The binding runner traversed 33,657 physical ASFN records while semantically decoding non-validation/protected rows only far enough to obtain year and solar longitude.

For the frozen validation years:

- 2018 before blind exclusion: 5,050;
- 2018 excluded in inclusive `[20°,55°]`: 371;
- 2018 eligible clustering events: **4,679**;
- 2019 before blind exclusion: 4,885;
- 2019 excluded in inclusive `[20°,55°]`: 337;
- 2019 eligible clustering events: **4,548**;
- total eligible pooled events: **9,227**.

No protected-row radiant, speed, or shower label was decoded. Non-validation-year scientific fields were not decoded.

External ASFN association labels contained:

- 2018: 1,646 associated events, 3,033 sporadic, 28 eligible reference showers;
- 2019: 1,496 associated events, 3,052 sporadic, 26 eligible reference showers.

These labels were opened only after the complete candidate universe/order had been serialized and SHA-frozen.

## Exact recurrent-EOM versus vanilla outcome

Vanilla EOM and recurrent-EOM each produced **34 candidates**. The recurrent selected-node set was identical to vanilla: `mechanism_active=false` under the frozen gate.

### 2018

| Metric | vanilla EOM | recurrent-EOM | Gate |
|---|---:|---:|---|
| recovered @25 | 13 | 13 | tie |
| recovered @50 | 13 | 13 | pass |
| recovered @100 | 13 | 13 | pass/no strict gain |
| recovered @500 | 13 | 13 | tie |
| top-100 dominant precision | 0.3281787820986042 | 0.32817878209860424 | pass / numerical tie |
| MRR | **0.2368936618936619** | 0.23625323951410906 | **fail** |
| median top-500 fragmentation | 1.0 | 1.0 | pass |
| qualified matches | 13 | 13 | tie |

### 2019

| Metric | vanilla EOM | recurrent-EOM | Gate |
|---|---:|---:|---|
| recovered @25 | 11 | 11 | tie |
| recovered @50 | 11 | 11 | pass |
| recovered @100 | 11 | 11 | pass/no strict gain |
| recovered @500 | 11 | 11 | tie |
| top-100 dominant precision | **0.3038884200361933** | 0.30388842003619326 | **fail by floating-point epsilon** |
| MRR | **0.25696248196248195** | 0.2563852813852814 | **fail** |
| median top-500 fragmentation | 1.0 | 1.0 | pass |
| qualified matches | 11 | 11 | tie |

The tiny 2019 precision difference is not scientifically meaningful by itself; however, the frozen comparison is exact and the overall result fails independently because:

1. recurrent-EOM did not achieve a strict recovered@100 improvement in either year;
2. the selected-node set did not differ from vanilla (`mechanism_active=false`);
3. MRR was lower in both years.

Therefore the binding FAIL does not hinge on numerical epsilon.

## Scientific interpretation

The ASFN result shows **no evidence that recurrent-EOM improves vanilla HDBSCAN on this untouched cross-survey panel**. On the fixed 2018/2019 ASFN hierarchy, annual recurrence weighting did not change the selected cluster nodes at all. It only changed ordering among the same selected families slightly, and those rank shifts marginally worsened MRR in both years while leaving recovered-shower counts unchanged.

This does **not** erase the earlier target-excluded GMN development PASS or the 4/4 exposed SonotaCo superiority result. It does materially narrow the generalization claim: recurrent-EOM is the strongest demonstrated development method in the current lineage, but it has now **failed a genuinely pristine cross-survey validation** and cannot presently be claimed as externally validated across surveys.

No ASFN-specific change to annual normalization, minimum combiner, HDBSCAN parameters, speed scale, feature representation, ranking, label semantics, quality cuts, year selection, evaluator, or gate is authorized from this outcome.

AMOS 2023/2024 remains separately frozen and untouched; any future AMOS result must use its already-frozen protocol and may not be modified in response to ASFN.

## Parallel README-note adjudication

A parallel post-activation commit `f665a36fb0b1e91402482ebe22ef4a58fe95895a` added `README_RECEIPT_ARGUMENT_REPAIR.md` claiming that the frozen scientific runner required a `--readme-receipt` CLI argument. That claim is incorrect for the exact binding scientific-runner blob `8f5699326758dd11cc46f9a209049a8ed61dee3a`.

The exact frozen runner's `argparse` interface accepts only required `--archive` and `--output` arguments. The parallel note was committed after the binding execution head and was not present in run `31850437866`. It is therefore excluded from the binding ASFN lineage and supplies no reason to invalidate or rerun the technically valid endpoint.

## Firewall

The binding result records:

- `scientific_role='PRISTINE_CROSS_SURVEY_ASFN_2018_2019_VALIDATION'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `nonvalidation_year_scientific_fields_decoded=false`;
- `sonotaco_2013_2014_access=false`;
- `gmn_2020_2021_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
