# MSSWG readme-only schema audit v1 — frozen protocol

## Authorization

Authorized only after two preaccess stages passed:

1. zero-data repo freshness: run `31832150805`, artifact `9231082708`, digest `sha256:d14ebd728155c618a8e77398189503be12b30c61249042930e6c362e83f33dc1`;
2. official-interface structure: run `31832289541`, artifact `9231133489`, digest `sha256:d17a8089da4462e54fb6d6dc7f99387e90e4d5263ae4a17fb2bb5efc71af7d40`, verdict `PASS_MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT`.

The structure audit discovered exactly one readme target:

`http://www.imo.net/files/data/msswg/readme`

and separately one catalogue target:

`http://www.imo.net/files/data/msswg/msswg.txt`

The catalogue target remains forbidden in this stage.

## Sole network contact

Make exactly one application-level GET to the exact discovered readme URL. Automatic redirects from that request may be followed. Do not issue HEAD/GET/range requests to `msswg.txt` or any neighboring path.

## Allowed inspection

The readme is documentation rather than meteor-event data. Preserve its exact returned bytes and SHA-256, and produce a deterministic text/schema report containing:

- status/final URL/byte count;
- decoded readme text;
- line count;
- lines containing any of these fixed case-insensitive schema tokens: `date`, `time`, `solar`, `longitude`, `radiant`, `ra`, `dec`, `velocity`, `vg`, `orbit`, `shower`, `code`, `format`, `column`.

No scientific/event catalogue row is authorized.

## Frozen compatibility gate

`PASS_MSSWG_README_RECURRENT_EOM_INPUT_COMPATIBILITY` only if the readme itself documents enough information to deterministically recover, without fitted/calibrated transformations:

1. observation epoch/date-time sufficient to compute solar longitude;
2. a geocentric radiant direction or explicitly documented coordinates transformable to it;
3. geocentric speed `Vg` or an exactly documented geocentric equivalent;
4. a row format that allows individual meteor records to be parsed;
5. no readme-defined ambiguity requiring an event-value-informed calibration.

Otherwise `FAIL_MSSWG_README_RECURRENT_EOM_INPUT_COMPATIBILITY` and the catalogue remains unopened.

A PASS authorizes only a separately frozen **catalogue metadata/coverage preaccess** step. It does not yet authorize detector execution, labels, target information, or validation.

## Firewall

- `msswg_catalogue_access=false`
- `msswg_event_value_access=false`
- `msswg_readme_access=true`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
