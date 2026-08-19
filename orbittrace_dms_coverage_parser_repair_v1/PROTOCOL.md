# OrbitTrace DMS coverage-only parser repair v1

## Status

**FROZEN BEFORE THE FIRST COVERAGE RESULT PRODUCED BY THIS REPAIR.**

The previously frozen DMS1991-1998 coverage-only audit failed technically on the current official IAU MDC ZIP before producing any coverage statistic. The failure occurred because the current archive uses one semicolon-separated 42-column member with two header rows followed by the already-public 908 DMS records, while the old parser's named-header/headerless schema detector did not recognize that two-row header layout.

Two diagnostics were run after that technical no-result. They accessed only file/member structure, header strings, and the four already-authorized coverage fields (`Yr`, `Mn`, `Day`, `LS`). They did not access radiant, velocity, orbital elements, shower labels, or OrbitTrace target information. The diagnostics established only that the archive has one member, 910 nonblank semicolon rows of width 42, and that the old generic fixed positions no longer correspond to `Yr/Mn/Day/LS` because the DMS-specific column layout differs from the generic MDC webpage ordering.

This repair changes **only schema resolution**. It does not change any coverage threshold, pair-selection rule, sealed interval, or scientific authorization.

## Immutable parent logic

Parent source:
- branch `agent/orbittrace-v15-dms-coverage-eligibility-run-v5`
- `orbittrace_v15_dms_coverage_eligibility_v1/audit_coverage.py`
- Git blob `8e519aa54b8f45e5fecc5d81cb4c20f2d5178685`

The repaired runner imports this exact parent and reuses unchanged:
- official page/archive discovery;
- allowed-value parser;
- target exclusion `[20°,55°]` inclusive;
- per-year coverage statistics;
- year eligibility gates (`>=80` target-excluded rows, `>=12` occupied 10° bins, `>=3` occupied quadrants);
- deterministic consecutive-pair selection;
- output/firewall flags.

## Sole repair

Replace only `choose_data_member(archive)` with a deterministic two-row semantic-header resolver:

1. require exactly one non-directory `.csv`, `.txt`, or `.dat` member;
2. require UTF-8/UTF-8-SIG decoding;
3. parse semicolon-separated nonblank rows;
4. require exactly 910 nonblank rows, constant width 42, and therefore exactly two header rows plus the public 908-record DMS catalogue;
5. inspect **header strings only** in rows 0 and 1;
6. for each allowed concept resolve exactly one column whose normalized short or long header matches:
   - year: `yr` or `year`;
   - month: `mn` or `month`;
   - day: `day` or `decday`;
   - solar longitude: `ls`, `solarlongitude`, or `solarlon`;
7. require the four resolved indices to be distinct;
8. set data start to row 2 and pass only those indices to the unchanged parent coverage parser.

No data-row value outside the four resolved columns may be interpreted, converted, compared, logged, summarized, or used for validation.

## Binding coverage result

The first technically valid result from this repaired coverage-only parser is binding. It may produce only:
- `ELIGIBLE_DMS_PAIR_RESERVED_PRE_SCIENCE`, with the deterministic parent-selected consecutive pair; or
- `INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR`.

If eligible, the pair is reserved before DMS scientific fields are opened. A later external-transfer protocol must be frozen separately before accessing radiant, velocity, orbital elements, or shower labels.

## Firewall

Forbidden in this coverage repair:
- RA/DEC or any radiant quantity;
- Vg/Vi/Vh or any velocity quantity;
- q/e/a/i/arg/nod or any orbital element;
- shower labels or classifications;
- D-criteria or shower matching;
- OrbitTrace target information;
- SonotaCo, GMN scientific rows, MAARSY, AMOS, or any method/comparator execution.

This is a transport/schema repair only and cannot support a scientific performance claim by itself.
