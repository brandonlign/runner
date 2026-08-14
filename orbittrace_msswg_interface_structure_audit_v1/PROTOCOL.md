# MSSWG official-interface structure audit v1 — frozen protocol

## Authorization

Authorized only because the repository-history freshness audit passed before any MSSWG network/data contact:

- run `31832150805`;
- artifact `9231082708`;
- artifact digest `sha256:d14ebd728155c618a8e77398189503be12b30c61249042930e6c362e83f33dc1`;
- verdict `PASS_MSSWG_ZERO_DATA_REPO_FRESHNESS_AUDIT`.

## Sole network contact

Make exactly one HTTP GET to the independently documented official IMO page:

`https://www.imo.net/observations/methods/video-observation/data/`

No other host/path is permitted. Redirects produced by that exact request may be followed by the HTTP library, but the audit may not issue a second application-level request.

## Allowed inspection

Inspect only the returned HTML structure needed to identify anchors whose normalized visible text is exactly:

- `readme`
- `msswg.txt`

Record:

- HTTP status;
- final URL after automatic redirects;
- response byte length and SHA-256;
- for those two exact anchor texts only: raw `href` and `urljoin`-resolved URL.

Do not record page prose beyond the two anchor labels. Do not follow either link. Do not inspect headers/content from the readme or catalogue targets.

## Frozen gate

`PASS_MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT` only if:

1. the one official-page GET returns HTTP 200;
2. exactly one `readme` anchor and exactly one `msswg.txt` anchor are found;
3. both resolve to HTTP(S) URLs;
4. the resolved targets are distinct;
5. no target request is made.

Otherwise `FAIL_MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT`; exact route closes without URL guessing or neighboring-path rescue.

A PASS authorizes only a separately frozen **readme-only** audit of the exact discovered readme URL. It does not authorize the catalogue target.

## Firewall

- `msswg_catalogue_access=false`
- `msswg_readme_access=false`
- `msswg_event_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
