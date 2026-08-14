# NASA ASFN Orbit Table HEAD-only metadata audit v1 — frozen protocol

Authorized by official-interface structure run `31833300121`, artifact `9231515664`, digest `sha256:1c879bd0f10a74fa98447cd80c38aa4e6b51dbd1f9fcfe52c0075cdf3ea7e832`, which discovered but did not follow:

`https://www.nasa.gov/xls/523317main_Orbit_Table.xls`

Make exactly one HTTP `HEAD` request to that exact URL. Automatic redirects are allowed. Do not issue GET/range requests and do not read spreadsheet bytes.

Record only status, final URL, redirect history, and response headers `Content-Type`, `Content-Length`, `Last-Modified`, `ETag`, `Content-Disposition` if present.

This stage has no scientific PASS/FAIL. Its sole role is to determine whether the official target metadata is consistent with the independently documented 2013–2019 33,660-event release or appears to be a separate/legacy object. Any scientific-data GET requires a separately frozen protocol.

Firewall: `orbit_table_body_access=false`, `asfn_event_data_access=false`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`.
