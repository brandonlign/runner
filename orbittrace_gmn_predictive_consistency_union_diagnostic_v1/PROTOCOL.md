# OrbitTrace GMN predictive-consistency union diagnostic v1

## Scientific role

This is a target-excluded GMN transfer diagnostic following the binding hard-family `PASS_GMN_PREDICTIVE_CONSISTENCY_SIGNAL` from run `31560470070`. It asks one necessary transfer question before any SonotaCo truth is revisited: does the exact same candidate-internal predictive mechanism retain useful ranking information when applied to the full immutable hard + P19 + P20 union used by the active GMN ranker?

No SonotaCo result is used to motivate or select this diagnostic. No target information, target-region event, MAARSY, or DMS access is authorized.

The first technically valid result is binding. A FAIL closes full-union transfer of this exact mechanism and blocks the dormant SonotaCo v61 benchmark. A PASS authorizes one separately frozen full-universe SonotaCo successor.

## Immutable universe and baseline

Use exact frozen GMN 2022/2023 artifacts:

- hard: 226 families;
- P19 soft: 1075 families;
- P20 soft: 3203 families;
- total union: 4504 families.

Input identities remain the existing frozen P19/P20/v8 hashes. Candidate generation and membership are not recomputed or changed.

The baseline order is the exact active #839 34-feature grouped five-fold OOF quality/diversity order at fixed lambda `0.8`, scale `1.0`, and its exact tie rule. It must reproduce the frozen control:

- recovered@25 = 22
- recovered@50 = 40
- recovered@100 = 75
- recovered@500 = 159
- qualified matches = 256
- top-100 dominant precision = 0.7645689180574315
- MRR = 0.019037817654898162

## Exact predictive feature

For every one of the 4504 immutable families and each year 2022/2023, apply exactly the already-passed hard-family rule:

1. Use pretruth member solar longitude, solar-centered radiant longitude, ecliptic latitude, and positive geocentric speed.
2. With annual membership >=4, perform deterministic leave-one-out OLS using design `[1, signed_delta_solar_longitude / 10 deg]` and response `[radiant unit-vector x,y,z, log(vg)]`.
3. Normalize the predicted radiant and score held-out residual as `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`.
4. With annual membership <4, use the annual static centroid residual as predictive residual and set the learned fraction to zero. Never delete a family.
5. Summarize each family by worst-year predictive q90, worst-year predictive median, worst event residual, worst-year static q90, q90 gain (`static_q90 - predictive_q90`), and learned-member fraction.

Predictive order is exactly:

`(lower worst-year predictive q90, lower worst-year predictive median, higher q90 gain, family_id)`.

No orbital elements or source identity enter the predictive score.

## Frozen fusion

Convert the exact #839 baseline order and exact predictive order to 1-based ranks over the same 4504-family universe. The sole fused order is:

`(baseline_rank + predictive_rank, baseline_rank, family_id)`.

No coefficient, alternate fusion, threshold, source quota, family deletion, diversity change, rank window, candidate-type exception, or post-result rescue is permitted.

## Binding PASS gate

PASS requires all five:

- fused recovered@100 strictly greater than 75;
- fused recovered@50 >= 40;
- fused recovered@25 >= 22;
- fused top-100 dominant precision >= 0.7645689180574315;
- fused MRR >= 0.019037817654898162.

Otherwise verdict is FAIL.

## Firewall

- protected solar longitude 20 deg through 55 deg remains excluded;
- SonotaCo 2013/2014 access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false;
- MAARSY scientific access = false;
- DMS scientific access = false.
