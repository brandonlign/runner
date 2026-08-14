# NASA ASFN zero-data freshness audit v1 — binding adjudication

**Classification: POSITIVE event-level freshness after disjoint-identifier adjudication. Preserve the raw audit FAIL unchanged.**

Binding raw audit:

- run `31833031981`;
- artifact `9231416220`;
- artifact digest `sha256:2a53b72c6360e545c8b376cc595ec4bb805424bb88a059712e761178204c2733`;
- raw verdict `FAIL_NASA_ASFN_ZERO_DATA_REPO_FRESHNESS_AUDIT`.

## Exact cause of raw FAIL

All network/release-specific indicators had zero historical hits:

- `NASA All Sky Fireball Network`: 0
- `All Sky Fireball Network`: 0
- `fireballs.ndc.nasa.gov`: 0
- `Seven Years of Bright Meteor Data`: 0
- `Kingery`: 0
- `meteoroids2022_poster_kingery`: 0
- matching ref names: 0

The sole failing indicator was the generic software name `ASGARD`.

## Disjointness proof

The historical `ASGARD` occurrences are in OrbitTrace literature-comparator records for the **Sugar et al. uncertainty pipeline on SonotaCo data**. For example:

- `orbittrace_literature_matched_v8/PROTOCOL.md` says the frozen Sugar comparator is a SonotaCo 2023/2025 transfer and explicitly states: `This is a faithful published-stage survey transfer, not an exact ASGARD covariance/software reproduction, because SonotaCo supplies marginal uncertainties.`
- `orbittrace_literature_matched_v8/COMPETITOR_FREEZE.json` records SonotaCo 2023/2025 Sugar runs and the scope note: `full published-stage survey transfer using SonotaCo marginal uncertainties; not exact ASGARD covariance/software reproduction`.

These hits concern the name of external reduction/software methodology in a **different SonotaCo dataset**. They do not identify, download, parse, score, or scientifically inspect NASA All Sky Fireball Network events.

The frozen raw protocol allowed recovery from a FAIL only if the prior exposure could be independently proven to concern a disjoint dataset without new ASFN event-value access. That condition is satisfied by the preserved historical files themselves; no NASA event data is needed for the proof.

## Corrected scientific status

`PASS_NASA_ASFN_EVENT_LEVEL_FRESHNESS_AFTER_DISJOINT_ASGARD_IDENTIFIER_ADJUDICATION`

This does **not** rewrite the raw fixed-pattern result. The historical result remains `FAIL_NASA_ASFN_ZERO_DATA_REPO_FRESHNESS_AUDIT`; its single `ASGARD` hit is classified as a false-positive dataset identifier collision.

Authorized next step: a separately frozen **official NASA interface/documentation-only audit**. Event pages, event files, bulk catalogue bytes, shower labels, detector execution, and validation remain forbidden until separately frozen gates authorize them.

## Firewall

- `network_access_by_history_audit=false`
- `new_asfn_event_data_access=false`
- `new_asfn_bulk_catalogue_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
