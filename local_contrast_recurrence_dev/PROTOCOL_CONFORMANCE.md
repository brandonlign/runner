# Local-contrast recurrence: protocol-conformance repair

Status: frozen before the conformance rerun. This stage changes no detector statistic, data, seed, trial count, injection, comparator, calibration family, or scientific endpoint.

## Integrity finding

The prospectively committed `DEVELOPMENT_PROTOCOL.md` states that the reduced kill screen continues when each independently audited null family has observed FWER at most **0.20**. The runtime derivation accidentally encoded **0.15** in the two null-family gates.

Workflow `30877969736` then observed:

- ideal-null FWER: 0.00;
- shared-structure-null FWER: 0.20;
- one-year-artifact detection: 0.00;
- weak recurrence-margin gain: +0.15;
- strong recovery gain: +0.0333.

The run is therefore not an authoritative failure of the frozen protocol: it failed only an implementation threshold that contradicted the predeclared document. Its scientific outputs remain preserved but cannot determine continuation.

## Sole repair

Derive the identical local-contrast source from the identical pinned worst-family source and original derivation, then replace only:

- null-family gate labels `0_15` with `0_20`;
- the two comparisons `<= 0.15 + tol` with `<= 0.20 + tol`.

The conformance wrapper requires each old source fragment to occur exactly once. No other byte-level source transformation is allowed.

## Frozen rerun

- exact base source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- original derivation file is unchanged and hash-recorded;
- 20 calibration catalogs per null family;
- 20 independently seeded audit catalogs per null family;
- 30 injections per strength;
- unchanged ideal and shared-structure nulls, recurrent injections, one-year artifacts, comparators, and alpha 0.10.

The conformance run passes only if every original frozen protocol gate at the documented 0.20 null-family ceiling passes. A pass authorizes a separately frozen larger Stage-0 benchmark with new seeds and more trials. It does not validate the method, authorize real-shower testing, or permit GhostStream application.

No later result may justify changing 0.20, the filter, recurrence order, trial counts, score, comparator, injection design, or any other gate in this conformance rerun.
