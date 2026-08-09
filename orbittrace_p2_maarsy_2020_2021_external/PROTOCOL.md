# OrbitTrace P2 — pristine MAARSY 2020/2021 external validation

## Status

This protocol is frozen after P2 became the legitimately active successor but before its authoritative development result exists and before any OrbitTrace-project access to MAARSY 2020/2021 event-level scientific values.

Activation requires, without retuning:

1. exact P2 development `PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT`;
2. the already-frozen matched SonotaCo Sugar/HDBSCAN adjudication returns `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against both comparator panels;
3. an execution-time full-repository freshness audit still finds no prior MAARSY 2020/2021 event-value scientific access.

If any prerequisite fails, MAARSY 2020/2021 stays unopened for any later method legitimately entitled to it.

## Claim boundary

P2 uses exact D_SH as one of its two membership features. Therefore this external test is explicitly a **cross-survey no-retuning generalization/transport test**, not an independent-orbit-modality validation. Orbital coherence can still be used to detect catastrophic over-expansion and loss of physical family quality on an unseen survey, but it is not presented as information independent of P2.

## Frozen panel and transport

Use exactly MAARSY 2020 and 2021 from the same public archive/field semantics already established without reinterpretation:

- `sun_lon` = solar longitude;
- `slat` = geocentric ecliptic radiant latitude;
- `slon` = radiant-minus-Sun geocentric ecliptic longitude;
- `norm(vels)` = geocentric speed in km/s;
- native `kepler` order = `a_m,e,i_deg,omega_deg,Omega_deg,nu_deg`;
- deterministic event identity = year + archive member + zero-based row index.

Remove solar longitude 20°–55° before retained radiant/speed/orbit values can enter P2. Apply the already-established deterministic identity-only density transport: at most 10,000 events per fixed 10° solar-longitude bin, selected by smallest SHA-256 event identity. The exact same retained event universe is used for promoted-v8 seeds and P2.

No alternate years, cap, binning, subset, density rule, or survey-specific parameter may be tried after any 2020/2021 value is opened.

## Stage S — promoted-v8 seed/rank freeze before orbit

Before reading native `kepler` values:

1. parse only solar longitude first and apply the 20°–55° exclusion;
2. read retained radiant/speed values only;
3. run the exact promoted-v8 fixed4/component/family graph and pooled-year-centroid multiplicity method on 2020/2021;
4. freeze the complete recurrent family universe, immutable seed IDs, multiplicity order and all transport/input identity hashes.

Require at least 100 recurrent promoted-v8 families. If fewer, return `INCONCLUSIVE_P2_MAARSY_2020_2021_EXTERNAL_SEED_POWER` and do not read `kepler`.

## Stage M — exact frozen P2 transport

Only after Stage S is immutable may P2 read native orbit values needed for its already-frozen `d_orb` feature. Apply exact P2 unchanged:

- source-year OAS observation template;
- exactly two features `[d_obs,d_orb]`;
- positives = opposite-year immutable seeds;
- negatives = all nonseed events in exact ±5° windows;
- at least 128 negatives per family-direction;
- exact family/direction weighting;
- exact weighted `StandardScaler` + L2 logistic regression (`C=1`, `lbfgs`, `max_iter=1000`, `tol=1e-10`);
- unit background and strict responsibility `>0.5`;
- immutable seeds, no refit, no recursive growth;
- exact promoted-v8 rank unchanged.

Freeze the fitted model, every candidate-pair feature/probability, conflict responsibility, final assignment and complete expanded membership payload before evaluating external quality gates.

If any family-direction is input-ineligible or the model fails exact convergence/integrity, return `FAIL_P2_MAARSY_2020_2021_EXTERNAL_INTEGRITY`; do not repair by changing P2.

## External power floor

The earlier MAARSY 2016/2017 promoted-v8 test produced N=107 recurrent families but only Q=11 families under the strict D_SH family-corroboration rule. That already-exposed result is used only to set a prospective feasible physical-quality floor for this later unopened panel.

Require:

- at least 100 frozen seed families;
- P2 expansion is nonvacuous;
- additions occur in at least 30 distinct families;
- at least 200 added events have valid native orbit rows;
- at least 200 deterministic control events have valid native orbit rows;
- both seed and expanded memberships yield at least 10 orbitally corroborated families under the unchanged family rule below.

If integrity passes but any power floor fails, return `INCONCLUSIVE_P2_MAARSY_2020_2021_EXTERNAL_POWER` and do not alter the floor or rerun another subset.

## Frozen physical-quality stress test

For seed and expanded memberships, use the already-established family criterion:

- exact Southworth–Hawkins D_SH;
- `D_SH < 0.05` single-link component;
- at least four members from each year;
- family orbital-corroboration precision at least 0.50.

For each P2-added event, define orbital consistency exactly as in the previously frozen P1 MAARSY protocol: within `D_SH < 0.05` of at least one opposite-year immutable seed orbit in its assigned family. Deterministic controls are drawn before outcome evaluation from the same exact ±5° family windows among nonseed events left unassigned by P2, using smallest SHA-256 identity with family/direction balancing and no resampling.

Because D_SH is an input to P2, these gates are treated as over-expansion/transport stress tests rather than independent evidence.

## Frozen scientific generalization gates

All must pass simultaneously:

1. `Q_P2 >= Q_seed` — expansion may not reduce the count of physically corroborated families;
2. P2-added-event orbital-consistency precision >= 0.60;
3. added-event precision exceeds deterministic-control precision by >= 0.15 absolute;
4. one-sided Fisher exact test for added-vs-control orbital consistency has `p <= 0.01`;
5. total membership inside the qualifying cross-year D_SH components grows by >=20% relative to immutable seeds;
6. median expanded-family orbital-corroboration precision across corroborated families >=0.60;
7. the exact Stage-S family universe and promoted-v8 multiplicity order remain byte-identical after P2 and evaluation.

The 0.60 / +0.15 / p<=0.01 / +20% bars are inherited unchanged from the P1 MAARSY preregistration rather than selected from P2 or MAARSY 2020/2021 outcomes. `Q>=10` is fixed prospectively from the historical 2016/2017 Q=11 yield, not from this unopened panel.

Return exactly:

- `FAIL_P2_MAARSY_2020_2021_EXTERNAL_INTEGRITY` for a non-power source/firewall/method failure;
- `INCONCLUSIVE_P2_MAARSY_2020_2021_EXTERNAL_SEED_POWER` for N<100 before orbit access;
- `INCONCLUSIVE_P2_MAARSY_2020_2021_EXTERNAL_POWER` for post-membership power insufficiency;
- `PASS_P2_MAARSY_2020_2021_EXTERNAL_VALIDATION` if every integrity, power and scientific gate passes;
- `FAIL_P2_MAARSY_2020_2021_EXTERNAL_VALIDATION` if powered but one or more scientific gates fail.

A powered scientific FAIL permanently rejects P2 external generalization. An inconclusive result does not authorize threshold changes, alternate years, a different cap, or a second look at 2020/2021 under different rules.

## Final-target boundary

Only exact P2 development PASS + matched Sugar/HDBSCAN broad/sparse superiority + exact `PASS_P2_MAARSY_2020_2021_EXTERNAL_VALIDATION` may satisfy P2's prerequisites for a separately frozen final target-containing Stage A. This protocol itself never authorizes target access.

No OrbitTrace coordinates, identity, canonical members, historical target rank/recovery, target-region GMN event, withheld reference, Stage-A ranking or Stage-B reveal artifact may be accessed.