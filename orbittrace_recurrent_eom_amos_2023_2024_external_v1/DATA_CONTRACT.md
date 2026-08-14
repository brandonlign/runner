# AMOS 2023/2024 recurrent-EOM data contract

This file is a transport/schema contract only. It does not change the scientific method or the frozen external-validation gate in `PROTOCOL.md`.

## Stage 1 — blinding index only

One file per year, complete solved multi-station sample:

- `AMOS_2023_INDEX.csv`
- `AMOS_2024_INDEX.csv`

Exact header, no extra columns:

```text
event_id,utc_time,solar_longitude_deg
```

Requirements:

- stable nonblank `event_id`, unique within and across the requested yearly sample;
- ISO-8601 UTC timestamp whose calendar year matches the file;
- finite solar longitude in `[0,360)` degrees;
- all solved multi-station meteors included, not only shower-associated events.

Only this stage is opened first. The fixed blind receipt removes inclusive solar longitude `[20.0,55.0]` and emits the retained-ID allowlist.

## Stage 2 — retained physical geometry only

After the retained-ID allowlist is returned, one file per year containing **exactly those retained IDs and no others**:

- `AMOS_2023_GEOMETRY_RETAINED.csv`
- `AMOS_2024_GEOMETRY_RETAINED.csv`

Exact header:

```text
event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s
```

Definitions required from the provider:

- `ra_j2000_deg`: geocentric radiant right ascension, J2000, degrees in `[0,360)`;
- `dec_j2000_deg`: geocentric radiant declination, J2000, degrees in `[-90,90]`;
- `vg_km_s`: geocentric speed in km/s, positive and uncorrected by any OrbitTrace-specific transform.

No orbit elements, shower codes, quality values, or protected-ID geometry belong in these files.

The already-frozen adapter maps these rows deterministically to `sol,sun_lon,ecl_lat,vg` with no fitted survey calibration.

## Stage 3 — shower associations, withheld until pretruth freeze

Do not open or supply this layer to the candidate-generation process. After `RECURRENT_EOM_AMOS_2023_2024_PRETRUTH.json` and its SHA-256 are persisted, one label file per year may be opened:

- `AMOS_2023_LABELS_RETAINED.csv`
- `AMOS_2024_LABELS_RETAINED.csv`

Exact header:

```text
event_id,shower_code
```

Requirements:

- exactly one row for every retained event ID and no other IDs;
- `shower_code` must be nonblank;
- events with no assigned shower must use the literal code `SPORADIC`;
- shower codes are treated as opaque identifiers by the evaluator;
- no radiant, velocity, orbit, quality, or target information belongs in these files.

## Execution boundary

`generate_pretruth.py` accepts only the two canonical geometry files and an output directory. It has no label argument.

`evaluate_labels.py` requires the exact pretruth SHA-256 plus the two separate retained label files. It cannot recompute candidates or ranks.

Any schema mismatch, duplicate/missing ID, protected-ID physical row, label access before pretruth freeze, or nonexact pretruth SHA is a technical no-result.

No AMOS event-level data existed or was accessed when this contract was frozen.
