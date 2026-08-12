# OrbitTrace documented CMN download-interface audit v1

## Status

Frozen after:

- `PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT`;
- binding failure of the exact IAU MDC `https://ceres.ta3.sk/` landing route.

No CMN scientific/event-level catalogue record has been accessed.

This audit uses an exact CMN interface URL obtained independently from published documentation, not from crawling the failed IAU response. Published CMN-related documentation identifies the project/download host `cmn.rgn.hr` and specifically cites `http://cmn.rgn.hr/downloads/downloads.html` for CMN orbit-table material.

## Frozen transport

Initial request is exactly:

`http://cmn.rgn.hr/downloads/downloads.html`

No query string is allowed.

Redirect handling is fixed before contact:

- do not auto-follow redirects;
- if and only if the response is HTTP 301, 302, 307, or 308 and `Location` changes only the scheme from HTTP to HTTPS while preserving host `cmn.rgn.hr`, path `/downloads/downloads.html`, and an empty query, make exactly one second request to that HTTPS URL;
- all other redirects fail closed;
- no other URL is requested.

## Frozen measurements

Inspect landing-page HTML structure only. Report:

- request count, HTTP status, final scheme/host/path, content type, response SHA-256;
- whether `Croatian Meteor Network` or standalone `CMN` is present;
- form count and field names/types/action paths only;
- number of same-host or relative links with file extensions in `{zip,csv,txt,dat}`;
- extension-frequency counts only (not filenames or link query parameters);
- whether at least one candidate downloadable orbit/data file exists structurally;
- categorized relevant link counts for `orbit`, `catalog`, `data`, `download`, `query`, `search`.

Do not follow any page link or download any candidate data file. Do not emit raw HTML, filenames, event IDs, row values, per-event dates, shower labels, orbit/radiant/velocity values, or catalogue contents.

## Frozen gate

`PASS_CMN_DOCUMENTED_INTERFACE_AUDIT` requires:

1. the merged CMN freshness PASS exists;
2. the merged IAU-interface FAIL exists;
3. transport obeys the exact rule above with at most two requests;
4. final response is HTTP 200 HTML from host `cmn.rgn.hr` and path `/downloads/downloads.html`;
5. a CMN label is present;
6. at least one structurally downloadable same-host/relative `{zip,csv,txt,dat}` file link is present;
7. no candidate file is downloaded and no page link is followed;
8. no scientific/event-level content is emitted.

Failure closes this documented `cmn.rgn.hr/downloads/downloads.html` route. No URL guessing or nearby-path crawl is authorized from the outcome.

A PASS authorizes a separately frozen minimal format/header compatibility audit of exactly one deterministically selected catalogue object, with a Range/header-only strategy fixed before contact. It does not authorize detector execution, scientific shower labels, or external validation.

## Firewall

- CMN scientific/event-level access: false.
- OrbitTrace target information/events: inaccessible.
- protected 20°–55° events: inaccessible.
- SonotaCo scientific access: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
