# NASA ASFN primary-paper bulk HEAD audit v1 — frozen protocol

Authorized by primary-publication PASS run `31834078469`, artifact `9231801482`, which independently documented the exact bulk target:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

Make exactly one application-level HTTP `HEAD` request to that exact URL. Automatic redirects from this request may be followed. Do not issue GET or range requests and do not read ZIP/event bytes.

Record only status, final URL, redirect history, and `Content-Type`, `Content-Length`, `Last-Modified`, `ETag`, `Accept-Ranges`, and `Content-Disposition` headers if present.

`PASS_NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT` only if the final response is HTTP 200 and metadata are consistent with a downloadable ZIP object. Otherwise `BLOCKED_NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT`.

A PASS authorizes only a separately frozen archive/readme-only acquisition step: the ZIP may be downloaded, but only archive listing and `nasfn_2013-2019_readme.txt` may be inspected; `nasfn_2013-2019_data.txt` event rows remain forbidden until another protocol is frozen.

Firewall: `asfn_bulk_body_access=false`, `asfn_event_value_access=false`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`.
