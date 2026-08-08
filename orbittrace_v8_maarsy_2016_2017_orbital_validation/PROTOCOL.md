# OrbitTrace v8 — MAARSY 2016/2017 post-ranking orbital validation

## Status

Frozen after the successful geometry-only MAARSY run `31233762587` / artifact `9014840161` and **before any MAARSY `kepler` dataset value is read**.

The geometry-only stage already fixed the complete 107-family universe and all four rankings without orbit access. This stage may only apply the already-frozen external orbital corroboration and scientific pass/fail rules to that immutable universe.

## Immutable geometry prerequisite

Require exactly:

- geometry run: `31233762587`;
- artifact: `9014840161`;
- artifact ZIP SHA-256: `8205805377eeea8791def0ce410365198dab9ebf68f9bd973e6e9eb82b1d8b12`;
- result file SHA-256: `12705afe1d499f8c0a5acbbae37d7119e4c369015b1cd1cfc18f2c3b63086351`;
- ranking file SHA-256: `fe8905d4c681a62f0b3f3b574465793d157f378d5c8321910f8d0bc6875e7279`;
- geometry verdict: `PASS_V8_MAARSY_EXTERNAL_N_POWER_GATE`;
- years: `[2016, 2017]`;
- recurrent families: `N=107`;
- exact canonical geometry-ranking SHA-256: `a23696dc09896696d8b3c210181b9f0f93446dde73329f1ac5c53a4cf288c05b`;
- `orbit_access=false`;
- `target_information_access=false`;
- all geometry-stage integrity gates true.

No family, event membership, ranking, score, year pair, density cap, blind cut, or v8 parameter may change here.

## Frozen MAARSY native orbit semantics before values

The selected MAARSY HDF5 schema was inspected structurally before any values and established `kepler` shape `(n, 6)` on the same row axis as the geometry fields.

The six columns are frozen from public DASST/pyorb and author source, not from observed MAARSY orbit values:

1. DASST source `danielk333/dasst` commit `298b45b2bdb2ef4e2d20bd6a13d5401189d79798`, `methods.py` Git blob `4672e516ea71a39a63a487f7ed6d4852b3a97b36` constructs `pyorb.Orbit(... degrees=True, type="true")` and serializes `orb.kepler` into `kepler_HeliocentricMeanEcliptic`.
2. pyorb source `danielk333/pyorb` commit `e808fd230599a7b0153c1632b298644f26595187`, `orbit.py` Git blob `a735a50893a60624f0148991153dc8eddcb11d44` defines `Orbit.KEPLER = ['a', 'e', 'i', 'omega', 'Omega', 'anom']`; `degrees=True` means angular elements are degrees.
3. Author source `jvierine/pansy_receiver` commit `a9f40ab941fa6fec0a781de552c2a4341c8639ba`, `dasst_orbits_from_candidate_states.py` Git blob `078ab7a939bc0939296aa0cf5bdc5ab00ad7a643` explicitly states: `DASST/pyorb order is a, e, i, omega, Omega, true anomaly`, defines `AU_M = 149597870700.0`, converts `a_au = kepler[0] / AU_M`, leaves the angles as supplied, and computes `q_au = abs(a_au * (1-e))`.

Therefore the exact native conversion is frozen as:

- column 0: semimajor axis `a_m`, meters;
- column 1: eccentricity `e`;
- column 2: inclination `i_deg`;
- column 3: argument of perihelion `omega_deg`;
- column 4: ascending node `Omega_deg`;
- column 5: true anomaly `nu_deg` (unused by D_SH);
- `a_AU = a_m / 149597870700.0`;
- `q_AU = abs(a_AU * (1-e))`;
- D_SH input `arg = omega_deg mod 360`, `node = Omega_deg mod 360`.

No alternative column permutation or unit conversion is permitted after orbit values are seen. If the stored values fail the preregistered validity checks under this mapping, the result is an interface/integrity failure rather than a remapping.

## Frozen orbital evaluator

Reuse byte-for-byte the already-used external evaluator and D_SH comparator:

- SAAMER evaluator Git blob `16a4e832893cbc689ff084510f792349035e5ff7`;
- literature D_SH comparator Git blob `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`;
- `D_SH < 0.05`;
- minimum 4 events from each year in a single-link orbital component;
- minimum orbital-corroboration precision `0.50` of all family events;
- family is orbitally corroborated only if all those frozen conditions hold.

The evaluator's only dataset-specific adaptation is replacing its SAAMER event-ID parser with the already-frozen MAARSY ID parser `MAARSY|YEAR|ARCHIVE_MEMBER|ROW_INDEX_0BASED` and setting years to `(2016, 2017)`. The corroboration and ranking-evaluation algorithms are otherwise unchanged.

## Orbit access boundary

The geometry artifact supplies the exact set of family event IDs. The Q stage may read `kepler` rows **only for those event IDs**.

For every archive member:

- if the member has no needed family-event row, do not open its HDF5 payload for orbit data;
- if needed, verify `kepler` is rank-2 with shape `(n, 6)` and numeric dtype;
- read only the sorted unique needed row indices from `kepler`;
- never read `kepler_std`;
- never read any geometry, label, CNN, RCS, pressure, altitude, or other scientific dataset in this stage;
- never access 2018+ member payloads;
- stop at the first `data/2018/` header.

A valid orbit row requires all converted D_SH inputs finite, `q>0`, `e>=0`, and `0<=i<=180`. `omega` and `Omega` may be any finite degree values and are reduced modulo 360. No eccentricity upper bound or semimajor-axis sign filter is introduced beyond the inherited evaluator behavior.

## Frozen power and scientific decision

Let `Q` be the number of orbitally corroborated families among the immutable `N=107` universe.

Power gates remain:

- `N >= 100` — already passed with N=107;
- `Q >= 30`.

For each frozen ranking, evaluate top `K=min(100,N)=100` corroborated count and exact hypergeometric enrichment with the inherited evaluator.

Primary scientific gates, unchanged from the direct-v8 AMOR external protocol:

1. multiplicity top-100 corroborated >= Brown top-100 corroborated + 1;
2. multiplicity top-100 corroborated >= `ceil(0.90 * persistence top-100 corroborated)`;
3. multiplicity top-100 hypergeometric enrichment p <= `0.05`.

Return exactly:

- `FAIL_V8_MAARSY_EXTERNAL_ORBITAL_INTEGRITY` if a non-power integrity/interface gate fails;
- `INCONCLUSIVE_V8_MAARSY_EXTERNAL_POWER_Q` if integrity passes but `Q < 30`;
- `PASS_V8_MAARSY_EXTERNAL_VALIDATION` if both power gates pass and all three scientific gates pass;
- `FAIL_V8_MAARSY_EXTERNAL_VALIDATION` if both power gates pass but one or more scientific gates fail.

A powered scientific failure is not authorization to alter v8 in this stage. A pass is the only outcome that can be used by a separate, artifact-bound adjudication to satisfy the frozen external-validation prerequisite for final GMN Stage A.

## Firewall

This stage must not access OrbitTrace coordinates, identity, canonical members, target-region GMN values, withheld reference, Stage A ranking, or Stage B reveal data. It must not create a Stage A or Stage B request itself.