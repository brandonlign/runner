# Engineering repair 1 — Python compatibility for pinned GMN reader

## Classification

**ENGINEERING NO-RESULT REPAIR ONLY.**

Workflow runs `31972230939` and `31972254101` did not read a single project monthly trajectory file and did not access any project `Num (stat)` value. Both stopped during dependency installation before `audit.py` executed.

The failure was packaging-only: `gmn-python-api==0.0.13` constrains `pandas<=1.3.5`; on CPython 3.11 pip attempted to build pandas 1.3.5 from source and failed while preparing the wheel.

No availability mapping, subset statistic, histogram, scientific ranking, shower truth, station identity, or protected-region station count was produced.

## Exact repair

Run the unchanged pinned package `gmn-python-api==0.0.13` under CPython **3.10**, a runtime compatible with the package's historical pandas dependency.

No project source, monthly-file endpoint, parsed fields, blind exclusion, event universe, completeness definition, conditional station-weighted successor, or scientific gate changes.

Also create the provenance output directory before dependency installation so any future pre-data engineering failure can still preserve logs/provenance.

## Scientific invariants

Unchanged:

- official GMN monthly trajectory source only;
- years 2022 and 2023 only;
- parsed project fields only: unique trajectory ID, solar longitude, `Num (stat)`;
- inclusive protected exclusion `[20.0,55.0]` before station count can enter an emitted mapping/statistic;
- exact eight #1284 sparse subsets and their frozen event counts;
- usable count = finite exact integer `>=2`;
- 95% completeness gates by year and subset;
- no station identity/geography, shower truth, meteor geometry, SonotaCo, ASFN/EFN, AMOS, MAARSY, DMS, or target information;
- conditional station-weighted topomodal protocol remains frozen byte-for-byte.

This repair is permitted because no project station-count data or scientific endpoint was reached.