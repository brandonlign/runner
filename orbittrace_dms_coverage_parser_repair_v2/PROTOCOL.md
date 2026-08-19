# OrbitTrace DMS coverage-only parser repair v2

## Status

**FROZEN BEFORE THE FIRST COVERAGE RESULT PRODUCED BY THIS EXACT V2 REPAIR.**

The parent DMS coverage-only audit and parser-repair v1 both remain scientific no-results. The parent failed before a coverage statistic because the current official DMS ZIP uses a DMS-specific compact 42-column/two-header-row schema rather than the generic MDC webpage order. Repair v1 then failed before parsing any data row because its solar-longitude header alias set did not match the compact DMS header spelling. No per-year row count, solar-longitude coverage statistic, eligibility gate, or reserved pair has yet been observed.

All diagnostics preceding v2 were limited to archive/member structure, header strings, and the already-authorized coverage fields. They did not interpret radiant, velocity, orbital-element, shower-label, or OrbitTrace-target values.

## Frozen parent logic

Exact parent:
- `orbittrace_v15_dms_coverage_eligibility_v1/audit_coverage.py`
- Git blob `8e519aa54b8f45e5fecc5d81cb4c20f2d5178685`

V2 reuses unchanged:
- official DMS archive discovery;
- allowed-value parsing for only Yr/Mn/Day/LS;
- inclusive target exclusion `[20°,55°]`;
- year gates: >=80 target-excluded rows, >=12 occupied 10° solar-longitude bins, >=3 occupied quadrants;
- earliest eligible consecutive-pair selection;
- all scientific-firewall flags.

## Sole v2 schema repair

The current official archive is required to satisfy every zero-value structural invariant established before this freeze:
- exactly one non-directory text member;
- UTF-8/UTF-8-SIG;
- semicolon-separated;
- exactly 910 nonblank rows;
- constant width 42;
- exactly two header rows followed by the public 908 DMS records.

For this compact DMS schema, the four coverage-only columns are fixed before the result to zero-based indices:
- `year = 2`
- `month = 3`
- `day = 4`
- `solar_longitude = 6`

This positional binding is guarded only by header metadata:
- column 2 must normalize to `yr` or `year` in one of the two header rows;
- column 3 must normalize to `mn` or `month`;
- column 4 must normalize to `day` or `decday`;
- column 5 must normalize to `n` in the compact archive;
- column 7 must normalize to `mv` or `mvmax`.

The public IAU MDC video-catalog parameter documentation places solar longitude (`LS`) between date fields and magnitude. Combined with the observed compact DMS header sequence `Yr, Mn, Day, N, [solar-longitude field], mv`, column 6 is therefore frozen as LS without using a DMS data-row value to choose it.

No other cell in any DMS data row may be interpreted, converted, compared, logged, summarized, or used for validation.

## Binding outcome

The first technically valid v2 coverage result is binding and may only be:
- `ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE`, with the unchanged parent-selected consecutive pair; or
- `INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR`.

A valid eligible result reserves that pair before DMS radiant, velocity, orbit, or shower-label values are opened. Any event-level method transfer must be frozen separately before scientific-field access.

## Firewall

Forbidden here:
- RA/DEC or any radiant value;
- Vg/Vi/Vh or any velocity value;
- q/e/a/i/arg/nod or any orbital element;
- shower labels/classes;
- D-criteria or stream matching;
- OrbitTrace target information;
- any method or comparator execution;
- SonotaCo/GMN/MAARSY/AMOS scientific rows.

V2 is a schema/transport repair only and cannot itself support a performance claim.
