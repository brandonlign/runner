# NASA ASFN Orbit Table HEAD-only audit v1 — result

**Classification: NEUTRAL / BLOCKED. No orbit-table body or event value was read.**

Binding run: `31833533986`  
Artifact: `9231600320`  
Artifact digest: `sha256:33baddfe5666be96b1c96e05fb2be7111596c6bb1698338b1141fd7682816a74`

The exact official NASA page target discovered by the prior structure audit was:

`https://www.nasa.gov/xls/523317main_Orbit_Table.xls`

The frozen audit made one application-level `HEAD` request only. Result:

- HTTP status: `404`
- final URL unchanged
- redirect history: empty
- `Content-Type: text/html; charset=UTF-8`
- no `Content-Length`, `Last-Modified`, `ETag`, or `Content-Disposition` metadata identifying a live spreadsheet
- `orbit_table_body_access=false`
- `asfn_event_data_access=false`

## Binding consequence

The current official NASA `Orbit Table` route is dead and does not authorize a bulk-data GET.

Do not rescue this result by guessing a changed spreadsheet filename, neighboring `/xls/` object, archived URL, or alternate scheme based on the 404. Any independently documented 2013–2019 bulk-release location must be established from a primary publication/documentation source before scientific data contact.

Verdict:

`BLOCKED_NASA_ASFN_OFFICIAL_ORBIT_TABLE_EXACT_TARGET_404`

This is not evidence for or against recurrent-EOM HDBSCAN performance. The 2013–2019 ASFN event release remains scientifically unconsumed by this route.

## Firewall

- `orbit_table_body_access=false`
- `asfn_event_data_access=false`
- `asfn_bulk_catalogue_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
