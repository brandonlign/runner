# OrbitTrace P3 — preregistered matched-literature comparison

## Status and activation

This protocol is frozen while authoritative P3 development run `31291214704` is still unresolved and before any P3 matched-literature result exists. It may execute only if that exact P3 lineage returns `PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT` with every integrity gate intact.

A P3 development failure permanently leaves this comparison dormant. No P3 threshold, fold, reliability rule, feature, model, conflict rule, core/rank rule or evaluator may be changed from the development outcome.

Solar longitude 20°–55° remains excluded throughout this comparison. No OrbitTrace target information is authorized.

## Purpose and competitors

Test the exact frozen complete P3 pipeline against the two strongest already-implemented catalogue comparators under pairwise exact-row matched SonotaCo panels:

1. Sugar uncertainty-aware retained-master catalogue reconstruction;
2. Peña-Asensio–Ferrari catalogue HDBSCAN transfer.

The Sugar and HDBSCAN row universes differ. All metrics and superiority decisions are therefore pairwise. A Sugar denominator may never be mixed with an HDBSCAN denominator.

## Immutable comparator artifacts

Reuse exactly the competitor assignments and row universes already frozen by the matched-v8/P2 literature protocols.

HDBSCAN:
- SonotaCo 2023 workflow `31076062060`, assignment SHA-256 `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60`;
- SonotaCo 2025 workflow `31071589912`, assignment SHA-256 `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`.

Sugar retained-master:
- SonotaCo 2023 workflow `31076789635`, assignment SHA-256 `2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389`;
- SonotaCo 2025 workflow `31075178517`, assignment SHA-256 `77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e`.

No comparator may be rerun, retuned, re-filtered, re-ranked or replaced after P3 outcomes are known.

## Exact P3 transport

Run two independent transports: the joint 2023/2025 Sugar exact-row universe and the joint 2023/2025 HDBSCAN exact-row universe.

For each pairwise panel:

1. Verify the exact competitor artifact and assignment hashes, then extract only the immutable exact event-ID universe. Competitor cluster labels and known-shower truth remain unavailable to P3 until its complete pretruth payload is frozen.
2. Resolve every retained ID to the immutable SonotaCo scientific row required by promoted-v8 core construction and P3 features. If any row scientifically required by a seed/template/candidate lacks a frozen input, the panel is input-ineligible; do not shrink the row universe after outcomes.
3. Remove solar longitude 20°–55° before retained-row geometry, orbit, label or comparator values can enter method construction.
4. Reconstruct the exact panel-specific promoted-v8 recurrent cores and exact multiplicity order under source commit `c9d6c44704013ba0c9430100e98a29a56b453304`. The matched event rows are the only permitted transport change.
5. Treat 2023 and 2025 as the two cross-year directions and reconstruct canonical P2 exactly: source-seed OAS Mahalanobis `d_obs`, minimum exact Southworth–Hawkins `d_orb`, deterministic ±5° local nonseed windows, >=128 negatives per family-direction, equal 0.5 positive/0.5 negative total weight per direction, StandardScaler and L2 LogisticRegression C=1.0/lbfgs/max_iter=1000/tol=1e-10.
6. Apply exact P3 on top of that panel-specific P2 construction: family fold = first eight bytes of SHA256(family ID UTF-8) modulo five; each held-out family-direction is scored by a P2-identical model trained on the other four family folds; `seed_floor_fd` is the minimum held-out recurrent-seed probability; `negative_tail_fd` is the complete local-negative fraction at or above that floor; a direction is reliable only with >=4 held-out seeds, `seed_floor_fd > 0.5`, and `negative_tail_fd <= 0.10`.
7. Fit the final all-family canonical P2 model unchanged. A candidate proposal survives only from a reliable direction and only if final-model probability is >= its already-frozen `seed_floor_fd`; then apply the unchanged unit-background joint family responsibility and strict maximum responsibility >0.5 rule.
8. Original v8 seeds remain immutable; additions never train/refit/recenter/seed growth; exact v8 multiplicity order remains unchanged.
9. Before truth or competitor labels are exposed, SHA-freeze: exact v8 family/core/order identity; five-fold assignment; every cross-fit model; every held-out positive/negative probability-vector digest; every family-direction reliability/seed-floor decision; final all-family model; complete candidate/proposal payload; complete conflict responsibilities/assignments; and complete P3 memberships.
10. Only after that freeze may the existing exact-row truth/comparator evaluator open the comparator assignments and mapped known-shower truth.

