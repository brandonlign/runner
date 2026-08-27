# OrbitTrace v16 — v15 locator + frozen joint-conformal membership

## Status

Successor-development protocol created only after the immutable v15 SonotaCo 2013/2014 matched-literature result established `FAIL_FINAL_LITERATURE_SUPERIORITY` in run `31405109267` / artifact `9069505548`.

Frozen v15 is not modified or rescued. SonotaCo 2013/2014 is now exposed development evidence for this successor and can never be called pristine validation for v16.

## Mechanistic diagnosis

The v15 matched output exposes the recurrent sparse-support core itself as final catalogue membership. The core can identify a real shower with very high precision but extremely low recall; e.g. one frozen 2013 match had 17/17 predicted events correct against a 553-event truth shower, so F1 was only ~0.060. This protocol changes only the membership-output layer.

## v16 architecture

1. Family existence and order are exactly the already-frozen v15 SonotaCo candidate output from run `31405109267`.
2. The original v15 family event IDs are immutable seeds and can never be removed.
3. For each target year, only original v15 seeds from the other year may define membership support.
4. Membership uses the exact fixed mathematics of the previously frozen joint density + trajectory conformal experiment (#461), without SonotaCo parameter selection:
   - second-nearest source-seed distance in the inherited normalized `(sol, sun_lon, ecl_lat, vg)` metric;
   - affine `(sun_lon, ecl_lat, vg)` trajectory versus solar longitude, fit only to other-year source seeds;
   - leave-one-out source references for both density distance and trajectory residual;
   - empirical upper-tail marginal p-values;
   - equal-weight Fisher nonconformity `-2(log p_density + log p_trajectory)`;
   - empirical joint conformal recalibration against source-seed Fisher scores;
   - fixed activity padding `+/-6 deg`;
   - fixed density ceiling `1.5`;
   - fixed trajectory-residual ceiling `1.5`;
   - fixed joint conformal acceptance `p > 0.05`;
   - exclusive assignment by largest joint p, then smaller Fisher nonconformity, then stable family ID.
5. New members never become support, never change family existence, never change v15 rank, and never recursively grow membership.

The constants above are inherited byte-for-mathematics from pre-SonotaCo PR #461; they are not chosen from the v15 SonotaCo failure.

## Development evaluation

The exact already-exposed matched SonotaCo rows, truth maps, comparator outputs, and v15 candidate artifacts from run `31405109267` are reused. The successor output is frozen before the exposed truth maps are loaded in the workflow, even though the panel is no longer prospectively blind.

Report the exact #854 one-to-one F1 matching endpoints for each comparator/year and compare v16 against both frozen v15 and the frozen literature comparator. Do not alter #854 budgets or matching semantics.

A gain on SonotaCo is development evidence only. A SonotaCo win after this point is not external validation and does not authorize MAARSY, DMS, or OrbitTrace target access.

## Stop / successor rule

- If joint-conformal membership closes most of the membership gap but v16 still loses, diagnose the next bottleneck from frozen output structure rather than tuning `alpha`, radii, padding, model order, neighbor order, Fisher weights, or assignment rule.
- The known candidate-universe shortage (only 19–22 v15 recurrent families on the matched panels, versus larger Sugar family budgets) is the next admissible architectural target if membership alone is insufficient.
- Any family-universe successor must be separately named and must preserve this v16 result rather than rewriting it.

## Firewalls

- No MAARSY event/scientific values.
- No DMS scientific values.
- No OrbitTrace target information or target-region event access.
- Solar longitude 20°–55° remains inaccessible to target-containing work.
- Original discovery provenance remains historical blind HDBSCAN.