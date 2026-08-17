# NASA ASFN archive readme-only preaccess v1 — frozen protocol

Authorized only after primary-paper publication PASS (`31834078469`) and exact bulk HEAD PASS (`31834401468`).

## Exact archive

Download exactly once:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

Expected HEAD metadata from the binding prior stage: HTTP 200, `Content-Type: application/zip`, `Content-Length: 4326351`, ETag `"4203cf-5bccf81bbe455"`.

## Allowed body handling

The ZIP body may be downloaded and SHA-256 frozen. This stage may inspect only:

1. ZIP central-directory file names, compressed/uncompressed sizes, and timestamps;
2. the exact documentation member whose basename is `nasfn_2013-2019_readme.txt`.

The scientific member whose basename is `nasfn_2013-2019_data.txt` must **not** be extracted, streamed with `unzip -p`, read, grepped, counted by newline, sampled, hashed separately, or otherwise inspected. Its central-directory metadata only may be recorded.

The readme may be preserved in full and inspected for field names, units, missing-value conventions, row format, event identifier/date format, shower-label definition, and any quality flags. No discovered URL is followed.

## Frozen gate

`PASS_NASA_ASFN_README_RECURRENT_EOM_PREACCESS` only if the archive contains exactly one readme member and one data member with the expected basenames and the readme alone documents a deterministic row parser plus recurrent-EOM's required solar longitude, geocentric radiant, and geocentric speed channels without event-informed calibration.

Otherwise `FAIL_NASA_ASFN_README_RECURRENT_EOM_PREACCESS`; scientific data member remains unopened.

A PASS authorizes only freezing a complete ASFN scientific evaluation protocol **before the first data-row inspection**.

## Firewall

- `asfn_archive_download=true`
- `asfn_data_member_extracted=false`
- `asfn_event_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
