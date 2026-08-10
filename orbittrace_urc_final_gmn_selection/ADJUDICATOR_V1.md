# Final GMN M0/M2 adjudicator — v1

## Purpose

Freeze the mechanical decision that ends GMN methodology selection before the only admissible M2 feasibility result is known.

The scientific decision rule is already fixed in `FREEZE.md`. This adjudicator adds no scientific threshold and performs no model fitting, candidate generation, membership generation, or evaluation. It merely enforces the already-frozen dependency chain and returns the final membership architecture when the required artifacts exist.

## Immutable facts

- Discovery catalogue/ranking is exact #839 hard+P19+P20 URC.
- M0 is the default membership.
- M1/#845 is a permanent scientific no-go and cannot be selected.
- Only final corrected #846 source commit `e5733a57488b7b8dff26c15ff76f679810efac9c`, run `31344902186`, may establish M2 feasibility.
- Earlier #846 runs are permanently inadmissible.
- M2 can exist only after exact #846 feasibility PASS, exact #850 fixed-policy five-salt stress PASS, and exact #852 full-URC promotion PASS.
- Any FAIL in that chain permanently selects M0.
- Missing downstream artifacts after an upstream PASS mean `NOT_READY`, not a scientific failure and not authorization to change anything.

## Deterministic states

1. #846 final corrected result absent → `NOT_READY_846`.
2. #846 verdict FAIL → `FINAL_GMN_METHOD_M0`.
3. #846 verdict PASS but #850 result absent → `NOT_READY_850`.
4. #850 verdict FAIL → `FINAL_GMN_METHOD_M0`.
5. #850 verdict PASS but #852 result absent → `NOT_READY_852`.
6. #852 verdict FAIL → `FINAL_GMN_METHOD_M0`.
7. #852 verdict `PASS_M2_FULL_URC_PROMOTION_GATE` → `FINAL_GMN_METHOD_M2`.

There is no discretionary tie-break because M1 already failed scientifically.

## Output

The final output records:

- chosen membership architecture M0 or M2;
- immutable #839 order hash;
- M0 reference metrics;
- if M2 is chosen, exact #846 selected model/threshold/cap plus hashes of the #846/#850/#852 inputs;
- explicit closure of GMN methodology development;
- SonotaCo/MAARSY/target authorizations remain false at this stage.

The final selected method still must be packaged as one deployable executable and source-audited before permanent SonotaCo 2013/2014 scientific access.

## Firewall

This adjudicator has no catalogue/data transport and no access to SonotaCo 2013/2014, MAARSY 2020/2021, the 20°–55° target region, OrbitTrace coordinates/members/identity, or prior target recovery results.
