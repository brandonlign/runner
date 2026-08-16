# OrbitTrace topomodal orbital Fréchet ordering v1 — frozen protocol

## Scientific question

Can the already-positive #1284 fixed-scale topological-modal candidate generator be ordered by an independent physical property — heliocentric orbital self-coherence — so that its strong sparse known-stream recovery, purity, fragmentation, and sample-size stability are retained while its persistent MRR deficit is removed?

This is an ordering/canonicalization successor, not a new candidate generator.

## Firewall

- GMN development years remain exactly 2022 and 2023.
- Solar longitude 20°–55° is excluded before any candidate, orbit mapping, score, or truth operation.
- OrbitTrace target information and target-region events remain inaccessible.
- SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS are inaccessible in this stage.
- Shower truth is inaccessible during orbit availability, candidate generation, and ordering.
- The hidden known-shower labels may be opened only by the separately frozen evaluator after the complete candidate order is serialized and SHA-256 sealed.

## Independence from the development truth definition

The GMN/WesternMeteorPyLib shower-association implementation is frozen conceptually as the benchmark-definition audit: known-shower association uses solar longitude, geocentric radiant position, and geocentric velocity. It does not use heliocentric orbital D-criteria. The current association source was audited at WesternMeteorPyLib path `wmpl/Utils/ShowerAssociation.py`; latest source-modifying commit observed before this protocol was `78818af6d7ef0e5416e8473ce3265e35ecf9780f`.

Therefore heliocentric orbital self-coherence is an independent physical view of a candidate rather than a direct reimplementation of the hidden label-assignment score.

## Literature-defined orbital dissimilarity

Use the Southworth–Hawkins orbital dissimilarity `D_SH` exactly, with no fitted coefficient or threshold:

`D_SH^2 = (q1-q2)^2 + (e1-e2)^2 + [2 sin(I/2)]^2 + [((e1+e2)/2) * 2 sin(Pi/2)]^2`

where `I` is the angle between orbital planes and `Pi` is the Southworth–Hawkins angle between eccentricity-vector directions, computed from `(i, Omega, omega)` using the standard formula and wrapped angular differences. Required per-event elements are exactly:

- eccentricity `e`
- perihelion distance `q` (AU)
- inclination `i`
- argument of perihelion `omega` / `peri`
- longitude of ascending node `Omega` / `node`

No semi-major axis, Tisserand parameter, radiant coordinates, solar longitude, shower label, or learned feature enters the orbital score.

## Stage A — zero-label orbit availability audit

Before any `D_SH` value is computed for a project candidate:

1. Reuse the immutable exact #1284 sparse-universe manifest produced before station truth:
   - schema `ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1`
   - exact panel sizes: d128 = 5567, 5840, 5857, 5816; d1024 = 677, 739, 736, 766.
2. Fetch only the same frozen official GMN 2022/2023 monthly trajectory files identified by that manifest and require byte-identical monthly source SHA-256 values.
3. Parse orbital elements only for event IDs already present in the immutable manifest.
4. Do not parse IAU shower number/code or any hidden-label field.
5. An event is orbit-usable iff all five required elements are finite, `e >= 0`, `q >= 0`, `0 <= i <= 180 deg`, and both angular elements are finite. Angles are subsequently reduced modulo 360 only for D_SH evaluation.
6. **Activation requires 100% usable orbital elements in every one of the eight frozen panels.** No event dropping, filtering, replacement, interpolation, imputation, clipping, or fallback geometry is permitted.
7. If any panel is below 100%, this exact lane is closed without truth.

The availability result and exact event-ID→orbit mapping must be serialized and SHA-256 sealed.

## Stage B — frozen candidate universe

Conditional on Stage A passing:

- Candidate memberships are **exactly the original #1284 complete fixed-scale topomodal hierarchy**, not station-weighted candidates and not any later successor.
- Exact #1284 physical embedding and radius-1 graph are unchanged.
- Exact #1284 density is unchanged: radius-neighborhood degree divided by subset event count.
- GUDHI 3.12 manual-graph/manual-density ToMATo hierarchy is unchanged.
- Retain every complete hierarchy membership with support >=4, exactly as #1284.
- Recurrent-EOM comparator and the eight deterministic d128/d1024 thinning panels are unchanged.

A regenerated candidate-membership summary must byte/semantic-match the binding #1284 structural artifact before orbital ordering is allowed.

## Stage C — orbital Fréchet energy and total order

For each candidate independently:

1. Compute all pairwise `D_SH^2` values among its member orbits.
2. For each member `j`, compute the mean squared dissimilarity to all other members:
   `E_j = (1/(n-1)) * sum_{i != j} D_SH(i,j)^2`.
3. Define the candidate orbital Fréchet energy:
   `E_orbit = min_j E_j`.
   The minimizing observed member is the orbital medoid. If multiple members are exactly tied, select the lexicographically smallest event ID only for provenance; the energy is unchanged.
4. Preserve #1284's root-vs-finite hierarchy tier. Rank key is exactly:
   - roots first, then finite/non-root hierarchy nodes;
   - within each tier: `E_orbit` ascending;
   - exact ties: `family_hash` ascending.
5. No persistence, station support, member count, year balance, radiant drift, background score, rank density, learned score, or fusion term enters the ordering.

This is intentionally a one-coordinate physical ordering. No transformed D criterion, alternative D function, orbital-element subset, robust quantile, trimmed statistic, size correction, weight, or blend is allowed after outcome.

## Stage D — immutable prelabel seal

Before shower truth is opened, serialize for all eight panels:

- exact event-universe hash;
- exact #1284 candidate membership and family hash;
- `E_orbit`, medoid event ID, root/non-root tier, and final rank;
- recurrent-EOM candidate order;
- equal candidate budget K = recurrent-EOM candidate count.

Require successor candidate count >= K on all eight panels. SHA-256 seal the complete prelabel. The evaluator may not import the candidate generator or orbital-ordering code.

## Stage E — binding truth endpoint

Use the same 16 annual sparse known-stream panels and the same ten gates used by the #1284/station-weighted recovery series:

Fine d1024:
1. qualified total strictly greater than recurrent-EOM;
2. qualified nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

Coarse d128:
6. qualified total not lower;
7. qualified nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten must pass. One technically valid truth outcome is binding.

## Closure / no-rescue rule

If availability fails, close the lane without truth. If the binding truth outcome fails any gate, permanently close this exact orbital-ordering family for this project. Specifically forbidden after outcome: switching to Drummond/Jopek/other D functions, changing mean to median/trimmed/quantile dispersion, using pairwise minima/maxima, size normalization, root/finite mixing changes, orbital thresholds, rank fusion, station/orbit fusion, fitted weights, or result-informed orbital feature selection.

SonotaCo/external transfer is forbidden unless all ten GMN truth gates pass and a transfer protocol is separately frozen before any external event-level outcome.
