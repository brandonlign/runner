# OrbitTrace CMN IAU public-interface structure audit v1 — binding result

## Verdict

`FAIL_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT`

This is a structural failure of the exact preregistered IAU MDC `OPEN` landing route, not a scientific failure of CMN and not a detector result.

## Binding provenance

- protocol freeze commit: `94e6c3889a5eeecb1811c623eaacbf7e297d92fe`
- implementation freeze commit: `debc53baafd945a7fe9d61f957b94cc7d1921671`
- workflow registration commit: `94a2c4c2331bb23dd28c68c46d30bf6e4d0ad8a2`
- first technically valid run: `31636840248`
- job: `94249188249`
- artifact ID: `9157280420`
- artifact digest: `sha256:2f232f6cd09f2c5558b680a4dbacb40919be3ff6df9cc2d782092845e33a7cb4`

## Exact outcome

One non-redirecting request was made to `https://ceres.ta3.sk/`.

- HTTP status: `200`
- final scheme/host: `https` / `ceres.ta3.sk`
- content type: `text/html`
- response SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- response body: empty
- CMN source label present: false
- form count: 0
- relevant structural links: 0
- structural query/data control present: false

## Interpretation

The official IAU MDC `OPEN` target is currently not a usable CMN structure-discovery interface under the frozen one-request protocol. This exact route is closed. No links were followed, no forms were submitted, and no scientific/event-level values were exposed.

The protocol permits a new route only if an exact CMN interface URL is obtained independently from published documentation and frozen before contact. It forbids crawling or guessing alternate endpoints from this result.

## Firewall

CMN scientific/event-level access, OrbitTrace target information/events, protected 20°–55° events, SonotaCo scientific values, MAARSY, and DMS all remained inaccessible.
