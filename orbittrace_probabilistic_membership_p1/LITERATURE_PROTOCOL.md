# OrbitTrace probabilistic membership P1 — preregistered matched-literature protocol

## Status and activation

This protocol is frozen before any P1 scientific development result exists. It is dormant unless the exact P1 development workflow returns `PASS_PROBABILISTIC_MEMBERSHIP_P1_DEVELOPMENT` under the frozen P1 protocol. A P1 failure leaves this comparison permanently dormant and authorizes no P1 retuning.

This protocol executes no target-containing search. Solar longitude 20°–55° remains excluded before geometry construction, core generation, P1 membership assignment, ranking, or truth evaluation.

## Purpose

The comparison asks whether the exact frozen P1 post-core membership architecture, when transported without retuning, beats the two strongest implemented catalogue comparators already frozen in the repository:

1. Sugar uncertainty-aware retained-master catalogue reconstruction;
2. Peña-Asensio–Ferrari catalogue HDBSCAN transfer.

The benchmark is pairwise exact-row matched. The Sugar and HDBSCAN event universes differ, so no metric may be compared across those two denominators.

## Immutable comparator inputs

Reuse the exact competitor assignment artifacts and exact-row definitions frozen in `orbittrace_literature_matched_v8/EXACT_ROW_PROTOCOL.md` and `COMPETITOR_FREEZE.json`.

### HDBSCAN

- 2023 workflow `31076062060`, assignment SHA-256 `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60`;
- 2025 workflow `31071589912`, assignment SHA-256 `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`.

### Sugar retained-master output

- 2023 workflow `31076789635`, assignment SHA-256 `2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389`;
- 2025 workflow `31075178517`, assignment SHA-256 `77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e`.

No competitor is rerun, retuned, re-filtered, re-ranked, or replaced after P1 outcomes are known.

## Pairwise transport of the frozen P1 method

Run two independent P1 transports:

1. Sugar exact-row universe, jointly using the frozen Sugar 2023 and 2025 row sets;
2. HDBSCAN exact-row universe, jointly using the frozen HDBSCAN 2023 and 2025 row sets.

Within each pairwise universe:

1. Resolve every competitor event ID to its immutable SonotaCo geometry row. Missing, duplicated, structurally invalid, or target-interval rows fail the panel rather than silently changing the universe.
2. Before any shower token or mapped truth is read, construct the exact promoted-v8 recurrent cores and exact promoted-v8 multiplicity order using source commit `c9d6c44704013ba0c9430100e98a29a56b453304`, with only the allowed event-ID universe changed.
3. Treat SonotaCo 2023 and 2025 as the two years supplied to P1. Reconstruct year-specific pooled centroids from immutable v8 seeds, pool seed-only residuals across those two years, fit the same OAS covariance, use the same 99% candidate ellipsoid, the same 99%–99.99% background shell, the same one-sided 95% Garwood upper bound, and the same strict responsibility >0.5 assignment rule.
4. Seeds never move. Added members never refit, recurse, seed growth, or alter the exact v8 multiplicity ranking.
5. Serialize and SHA-256 freeze the complete v8 core/ranking identity and complete P1 membership payload before invoking the common SonotaCo truth parser.
6. Only after that freeze, evaluate P1 and the frozen comparator on identical rows and identical mapped truth under the exact existing tie rules.

No P1 probability, covariance choice, shell, containment probability, responsibility threshold, ranking term, event filter, year pairing, or matching rule may change for SonotaCo.

## Truth and denominator discipline

For each comparator/year, use the exact common-label rules from the prior v8 exact-row benchmark:

- mapped supported showers receive their audited `complex_key`;
- all other exact-row IDs are `SPORADIC` for both methods;
- every supported shower with at least four members in that year's exact-row set is eligible;
- P1 and the comparator use identical annual shower-size denominators and size bins.

The Sugar and HDBSCAN exact-row universes remain separate. Cross-comparator denominator mixing is forbidden.

## Metrics

For each comparator and year report:

- eligible shower count;
- macro F1, macro precision, and macro recall under frozen best-match rules;
- number/fraction of eligible showers with F1 >0.5 and F1 >0.8;
- mean F1 in annual reference-size strata `4–9`, `10–24`, `25–49`, `50–99`, and `100+`;
- combined `4–24` mean F1;
- comparator noise/unassigned burden where its frozen output supports it;
- P1 unassigned burden and added-member count.

Because P1 preserves the exact v8 ranking, do not invent a Sugar/HDBSCAN ranking. Ranked-discovery metrics may be reported only as P1/v8 internal diagnostics and cannot establish literature superiority.

## Frozen superiority classifications

These bars deliberately reuse the v6 matched-literature thresholds frozen before either v6 or P1 outcomes. P1 receives no easier post-result standard.

Every required annual condition must hold in both 2023 and 2025. A tie is not a win.

### `BROAD_CATALOGUE_SUPERIORITY`

The following must hold separately against Sugar on the Sugar exact-row universe and against HDBSCAN on the HDBSCAN exact-row universe:

1. P1 macro F1 >= comparator macro F1 +0.05 absolute in both years;
2. P1 is not below that comparator by >0.05 absolute mean F1 in any nonempty size stratum in either year;
3. P1 exceeds that comparator by >=0.10 absolute mean F1 in at least two size strata in each year;
4. P1 has at least as many eligible showers with F1 >0.5 as that comparator in each year;
5. all source, exact-row, target-firewall, pre-truth-freeze, and evaluation-integrity gates pass.

### `SPARSE_STREAM_SUPERIORITY`

This supports only a scoped sparse/small-population superiority claim. Separately against both Sugar and HDBSCAN:

1. `4–9` P1 mean F1 >= comparator +0.10 in both years;
2. combined `4–24` P1 mean F1 >= comparator +0.10 in both years;
3. P1 macro F1 is no more than 0.10 absolute below that same comparator in either year;
4. P1 retains at least 80% of that comparator's F1>0.5 shower count in each year;
5. all integrity gates pass.

Any non-sparse disadvantage must be reported explicitly.

### `NO_LITERATURE_SUPERIORITY`

If neither classification passes against both comparators, P1 has not beaten the implemented literature methods. Preserve the result and do not relax thresholds or retune P1 from the exposed benchmark.

## Information-parity claim boundary

Unlike catalogue-v6's native-background-calibrated matched benchmark, P1 receives only the pairwise exact-row geometry and its own immutable v8 seed/core outputs before truth. Native SonotaCo shower designations, mapped catalogue labels, and competitor cluster labels are forbidden from P1 core generation, covariance/background fitting, membership assignment, and ranking.

Therefore, provided the implementation audit confirms this protocol exactly, a P1 literature win may be described as an event-row-matched, truth-matched, detector-input-geometry-matched comparison against the implemented Sugar/HDBSCAN transports. It still does not establish universal superiority over methods or survey regimes not faithfully represented here.

## External and target boundary

A P1 matched-literature pass does not authorize target access. P1 must subsequently pass a separately frozen no-retuning external/held-out generalization protocol. Only after development, literature, and generalization gates all pass may a final blind target-containing deployment be frozen and executed.

No OrbitTrace coordinate, identity, member, prior target rank, target-region event, or target-containing output may be accessed or used anywhere in this comparison.
