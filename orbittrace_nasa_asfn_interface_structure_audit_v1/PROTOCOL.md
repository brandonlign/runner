# NASA ASFN official-interface structure audit v1 — frozen protocol

## Authorization

Authorized after the zero-data history audit plus disjoint-identifier adjudication established no prior OrbitTrace scientific/event-level use of NASA All Sky Fireball Network data:

- raw audit run `31833031981`, artifact `9231416220`, digest `sha256:2a53b72c6360e545c8b376cc595ec4bb805424bb88a059712e761178204c2733`;
- adjudication commit `8f32e47b61534a3bb073e2b8edcccf486b372cb4`;
- the only historical hit was the generic software name `ASGARD` in SonotaCo Sugar-comparator records, while every NASA-network/release-specific indicator had zero hits.

## Sole network contact

Make exactly one application-level GET to the official NASA MEO page:

`https://www.nasa.gov/meteoroid-environment-office/all-sky-fireball-network/`

No fireball event page, spreadsheet, text file, network date page, API, or second URL is authorized. Automatic redirects caused by this exact request may be followed.

## Allowed inspection

Inspect only anchor structure sufficient to record:

1. anchors whose normalized visible text is exactly `Orbit Table`;
2. anchors whose resolved host is exactly `fireballs.ndc.nasa.gov` and whose path does not contain `/events/` or an 8-digit date page.

Record status/final URL/response SHA-256 and only the matching anchor text + href + resolved URL. Do not preserve page prose or follow any discovered link.

## Frozen gate

`PASS_NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT` only if:

- official page returns 200;
- exactly one `Orbit Table` anchor is present;
- at least one non-event network-site anchor resolves to `fireballs.ndc.nasa.gov`;
- all discovered targets use HTTP(S);
- `target_requests_made=false`.

Otherwise `FAIL_NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT`; no URL guessing or neighboring-path rescue.

A PASS authorizes only a separately frozen documentation/schema adjudication. It does not authorize Orbit Table bytes or any event values.

## Firewall

- `asfn_event_data_access=false`
- `asfn_bulk_catalogue_access=false`
- `orbit_table_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
