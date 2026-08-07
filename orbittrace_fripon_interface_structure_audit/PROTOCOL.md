# OrbitTrace v8 external validation — FRIPON pre-scientific interface/structure audit

## Status
Frozen after FRIPON 2018/2019 passed the full-repository zero-data freshness audit and **before any FRIPON 2018 or 2019 event page, event identifier, radiant, velocity, orbit, or source/shower label is requested**.

This stage tests only whether the public guest interface has a stable structural contract that could support a later, separately frozen v8 external protocol. It is not a method evaluation and it does not authorize reserved-year access.

## Immutable freshness prerequisite
Require FRIPON freshness run `31227452342`, artifact `9012594819`, artifact ZIP SHA-256 `94f855cf860a7c48991937afeedbaf2a71905a2f1478a26e66cc50b890a3e928`, verdict `PASS_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT`, zero potential exposure hits, and both AMOR/UKMON positive controls.

## Fixed public interface sources
Exactly three FRIPON guest-mode pages may be requested:

1. `https://fireball.fripon.org/list_multiple.php`
   - public multiple-event index;
   - used only for table/list semantics, column names, HTML/script route names, and whether the initial HTML contains embedded event rows.
2. `https://fireball.fripon.org/list_pipeline.php`
   - public data-release page;
   - used only for release-policy text and published field names.
3. `https://fireball.fripon.org/displaymultiple.php?id=19701`
   - fixed non-reserved 2022 confirmed example event;
   - selected before this audit as a released 2022 example, not from 2018/2019 and not from any detector result;
   - used only to verify that the public event-detail page exposes the required **field labels** in its `Pipeline content` section.

No other event ID, date, year, search filter, fallback URL, API guess, or archive is permitted in this stage.

## Allowed inspection
The audit may inspect:
- HTTP status;
- response byte length/hash for provenance;
- HTML title/section existence;
- static table header names;
- literal PHP route basenames and script-source basenames appearing in the HTML;
- whether the initial `list_multiple.php` HTML contains zero embedded event rows;
- presence/absence of fixed textual field labels.

For the 2022 example page, the audit may test only the presence of these labels, never parse or report their values:
- `multiple id`, `multiple folder`, `multiple count`, `multiple status`;
- `orbit perifocal`, `orbit eccentricity`, `orbit inclination`, `orbit longitude`, `orbit argument`, `orbit epoch`, `orbit semiaxis`;
- `trajectory VE`, `trajectory RadianRA`, `trajectory RadianDec`.

It may also require that the page identifies itself as the fixed 2022-12-25 event and contains `Pipeline content`.

## Prohibited inspection
This stage must not:
- request any URL containing a 2018 or 2019 FRIPON event/date/filter;
- enumerate or infer any reserved-year event identifier;
- parse, convert, compare, summarize, log, or persist any numeric 2022 example-event scientific value;
- use event science to choose a field, route, threshold, quality rule, coordinate conversion, or year;
- run v8 or any comparator;
- access OrbitTrace target information.

The downloaded 2022 HTML is ephemeral and is not uploaded as an artifact.

## Structural gates
All are required:
1. all three fixed pages return HTTP 200;
2. the multiple-event index states one multiple-event per row, documents `YYYY-MM-DD hh:mm:ss`, and exposes the public columns ID/event date/count/status/stations;
3. its initial HTML has no embedded data rows, preventing accidental current/reserved event-value inspection in this structure audit;
4. the data-release page states yearly releases from 2021 onward and names orbital parameters, pre-atmospheric speed, and radiant output;
5. the fixed 2022 event page contains the expected 2022 event header and `Pipeline content`;
6. every fixed required pipeline field label above is present;
7. no reserved-year FRIPON request was made;
8. no scientific value, source/shower label, detector result, or OrbitTrace target information was interpreted.

## Decision
- `PASS_FRIPON_PUBLIC_INTERFACE_STRUCTURE_AUDIT` if all structural gates pass.
- `FAIL_FRIPON_PUBLIC_INTERFACE_STRUCTURE_AUDIT` if any structural gate fails.
- HTTP/transport failures remain explicit interface failures and do not authorize alternate event IDs or routes.

A pass establishes field/interface structure only. **It does not yet establish a deterministic bulk enumeration transport for 2018/2019, nor that `trajectory VE`/`RadianRA`/`RadianDec` are scientifically interchangeable with v8's geocentric input geometry.** Those two issues must be resolved from public interface source/documentation and non-reserved data before the first reserved-year scientific access.
