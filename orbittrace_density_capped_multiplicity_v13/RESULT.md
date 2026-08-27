# OrbitTrace density-capped multiplicity v13 — target-excluded development result

## Frozen verdict

`FAIL_DENSITY_CAPPED_MULTIPLICITY_V13_TARGET_EXCLUDED_DEVELOPMENT`

v13 is a permanent no-go in this form. The preregistered rule required every lower-cardinality stress condition (96, 64, and 32) to pass every robustness gate relative to the exact cap-128 reference. Cap 32 failed the preregistered MRR-retention gate, so the method cannot be promoted by selecting the better-performing 64/96 conditions after seeing results.

## Provenance

- clean pre-external base: `c9d6c44704013ba0c9430100e98a29a56b453304`
- source/protocol PR: `#905`
- frozen r3 source head before execution token: `b4a3bde579957495247ac1664181d46f6765ffbf`
- execution PR: `#908`
- execution commit: `c95f5f4199a1e414b973ab4504f710b2f6bb6bab`
- workflow run: `31356056453`
- aggregate artifact: `orbittrace-density-capped-multiplicity-v13-development`, artifact ID `9050826968`

Earlier r1/r2 runs were superseded for implementation/transport reasons and their incomplete stress outputs were not used for model selection.

## Integrity result

Every preregistered integrity gate passed:

- cap 128 exact family universe matched direct frozen v5;
- cap 128 exact multiplicity order matched direct frozen v5;
- cap 128 exact multiplicity metrics matched direct frozen v5;
- all caps used the same 92-family universe;
- Brown-equivalence error remained within `1e-10`;
- all synthetic cardinality checks were present;
- labels entered only after ranking;
- SonotaCo 2013/2014, MAARSY, and OrbitTrace target information were not accessed.

Reference family-universe SHA-256: `486690de951d63a40e0c1682531a0a8d0ba3fcd17f1b026c6c3b2b8559350a7a`.
Reference multiplicity-order SHA-256: `37d7617ba00998611bdb4709cde25df538ddab4cdaef74f37b8ac2a83fa8ac13`.

## Frozen cap-128 reference

- family count: 92
- qualified matches: 56
- recovered@100: 56
- MRR: `0.07346150537319665`
- median rank: `37.5`
- top-100 dominant precision: `0.6969754706187407`
- preregistered 90% MRR floor: `0.066115354835877`
- preregistered recovered@100 floor: 51

## Stress results

### Cap 96 — PASS

- recovered@100: 56
- MRR: `0.0681244366177763`
- median rank: `38.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- all preregistered robustness gates: pass

### Cap 64 — PASS

- recovered@100: 56
- MRR: `0.07520157419297539`
- median rank: `33.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- all preregistered robustness gates: pass

### Cap 32 — FAIL

- recovered@100: 56 — pass
- MRR: `0.0652748398778187` — **fail**
- median rank: `39.0`
- top-100 dominant precision: `0.6969754706187407` — pass
- qualified matches: 56 — pass

The cap-32 MRR is `0.888558429972428` of the cap-128 reference, a decline of about `11.14%`, below the preregistered requirement of at least 90% retention. This single failed gate is binding.

## Interpretation

The experiment supports two narrower conclusions but not promotion of v13:

1. The multiplicity ratio itself remains technically well behaved under reduced episode cardinality: family universe, recovery count, precision, Brown equivalence, and the exact cap-128 identity controls all remained intact.
2. Simply replacing fixed 128-event episodes with uncorrected `K=min(128,N_local)` is not robust enough at the lowest preregistered stress level because ranking quality measured by MRR degrades beyond the frozen tolerance.

Therefore v13 must not be rescued by retrospectively setting a 64-event floor, dropping cap 32, relaxing the 90% MRR gate, or selecting the best cap. Those would be post-result changes.

A successor may address the identified low-cardinality ranking-variance problem as a new architecture on target-excluded development data, but v13 itself remains failed. SonotaCo 2013/2014 remains unavailable as an untouched validation set for any successor.
