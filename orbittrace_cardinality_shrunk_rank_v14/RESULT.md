# OrbitTrace cardinality-shrunk rank v14 — target-excluded development result

## Frozen verdict

`FAIL_CARDINALITY_SHRUNK_RANK_V14_TARGET_EXCLUDED_DEVELOPMENT`

v14 is a permanent no-go in this form. The preregistered rule required every lower-cardinality stress condition (96, 64, and 32) to pass every unchanged v13 robustness gate relative to the exact cap-128 multiplicity reference. Cap 96 failed the MRR-retention gate, so the shrinkage rule cannot be rescued by changing its weighting curve or selecting only the caps that passed.

## Provenance

- clean pre-external base: `c9d6c44704013ba0c9430100e98a29a56b453304`
- source/protocol PR: `#909`
- frozen source head: `a28900c762281af7f0b192062d7c61f91dff9c14`
- execution PR: `#910`
- execution commit: `503e88de967612006aff991372f2245171767f1c`
- workflow run: `31357201878`
- label-free sanitized-input artifact: ID `9051053392`, SHA-256 `95b2aad8fb089de708fe9dd5d168c15a12fada8399420956e164f2c32b9cc72a`
- frozen pretruth-order artifact: ID `9051055612`, SHA-256 `8fdc9b348ea6e67227552996bb69e1e0858140a540e059115f2bca32195d2be2`
- final development-result artifact: ID `9051058641`, SHA-256 `9defe592df1b29b1872af76ac19604f412561e358160e7db4cb63dcf6fdcfa1b`

## Frozen rule

For each recurrent family and stress cap:

- `r_M`: zero-based frozen multiplicity rank;
- `r_F`: zero-based frozen fixed4-persistence rank;
- `q = min(year episode sizes) / 128`, clipped to `[0,1]`;
- `R14 = q*r_M + (1-q)*r_F`;
- rank ascending by `R14`, then `r_M`, then `r_F`, then stable family ID.

No coefficient was fitted and no cap was selected after results.

## Firewall and integrity result

Every preregistered integrity gate passed:

- all four v14 orders were frozen in a job that received no evaluation, family-label, holdout, or truth files;
- the evaluator downloaded the frozen label-evaluation payload only after `PASS_V14_PRETRUTH_RANK_FREEZE`;
- exact family membership matched across all caps;
- cap 128 v14 order exactly matched direct frozen-v5 multiplicity order;
- cap 128 recomputed metrics matched the direct frozen-v5 values to machine precision (maximum absolute difference `1.1102230246251565e-16`);
- every `q` was in `[0,1]` and every fused rank score lay between its multiplicity and fixed4 endpoints;
- every `q=1` row reproduced the multiplicity endpoint exactly;
- SonotaCo 2013/2014 was not accessed;
- MAARSY was not accessed;
- OrbitTrace target information/region was not accessed.

Frozen family count: 92.
Frozen exact-family-membership SHA-256: `695fd71df60f727a99f481553b31958f6a5f306d38036fcf9c6afe8fb4410e2e`.

## Cap-128 reference

- eligible labels: 297
- qualified matches: 56
- recovered@100: 56
- recovered@500: 56
- MRR: `0.07346150537319665`
- median rank: `37.5`
- macro F1: `0.2109415894913715`
- top-100 dominant precision: `0.6969754706187407`
- required 90% MRR floor: `0.066115354835877`
- required recovered@100 floor: 51

## Stress results

### Cap 32 — PASS

- recovered@100: 56
- MRR: `0.07207174755674244`
- median rank: `37.0`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- all preregistered robustness gates: pass

### Cap 64 — PASS

- recovered@100: 56
- MRR: `0.07569625815397829`
- median rank: `34.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- all preregistered robustness gates: pass

### Cap 96 — FAIL

- recovered@100: 56 — pass
- MRR: `0.0556458723815386` — **fail**
- median rank: `36.5`
- top-100 dominant precision: `0.6969754706187407` — pass
- qualified matches: 56 — pass

The cap-96 MRR is about `75.75%` of the cap-128 reference, well below the frozen 90% retention requirement. This failed gate is binding.

## Interpretation

The deterministic linear shrinkage rule solved the v13 cap-32 failure but introduced a much larger ranking failure at cap 96. The failure is therefore not simply “too little multiplicity information at low N”; ordinal mixing between multiplicity and fixed4 can itself destabilize the positions of qualified families even when the episode retains 75% of the full cardinality.

v14 must not be rescued by changing `q`, adding a fitted exponent, introducing a cap-specific exception, or choosing only caps 32/64. Those would be post-result changes.

A legitimate successor should target **rank stability directly using label-free perturbations or consensus**, rather than hand-adjusting a multiplicity/fixed4 interpolation curve. Any such successor remains development-only and requires a different untouched external validation dataset after freezing.
