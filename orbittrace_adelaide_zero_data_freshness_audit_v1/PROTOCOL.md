# Adelaide radar zero-data scientific-freshness audit v1 — frozen protocol

## Purpose

Determine whether the Adelaide radar meteor-orbit catalogues remain scientifically unconsumed by OrbitTrace **before any Adelaide/PDS catalogue, label, readme, or event-level contact**.

This stage is repository-history only. It contains no network client and must not contact PDS, NASA, Adelaide survey data, or any meteor-event endpoint.

Independent public metadata identified two potentially useful two-year radar catalogues, `ade6061` and `ade6869`; those metadata motivate this audit only and are not contacted by the workflow.

## Fixed history indicators

Search every reachable historical patch and branch/tag/ref name case-insensitively for:

- `Adelaide`
- `ade6061`
- `ade6869`
- `Adelaide radar`
- `Adelaide Meteor`
- `ade6061.tab`
- `ade6869.tab`

Exclude only this audit's own directory/workflow/current branch from self-hits.

Require known historical `FRIPON` and `UKMON` indicators as positive controls proving the scan detects prior survey work.

## Frozen verdict

`PASS_ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT` only if:

1. no fixed Adelaide indicator appears anywhere in prior reachable history or ref names; and
2. both positive controls have historical hits.

Otherwise:

`FAIL_ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT`.

A PASS authorizes only a separately frozen official-PDS **metadata/label-only** structure audit. It does not authorize a scientific table, meteor event row, detector run, shower label, or validation result.

A FAIL closes Adelaide as a pristine external-validation route unless prior exposure can be independently proven to concern a disjoint dataset without opening new Adelaide event values.

## Firewall

The audit must record:

- `network_access=false`
- `adelaide_catalogue_access=false`
- `adelaide_label_access=false`
- `adelaide_event_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