No P3 window, feature, D_SH implementation, OAS rule, fold count/hash rule, seed-floor definition, 0.5 seed-floor minimum, 0.10 negative-tail maximum, classifier setting, sample weighting, responsibility model/threshold, tie rule, ranking term, row filter or evaluator may change for SonotaCo.

## Input eligibility

The exact P3 transport is input-ineligible rather than retuned if any required condition fails, including:
- exact promoted-v8 panel construction cannot be reproduced;
- any family-direction has fewer than 128 deterministic local negatives;
- exact required orbital/geometry fields are unavailable for retained required rows;
- a fold is empty or a held-out family leaks into its own training fold;
- a cross-fit or final logistic fit does not converge under frozen settings;
- any required pretruth artifact cannot be frozen before truth/comparator access.

An input-ineligible panel cannot count as a superiority win and cannot be repaired using outcome-guided filtering or parameter changes.

## Truth and denominator discipline

Within each comparator/year:
- mapped supported showers receive the already-audited `complex_key`;
- all other exact-row IDs are `SPORADIC` for both methods;
- every supported shower with at least four members in that year's exact-row universe is eligible;
- P3 and comparator use exactly the same annual truth denominator and size stratum.

Sugar and HDBSCAN remain separate pairwise universes.

## Metrics

For every comparator/year report:
- exact-row universe size;
- recurrent promoted-v8 seed-family count;
- P3 eligible/reliable family-direction counts and minimum negative count;
- P3 additions, contested candidates and unassigned burden;
- eligible known-shower count;
- macro F1, precision and recall under frozen best-match rules;
- count/fraction of eligible showers with F1 >0.5 and >0.8;
- mean F1 in annual reference-size strata `4–9`, `10–24`, `25–49`, `50–99`, `100+`;
- combined `4–24` mean F1;
- comparator and P3 noise/unassigned burden when defined on common rows.

P3 keeps exact v8 multiplicity ranking. Do not invent a Sugar or HDBSCAN ranking. Ranked internal P3/v8 diagnostics cannot establish literature superiority.

## Frozen superiority classifications

These are exactly the broad/sparse bars already preregistered for v6/P1/P2. P3 receives no easier standard.

Every required annual condition must hold in both 2023 and 2025. Ties do not count as wins.

### `BROAD_CATALOGUE_SUPERIORITY`

Separately against Sugar on its exact-row universe and HDBSCAN on its exact-row universe, all must hold:
1. P3 macro F1 >= comparator macro F1 +0.05 in both years;
2. P3 is not below comparator by >0.05 mean F1 in any nonempty size stratum in either year;
3. P3 exceeds comparator by >=0.10 mean F1 in at least two size strata in each year;
4. P3 has at least as many eligible showers with F1 >0.5 as comparator in each year;
5. all source/input/row/firewall/pretruth/evaluator integrity gates pass.

### `SPARSE_STREAM_SUPERIORITY`

Separately against both Sugar and HDBSCAN, all must hold:
1. `4–9` P3 mean F1 >= comparator +0.10 in both years;
2. combined `4–24` P3 mean F1 >= comparator +0.10 in both years;
3. P3 macro F1 is no more than 0.10 below that comparator in either year;
4. P3 retains >=80% of that comparator's F1>0.5 shower count in each year;
5. all integrity gates pass.

Any non-sparse disadvantage must be reported explicitly.

### `NO_LITERATURE_SUPERIORITY`

If neither classification passes against both comparators, P3 has not beaten the implemented literature methods. Preserve that outcome permanently. Do not alter P3 or this benchmark from the exposed result.

## Information-parity claim boundary

The benchmark is event-row matched and post-freeze-truth matched within each comparator universe. No known-shower or comparator-cluster label enters P3 before the complete P3 payload is frozen. Each method retains its own frozen scientific representation: P3 uses promoted-v8 recurrence plus observation/orbit two-view membership and cross-fit reliability; Sugar/HDBSCAN retain their frozen inputs. A win therefore supports superiority of the complete frozen target-free P3 operational pipeline on these exact-row SonotaCo panels, not a claim of identical feature information.

P3 receives no native SonotaCo shower/background designation for calibration or membership.

## Downstream boundary

A P3 literature pass still does not authorize target access. P3 must then pass a separately frozen no-retuning external/generalization test on an event-value-unexposed panel before final Stage A. MAARSY 2020/2021 remains unopened because P2 failed development before its reserved external route executed; any P3 use requires a P3-specific protocol frozen before first MAARSY 2020/2021 event-value access.

No OrbitTrace coordinate, identity, member, historical target rank/recovery, target-region event, withheld target reference or target-containing output may be accessed anywhere in this comparison.