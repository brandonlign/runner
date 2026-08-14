# Hissar 1968–1969 recurrent-EOM preaccess adjudication

**Classification: NEUTRAL — event rows remain untouched; recurrent-EOM annual-domain comparability is not satisfied.**

This adjudication uses only already-existing zero-row OrbitTrace artifacts plus published Hissar documentation. It does **not** submit the IAU MDC Hissar form, contact a result/download endpoint, or inspect a Hissar meteor row.

## Existing untouched status

The prior Hissar program already established freshness and metadata compatibility without scientific-row access. Its final zero-row coverage adjudication is:

- run `31228615518`;
- artifact `9012960964`;
- digest `sha256:790cadb1f10c24b3a9bc37435b34a276020bb4abdc3d436a29caed657113f6b4`;
- `hissar_catalogue_form_submitted=false`;
- `hissar_meteor_row_access=false`;
- `hissar_result_or_download_endpoint_contacted=false`;
- `scientific_event_values_inspected=false`;
- published extent `1968-12-12.73530` to `1969-12-24.18900`.

That zero-row audit conservatively proved that calendar 1968 spans at most 19.2647 days and at most four 10-degree solar-longitude bins even under a deliberately loose 1.1 deg/day solar-longitude envelope.

## Interface compatibility

Unlike Obninsk, Hissar is field-compatible with the promoted recurrent-EOM representation. Published IAU MDC documentation defines:

- `LS` as solar longitude at meteor detection;
- `RA` / `DEC` as J2000 geocentric radiant coordinates;
- `Vg` as geocentric velocity.

Therefore no undocumented speed substitution is required.

## Recurrent-EOM domain incompatibility

The promoted recurrent-EOM method is not merely a two-batch consensus rule. Its scientific object is **annual recurrence**: for every HDBSCAN hierarchy node, ordinary EOM mass is partitioned by observing year, each annual contribution is normalized by that year's accessible event count, and the node objective is the minimum of the two annual values.

All binding uses so far compare two broadly annual survey domains after the same 20°–55° exclusion. Hissar calendar 1968 is fundamentally different: it is December-only, whereas 1969 extends through almost the entire year. Thus the two normalized operands would be defined over drastically different solar-longitude support. Running the unmodified formula would make a cluster's 1968 recurrence score conditional on December availability rather than on comparable annual survey coverage.

This is not repaired by event-count normalization: normalization changes total mass scale, not missing phase support. Splitting 1969, redefining observing epochs, filling missing solar-longitude intervals, dropping annual recurrence, or adding a phase-overlap correction would create a new method after inspecting external-survey metadata and is not authorized as recurrent-EOM v1 validation.

## Binding consequence

Verdict:

`DEFER_HISSAR_RECURRENT_EOM_EXTERNAL_VALIDATION_ANNUAL_DOMAIN_INCOMPATIBLE_PREACCESS`

- Do **not** open Hissar event rows for recurrent-EOM v1.
- Do **not** reinterpret 1968/1969 as equal-coverage annual panels.
- Do **not** split/reweight/impute the survey to make the panel fit.
- Preserve Hissar as event-value untouched for a future method explicitly frozen for unequal phase coverage before row access.

This is scientifically neutral: it is neither a recurrent-EOM success nor failure.

## Firewall

- `target_information_access=false`
- `target_region_events_accessed=false`
- `hissar_meteor_row_access=false`
- `hissar_catalogue_form_submitted=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected `[20°,55°]` remains inaccessible.
