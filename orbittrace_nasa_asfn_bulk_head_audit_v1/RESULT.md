# NASA ASFN primary-paper bulk HEAD audit v1 — result

**Classification: POSITIVE preaccess transport result. No ASFN body/event byte was read.**

Binding run: `31834401468`  
Artifact: `9231911063`  
Artifact digest: `sha256:fe4219dfb77b9f12c81cbc63e0dabf953393d216afebe031604f0ae78197958b`

Exact primary-paper target:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

One HEAD request returned:

- HTTP `200`
- final URL unchanged
- no redirects
- `Content-Type: application/zip`
- `Content-Length: 4326351`
- `Accept-Ranges: bytes`
- `Last-Modified: Fri, 05 Mar 2021 19:58:24 GMT`
- `ETag: "4203cf-5bccf81bbe455"`

Verdict: `PASS_NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT`.

The next authorized step is the already-preregistered archive/readme-only acquisition: the exact ZIP may be downloaded, but only its file listing and `nasfn_2013-2019_readme.txt` may be inspected. `nasfn_2013-2019_data.txt` event rows remain forbidden until a new scientific protocol is frozen.

Firewall: `asfn_bulk_body_access=false`, `asfn_event_value_access=false`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`.
