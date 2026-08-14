# EFN Stage-1 Lsun transport diagnostic — frozen before execution

**Classification: engineering-only diagnostic after Stage-1 technical no-result; no geometry or shower-label access.**

Live Stage-1 retry 2 (`31835001724`) passed the frozen TAP schema, header-alias, and VizieR `sec/2000` date parser authorizers. The same frozen blind-index query then stopped while validating `Lsun` for fireball code `EN200318_231813`:

`invalid EFN Lsun for EN200318_231813`

Binding technical-failure provenance:

- run: `31835001724`
- job: `94879228888`
- execution head: `1c6da459f169a7762c8bbb4a04b1bd5cab10dca2`
- artifact: `9232135869`
- artifact digest: `sha256:794f5887dedec28c887ad7b0f313aba4bfcd0a4931c886ab77c5a83a936fe666`

No valid Stage-1 endpoint or retained-ID set was produced. The raw Stage-1 response was not persisted. Stage-2 geometry and Stage-3 shower labels remain unopened.

The CDS ReadMe defines `Lsun` as a fixed-width floating-point Solar Longitude J2000 field and does not mark it nullable, but it does not itself state the numeric wrap convention. Therefore no wrap/normalization or missing-value assumption is authorized from the failure alone.

## Sole authorized diagnostic

Issue the **same Stage-1 ADQL query, byte-for-byte unchanged**:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

The diagnostic may inspect only the returned blind fields `Code`, `Obs_date`, and `Lsun` and must:

1. require exactly the same CSV header;
2. require exactly 824 unique nonblank `Code` rows;
3. parse no geometry, velocity, shower, orbit, brightness, or quality field;
4. report only rows whose returned `Lsun` is non-numeric, non-finite, `<0`, or `>=360`;
5. for each invalid row, persist only `Code`, the raw `Lsun` string, and a mechanical reason category;
6. persist no raw response and no valid-row solar longitudes;
7. make no retained/excluded decision and produce no Stage-1 scientific endpoint.

This diagnostic exists only to determine whether the failure is a VizieR transport sentinel, a catalogue wrap convention, or another blind-field representation issue. Any subsequent parser repair must be separately frozen before another live Stage-1 attempt.

Firewall:

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
