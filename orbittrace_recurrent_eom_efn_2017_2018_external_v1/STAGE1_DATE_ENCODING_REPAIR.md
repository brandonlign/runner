# EFN Stage-1 VizieR date-encoding repair

**Classification: engineering-only technical repair after a Stage-1 no-result. No EFN geometry or shower-label access.**

## Triggering technical no-result

Repaired live Stage-1 retry run `31834474845` passed all preaccess authorizers and the returned-header repair. The frozen blind-index query was accepted by VizieR and the parser reached the first row, then stopped before producing a valid retained-ID set because the returned `Obs_date` value was an integer-like VizieR time encoding rather than a printable year-prefixed timestamp.

Exact parser failure:

`unexpected Obs.date year encoding: '594264654'`

Binding technical-failure provenance:

- run: `31834474845`
- job: `94877568290`
- execution head: `af200be9f86bc4e9a5a00fcb4e37cfbd96fd402f`
- artifact: `9231937755`
- artifact digest: `sha256:dbd293662bb36449a92dec628b0b23b9d0bfc738b20a82e6f21c002e02e19c57`

No valid Stage-1 endpoint was created. No retained-ID list was frozen. The raw 824-row response was not persisted or uploaded. Stage 2 geometry and Stage 3 shower labels remain unopened.

## Official VizieR convention

VizieR's own META catalogue documents internal date/time integer fields using the convention `sec/2000`; examples include `METAtab.loadate/release` and `METAstat.tstart/tlocal/tother`, each explicitly described as date/time in `sec/2000` with `time.epoch` semantics.

Primary VizieR references inspected on 2026-08-14:

- `https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=METAtab`
- `https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=METAstat`

The EFN TAP metadata already frozen in `TAP_SCHEMA_FREEZE.json` reports `Obs.date` as integer with unit seconds and observation-date/time semantics. The first safely exposed Stage-1 value, `594264654`, interpreted under the documented VizieR `sec/2000` convention from `2000-01-01T00:00:00`, corresponds to `2018-10-31T01:30:54`, inside the frozen 2018 survey year. Interpreting the same integer as Unix seconds would place it in 1988 and contradict the fixed 2017/2018 catalogue cohort.

## Authorized parser-only repair

Keep the live ADQL query **exactly unchanged**:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

Keep the returned CSV header mapping exactly unchanged:

`Code, Obs_date, Lsun`

Change only `parse_year()`:

1. require `Obs_date` to be an integer decimal string;
2. interpret it as elapsed seconds from `2000-01-01T00:00:00` under the VizieR `sec/2000` convention;
3. derive only the UTC calendar year;
4. require that year to be exactly 2017 or 2018;
5. fail closed on negative/noninteger/out-of-domain values.

Frozen numeric boundaries implied by that convention:

- 2017 starts at `536544000` sec/2000;
- 2018 starts at `568080000` sec/2000;
- 2019 starts at `599616000` sec/2000.

Therefore:

- `536544000 <= Obs_date < 568080000` => 2017;
- `568080000 <= Obs_date < 599616000` => 2018;
- every other value fails closed.

Only the year is retained/used. No timestamp value is written to a Stage-1 output artifact.

## No scientific change

This repair does not alter:

- the fixed 824-row EFN cohort;
- years 2017/2018;
- selected Stage-1 fields;
- solar longitude or inclusive 20°–55° exclusion;
- any retained-ID criterion other than correctly parsing the already-authorized observation-year field;
- recurrent-EOM v1;
- GEO6;
- Stage-2 native geometry mapping;
- Stage-3 label interface;
- evaluator or external-validation gate.

Firewall at repair freeze:

- `valid_stage1_endpoint=false`
- `retained_ids_frozen=false`
- `raw_stage1_response_persisted=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `target_information_access=false`
- `target_region_physical_values_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
