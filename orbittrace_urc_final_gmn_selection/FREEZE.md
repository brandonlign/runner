# Final GMN URC method-selection freeze

## Purpose

Freeze the decision that ends GMN 2022/2023 methodology development before the currently running membership experiments (#845 and #846) are known. This prevents post-result selection among architectures and defines exactly when the active #839 method can be replaced.

This file accesses no scientific result from #845/#846 and runs no detector.

## Immutable discovery core

The final GMN candidate/ranking architecture is already fixed unless a future preregistered scientific failure of that architecture itself occurs:

- candidate universe: exact hard-v8 + P19-soft + P20-soft union, 4,504 families on the unperturbed GMN development panel;
- P21 is excluded by its frozen no-material-increment stopping rule;
- ranking: PR #839 strict same-shower grouped ExtraTrees quality regression plus diversity;
- ranker parameters: depth 4, min leaf 5, diversity lambda 0.8, scale 1.0;
- exact selected order SHA-256: `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`;
- ranking/candidate robustness requirement is already satisfied only if the frozen #842 grouped-CV and generator-thinning stress verdicts remain PASS.

No membership experiment may add/remove candidates, reorder candidates, regenerate proposals, or tune the #839 ranker.

## Default membership M0

If no challenger satisfies the final promotion gate below, the final GMN method is #839 with the original frozen hard/P19/P20 memberships.

Reference endpoints for M0 on target-excluded GMN 2022/2023:

- recovery@25 = 22;
- recovery@50 = 40;
- recovery@100 = 75;
- recovery@500 = 159;
- qualified known streams = 256;
- MRR = 0.019037817654898162;
- top-100 dominant precision = 0.7645689180574315;
- best-membership macro F1 across all eligible streams = 0.17953659309876194.

## Admissible membership challengers

Only architectures already frozen/running before this file may challenge M0:

### M1 — #845 fixed-rank fragment-membership merge

M1 exists only if #845 obtains its own preregistered scientific PASS. Its candidate universe/rank stay exactly #839. If #845 fails, no radius/rule from that experiment remains eligible and no M1 rescue is allowed.

### M2 — #846 strict-group event-level P12 calibration

M2 exists only if #846 obtains its own preregistered scientific PASS and freezes one model/rule under its predeclared selector. Because #846 evaluates the hard-family membership problem before full-URC integration, a passing #846 rule receives exactly one subsequent integration evaluation under the immutable #839 candidate order; no model, probability threshold, cap, feature, or calibration parameter may change for that integration. The fixed integrated evaluation may not search another rule.

If #846 fails, no model/threshold/cap from its grid remains eligible and no M2 rescue is allowed.

The superseded pre-result #847 experiment is scientifically inadmissible and cannot become a challenger.

## Final promotion gate versus M0

A challenger can replace M0 only if its final fixed-membership evaluation under the exact #839 order satisfies **all** of:

- recovery@25 >= 22;
- recovery@50 >= 40;
- recovery@100 >= 75;
- recovery@500 >= 159;
- qualified known streams >= 256;
- MRR >= 0.019037817654898162;
- top-100 dominant precision >= 0.740000;
- best-membership macro F1 >= 0.19953659309876195 (M0 + 0.020000);
- annual all-shower mean F1 delta versus M0 >= 0 in both 2022 and 2023;
- annual 4–9-member mean F1 delta versus M0 >= -0.002 in both years and >= 0 on average;
- at least one of the 25–49, 50–99, or 100+ strata improves in both years, with mean two-year gain >= +0.015;
- all original-membership/candidate/ranking/target-firewall integrity checks pass.

Thus a membership improvement cannot be purchased by giving back #839's discovery coverage or early-rank recovery.

## Robustness requirement

A challenger must also satisfy the robustness condition already frozen inside its own experiment:

- M1: at least two adjacent frozen radii pass #845's preregistered feasibility gates;
- M2: #846's preregistered multi-variant feasibility requirement passes, and its selected fixed rule subsequently passes the already-required fixed-setting repeated same-shower group-fold stress before full-URC promotion.

No new robustness threshold may be chosen after result inspection.

## Deterministic winner if both challengers survive

If neither challenger survives the final promotion gate, choose M0.

If exactly one survives, choose that challenger.

If both survive, choose by the following frozen lexicographic rule on their fixed integrated GMN results:

1. larger best-membership macro F1;
2. larger minimum of the 2022 and 2023 all-shower F1 deltas versus M0;
3. larger recovery@100;
4. larger recovery@50;
5. larger top-100 dominant precision;
6. larger qualified-stream count;
7. fewer added event memberships.

If the absolute macro-F1 difference is <0.005 and all later numerical criteria through qualified-stream count tie, prefer M1 because it is label-free at both development and application rather than supervised on known-shower membership correctness.

This tie-break is frozen before either membership result is read.

## Development stopping rule

Once this decision is resolved, GMN 2022/2023 methodology development stops. No additional candidate generator, ranking model, membership architecture, threshold family, or score combination may be introduced from the final GMN outcomes.

The chosen method is then source-frozen as one executable transport before any SonotaCo 2013/2014 scientific value is opened.

## Fixed downstream pipeline

The dataset roles are immutable and may not be swapped or repurposed after results are seen: **GMN 2022/2023 is development/training, SonotaCo 2013/2014 is the single literature-comparison test, and MAARSY 2022 is the no-retuning external validation.**

After the final GMN method is frozen:

1. exactly one SonotaCo 2013/2014 matched-data literature test against the already-frozen Sugar and catalogue-HDBSCAN implementations, under candidate-budget parity and one-to-one candidate↔known-shower matching;
2. only a passing literature-superiority result may authorize the frozen MAARSY 2022 no-retuning external validation;
3. only passing external/generalization gates may authorize restoration of solar longitude 20°–55° for the final frozen blind target-free OrbitTrace search.

Until then, SonotaCo 2013/2014 scientific values, MAARSY 2022 scientific values, the 20°–55° target region, OrbitTrace coordinates/members/identity, and prior OrbitTrace recovery information remain inaccessible.
