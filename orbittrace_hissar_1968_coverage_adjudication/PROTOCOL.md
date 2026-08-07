# OrbitTrace v8 — Hissar 1968 matched-coverage eligibility adjudication

## Status
Frozen **before any Hissar catalogue form submission or meteor-row access**.

This stage answers a single pre-scientific question: can the documented Hissar 1968 observing window possibly satisfy the already-frozen external requirement of at least 24 scannable 10° solar-longitude bins in each year? If not, the fresh Hissar event panel must remain unopened and is rejected as a matched external validation panel on data-availability/coverage grounds.

## Immutable v8/external rule
The authoritative frozen v6 source is `orbittrace_label_free_sparse_support_v6/run_development.py`, blob SHA `7995fc6b75d1fd51eb4b304ace39db28a5a1e876`.

The audit must source-verify all of these exact facts:
- `MIN_SCANNABLE_BINS=24`;
- scan loop has exactly 36 bins;
- each bin is exactly 10° wide (`low=bin_index*10.0`, `high=(bin_index+1)*10.0`);
- anchors must lie inside the bin itself;
- a bin cannot be counted scannable when it has no anchors;
- the ±15° pool must contain at least the frozen 128-neighbor audit requirement.

The Hissar scientific protocol on parent branch `agent/orbittrace-v8-hissar-1968-1969-external` restores this 24-bin gate before first scientific access. No lower coverage floor is admissible.

## Allowed metadata sources
Exactly two public metadata GETs are allowed:
1. IAU MDC radio catalogue page: `https://ceres.ta3.sk/iaumdcdb/home/catalog/radio`;
2. NASA/JPL Solar System Dynamics approximate planetary positions page: `https://ssd.jpl.nasa.gov/planets/approx_pos.html`.

No IAU form submission, result/download action, Hissar event row, source/shower label, excluded-interval content, or OrbitTrace target information may be accessed.

The IAU page must establish the published Hissar overall extent begins at `1968 12 12.73530`. For the most favorable possible 1968 coverage bound, assume observations could continue continuously from that exact published start through **1969-01-01 00:00**, even if the actual 1968 data end earlier. This deliberately maximizes the possible 1968 solar-longitude span.

## Conservative solar-longitude motion bound
Use NASA/JPL's published Earth-Moon-barycenter approximate Keplerian elements valid for 3000 BC–3000 AD. The frozen constants are:
- eccentricity at J2000: `e0 = 0.01673163`;
- eccentricity rate: `edot = -0.00003661 / century`;
- mean-longitude rate: `Ldot = 35999.37306329 deg / century`;
- longitude-of-perihelion rate: `varpidot = 0.31795260 deg / century`.

For the 1968 interval, compute `e` from the JPL linear element model. Set mean-anomaly rate `n=(Ldot-varpidot)/36525` deg/day. For an ellipse, the maximum true-anomaly rate is at perihelion:

`dnu_max = n * (1+e)^2 / (1-e^2)^(3/2)`.

Add `abs(varpidot)/36525` to obtain a conservative true-longitude rate bound. The calculation must verify this model bound is below the deliberately looser frozen envelope **1.1 deg/day**. Use 1.1 deg/day—not the tighter computed value—for the coverage impossibility calculation.

This envelope is intentionally conservative relative to JPL's Earth orbital model; small frame/apparent-longitude conventions cannot bridge the enormous gap to the 24-bin requirement.

## Maximum possible occupied-bin calculation
Let `D` be the maximum possible 1968 observing duration in days from `1968-12-12.73530` through `1969-01-01 00:00`. Let `S = 1.1 * D` degrees be the conservative maximum possible solar-longitude arc.

For any contiguous arc of length `S` on a fixed 10° bin grid, the maximum number of distinct bins it can intersect is:

`Bmax = ceil(S / 10) + 1`.

This is deliberately an upper bound: it assumes at least one otherwise-valid anchor can occur in every intersected bin, ignores the 128-event ±15° pool requirement, ignores the 20°–55° blind interval, and ignores all event-quality losses. Those real rules can only reduce scannability.

## Decision
- `PASS_HISSAR_1968_COVERAGE_ELIGIBILITY`: only if `Bmax >= 24`; this would authorize proceeding to the already-frozen scientific Hissar request.
- `FAIL_HISSAR_1968_COVERAGE_ELIGIBILITY`: if `Bmax < 24`; this establishes before event access that Hissar cannot satisfy the immutable matched-coverage integrity gate. Do **not** submit the Hissar catalogue form.

A coverage-eligibility FAIL is **not a v8 performance failure**. It is a defensible external data-availability limitation: a fresh, interface-compatible panel exists, but its documented 1968 observing season cannot support the matched external test required by the frozen methodology.

## Preservation and blindness
Record exact source hashes, metadata hashes, duration, JPL-derived rate bound, the deliberately loose 1.1°/day envelope, `Bmax`, and the verdict in a GitHub Actions artifact. Delete downloaded HTML before artifact upload. Preserve all prior UKMON/Harvard/Hissar audit failures. Do not access OrbitTrace target information.