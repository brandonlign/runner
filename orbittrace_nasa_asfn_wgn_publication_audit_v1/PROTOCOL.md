# NASA ASFN WGN publication-only availability audit v1 — frozen protocol

## Purpose

Determine whether the primary Kingery et al. WGN publication independently documents an accessible bulk location or release format for the 2013–2019 NASA All Sky Fireball Network dataset, without contacting any ASFN event file/site endpoint.

The publication is independently identified as:

A. Kingery, D. E. Moser, W. J. Cooke, and A. V. Moorhead (2020), `Seven years of bright meteor data from the NASA All Sky Fireball Network`, WGN 48:3, pp. 60–68.

IMO's official WGN archive page independently exposes the exact public 2020 archive link:

`https://www.imo.net/files/wgn/WGN%202020.zip`

## Sole permitted network object

Download exactly that official WGN 2020 ZIP archive. Do not request `fireballs.ndc.nasa.gov`, NASA event pages, spreadsheets, APIs, guessed data URLs, or any link discovered inside the paper.

## Allowed publication inspection

Unzip the archive locally. Use `pdftotext` only on PDFs inside the archive to identify the issue containing the exact normalized title phrase:

`Seven years of bright meteor data from the NASA All Sky Fireball Network`

Exactly one issue PDF must match.

From that matching issue, preserve:

- archive ZIP SHA-256 and file listing;
- matching issue filename and SHA-256;
- extracted full issue text for later local publication review;
- a deterministic excerpt report consisting only of lines within ±4 lines of matches to these fixed case-insensitive tokens: `data release`, `available`, `availability`, `download`, `database`, `website`, `fireballs.ndc.nasa.gov`, `supplement`, `catalog`, `catalogue`, `repository`, `33,660`, `33660`.

No discovered URL is followed. No event-data object is contacted.

## Frozen gate

This stage is publication-documentation only.

`PASS_NASA_ASFN_WGN_BULK_RELEASE_DOCUMENTED` only if the primary paper text itself identifies a concrete bulk-data object/location or an unambiguous retrieval procedure for the released 2013–2019 catalogue that can be frozen before scientific bytes are contacted.

`BLOCKED_NASA_ASFN_WGN_BULK_RELEASE_NOT_DOCUMENTED` if the paper describes the release but does not provide such a concrete bulk retrieval location/procedure.

Any ambiguous statement such as only naming the live fireball website, without a documented bulk 2013–2019 retrieval object, is a BLOCKED outcome.

A PASS authorizes only a separately frozen structure/HEAD/schema audit of the exact independently documented target. It does not authorize event bytes or detector execution.

## Firewall

- `wgn_publication_access=true`
- `asfn_event_data_access=false`
- `asfn_bulk_catalogue_access=false`
- `fireballs_site_access=false`
- `discovered_links_followed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
