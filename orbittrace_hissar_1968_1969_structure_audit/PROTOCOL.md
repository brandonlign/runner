# OrbitTrace Hissar 1968/1969 pre-scientific interface/transport audit

## Status
Frozen after `PASS_HISSAR_1968_1969_ZERO_DATA_FRESHNESS_ADJUDICATION` and before any IAU MDC catalogue form submission or meteor-row access.

Freshness prerequisite:
- run `31227612252`;
- job `93024960168`;
- artifact `9012644763`;
- artifact ZIP SHA-256 `31f50436e7dfad5a2768d12e559942a1ee5dd0f96816d71226151ed381701598`;
- raw conservative freshness FAIL preserved, exactly one metadata-only explicit-nonuse hit, zero additional hits forgiven.

## Allowed network access
Exactly two fixed GET resources may be contacted:
1. `https://ceres.ta3.sk/iaumdcdb/home/catalog/radio`
2. `https://ceres.ta3.sk/iaumdcdb/public/docs/HISSAR_documentation.pdf`

The audit may inspect only HTML form/control structure and the official Hissar documentation. It must not submit any HTML form, follow any catalogue-result/download action, request Hissar rows, or inspect scientific event values.

## Official interface facts required
The documentation/page must establish prospectively:
- Hissar is a radio-meteor catalogue with 8,916 records;
- observing span covers December 1968 through 1969;
- positional parameters are referred to equinox J2000.0/2000.0;
- `LS` is solar longitude;
- `RA`,`DEC` are geocentric radiant coordinates;
- `Vg` is geocentric velocity;
- `q`,`e`,`i`,`arg`,`nod` are available orbital elements;
- `#IC` is the unique IAU MDC identification code;
- a reduced single-line format exists with one meteor per line, and the spreadsheet format also contains the required discovery/orbital fields.

## Structure/transport inspection
Parse the public radio page without submitting it. Record:
- form count;
- each form's method/action only;
- control names/types;
- select/checkbox/radio option values and non-scientific labels;
- whether the form exposes Hissar selection, year/date limits, required parameter selectors, and a deterministic submission action/method.

Do not store the raw page or PDF in the artifact; hash them and delete them after the audit.

## PASS gates
PASS only if:
1. both fixed GETs succeed;
2. the official documentation establishes all required interface facts above;
3. the radio page exposes Hissar and the expected parameter names `Yr`, `Mn`, `Day`, `LS`, `RA`, `DEC`, `Vg`, `q`, `e`, `i`, `arg`, `nod`, plus identification fields `DB` and `IC`;
4. at least one form exists and its method/action/control schema can be frozen without submitting it;
5. no result/data/download form action is invoked;
6. no meteor row or scientific value is accessed.

FAIL is terminal for Hissar transport/interface under this validation track. Do not infer missing mechanics by submitting test queries.

A PASS authorizes freezing the complete scientific v8 external protocol before the first catalogue submission. It is not a power or performance result.
