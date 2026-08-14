# MSSWG zero-data scientific-freshness audit v1 — frozen protocol

## Purpose

Determine whether the Japanese Meteor Science Seminar Working Group (MSSWG) Orbit Database remains scientifically unconsumed by OrbitTrace **before any MSSWG catalogue/readme/event-level contact**.

This audit is repository-history only. It contains no network client and must not contact IMO, MSSWG, or any catalogue endpoint.

The candidate external source is independently documented by IMO as a multi-station meteor-orbit database spanning 1983-01-03 through 2009-10-21. Those external metadata motivate the audit but are not accessed by this workflow.

## Fixed history indicators

Search every reachable historical patch and branch/tag/ref name for these case-insensitive indicators:

- `MSSWG`
- `Meteor Science Seminar Working Group`
- `msswg.txt`
- `/msswg/`
- `files/data/msswg`

Exclude only this audit's own directory/workflow/current branch from self-hits.

Require known historical `FRIPON` and `UKMON` indicators as positive controls proving the scan can detect prior survey work.

## Frozen verdict

`PASS_MSSWG_ZERO_DATA_REPO_FRESHNESS_AUDIT` only if:

1. no fixed MSSWG indicator appears anywhere in prior reachable history/ref names; and
2. both positive controls have historical hits.

Otherwise:

`FAIL_MSSWG_ZERO_DATA_REPO_FRESHNESS_AUDIT`.

A PASS authorizes **only** a separately frozen structure-only audit of the official IMO MSSWG landing/link metadata and then, if available, a separately frozen readme/schema audit. It does not authorize `msswg.txt`, event rows, detector execution, shower labels, or validation.

A FAIL closes MSSWG as a pristine external-validation route unless the historical exposure can be independently proven to concern a disjoint dataset without opening new MSSWG event values.

## Firewall

This workflow must record:

- `network_access=false`
- `msswg_catalogue_access=false`
- `msswg_readme_access=false`
- `msswg_event_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
