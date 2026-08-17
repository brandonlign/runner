# EFN 2017/2018 VizieR schema freeze — metadata only

**Classification: engineering-only preaccess metadata freeze. No EFN event row has been queried or opened.**

This file resolves the exact VizieR table/column interface allowed by the scientific protocol frozen at commit `fb2f3bd14149f0fdccb128d406d87b89bf336dcd` and the source-pin correction recorded in `SOURCE_PIN_REPAIR.md`.

## Official catalogue identity

Official CDS/VizieR metadata for `J/A+A/667/A157` resolves the one data table as:

`J/A+A/667/A157/catalog`

VizieR reports it as “Fireball data (824 rows)”. The CDS ReadMe independently reports `catalog.dat` with 824 records.

The TAP/ADQL table identifier must therefore be quoted because it contains special characters:

`"J/A+A/667/A157/catalog"`

No alternate table/release is authorized.

## Exact VizieR column interface

The official VizieR table metadata exposes the detector/evaluator fields under these identifiers:

- `Code` — Fireball code
- `Obs.date` — VizieR observation date/time field
- `Lsun` — Solar Longitude J2000
- `Lgeo-Lsun` — ecliptic longitude of geocentric radiant minus Solar Longitude
- `Bgeo` — ecliptic latitude of geocentric radiant
- `Vgeo` — geocentric velocity
- `Shower` — possible IAU meteor-shower code

Columns containing `.` or `-` must be quoted in ADQL. Therefore use `"Obs.date"` and `"Lgeo-Lsun"`.

## Preaccess Stage-1 transport repair

The catalogue ReadMe describes fixed-width `Obs.date` and `Obs.time` fields separately, but the VizieR query-table metadata exposes them through a combined observation timestamp field named `Obs.date`; there is no separate query-table `Obs.time` column in the official VizieR table metadata.

The original protocol's Stage-1 query listed:

`Code, Obs.date, Obs.time, Lsun`

That query cannot be expressed against the actual VizieR table interface as written. Before any event access, the authorized transport-only repair is:

`Code, "Obs.date", Lsun`

This does not change any scientific input. Recurrent-EOM uses only the calendar year parsed from the observation timestamp and `Lsun` for the blind exclusion; time-of-day never enters GEO6, clustering, ranking, truth, or the gate.

No other Stage-1 column may be returned.

## Frozen staged ADQL shapes

These are query **shapes** frozen before event access. The execution program must URL/form-encode them without changing selected columns or filters.

### Stage 1 — blind index

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

Requirements after return remain exactly as frozen scientifically:

- exactly 824 rows;
- unique nonblank Code;
- calendar year from `Obs.date` is only 2017 or 2018 and both years are nonempty;
- finite Lsun in [0,360);
- inclusive 20.0 <= Lsun <= 55.0 exclusion;
- only retained-ID hashes/counts may authorize Stage 2.

### Stage 2 — retained physical geometry

```sql
SELECT Code, "Obs.date", Lsun, "Lgeo-Lsun", Bgeo, Vgeo
FROM "J/A+A/667/A157/catalog"
WHERE Lsun < 20.0 OR Lsun > 55.0
```

No protected-row physical value may be returned by the server. Returned Code IDs must equal the Stage-1 retained allowlist exactly.

### Stage 3 — post-pretruth labels only

```sql
SELECT Code, Shower
FROM "J/A+A/667/A157/catalog"
WHERE Lsun < 20.0 OR Lsun > 55.0
```

Stage 3 remains forbidden until the complete vanilla/recurrent candidate payload and ranking are persisted and SHA-256 frozen.

## Promoted source identity correction

The authoritative promoted recurrent-EOM implementation Git blob remains:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

The malformed source-pin string in the original protocol is superseded only for provenance by `SOURCE_PIN_REPAIR.md`; no method byte or scientific setting changes.

## Metadata sources inspected

Only CDS/VizieR catalogue metadata/ReadMe pages were inspected. No query selecting from `"J/A+A/667/A157/catalog"` has been executed by OrbitTrace at the time of this freeze.

## Firewall state at freeze

- `efn_event_rows_accessed=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
