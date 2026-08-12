# OrbitTrace CMN public-interface structure audit v1

## Status

Frozen after the binding `PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT` and before any Croatian Meteor Network scientific/event-level record is accessed.

This audit may contact exactly one public landing endpoint: the IAU Meteor Data Center orbital-database `OPEN` target identified by the official IAU MDC landing page, `https://ceres.ta3.sk/`. It may inspect HTML/interface structure only. It may not follow links, submit forms, issue catalogue queries, or parse/output scientific row values.

## Purpose

Determine whether the fresh CMN catalogue is structurally reachable through a public orbital-database interface in a way that could support a later separately frozen compatibility audit without bulk blind data exposure.

## Frozen measurements

From the single HTTP response only, report:

- HTTP success and final HTTPS host;
- response content type and SHA-256;
- whether the page contains a CMN source label (`Croatian Meteor Network` or standalone `CMN`, case-insensitive);
- form count;
- form field names/types only;
- form action paths only, with query strings removed;
- link paths/text categories only when the link text or path contains `orbit`, `catalog`, `data`, `download`, `query`, or `search`;
- whether at least one query/download/search structural control exists.

Raw HTML, table cells, numerical scientific values, event identifiers, source counts, dates attached to individual meteors, shower labels, orbital/radiant/velocity values, and query results must not be written to the artifact or logs.

## Frozen gate

`PASS_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT` requires all of:

1. the prior merged freshness result exists and says `PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT`;
2. exactly one network fetch is made, to `https://ceres.ta3.sk/` with no query string;
3. final scheme is HTTPS and final host is `ceres.ta3.sk`;
4. HTTP status is 200 and HTML is returned;
5. a CMN source label is present on the landing response;
6. at least one form or relevant structural link indicates a search/query/download/data-access interface;
7. no link is followed and no form is submitted;
8. no scientific/event-level values are emitted.

Failure closes this exact IAU-MDC landing-interface route for CMN. Do not rescue it by crawling alternate endpoints or guessing URLs from the outcome. A failure may only motivate a new source from independently published interface documentation, frozen before contact.

A PASS authorizes only a separately frozen **field-compatibility audit** with a minimal fixed metadata/schema request. It does not authorize detector execution, shower-label use, or scientific evaluation.

## Firewall

- CMN scientific/event-level access: false.
- OrbitTrace target information/events: inaccessible.
- Protected 20°–55° target region: inaccessible.
- SonotaCo scientific access: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- External validation performed: false.
