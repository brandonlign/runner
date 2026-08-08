# OrbitTrace P2 — preregistered matched-literature protocol

## Status and activation

Protocol-only preregistration frozen before any P1 or P2 scientific result exists.

This protocol is dormant unless the exact frozen P2 development workflow returns `PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT` after the normal succession rule has legitimately reached P2. A P2 development failure leaves this comparison permanently dormant and authorizes no P2 retuning.

No target-containing search is authorized here. Solar longitude 20°–55° remains excluded before recurrent-core construction, P2 feature construction, training, candidate scoring, membership assignment, ranking, or truth evaluation.

## Purpose

Test whether the exact frozen P2 cross-year two-view membership architecture beats the two strongest already-implemented catalogue comparators under pairwise exact-row matched SonotaCo benchmarks:

1. Sugar uncertainty-aware retained-master catalogue reconstruction;
2. Peña-Asensio–Ferrari catalogue HDBSCAN transfer.

The Sugar and HDBSCAN exact-row event universes differ. Every comparison is therefore pairwise; metrics may never be mixed across comparator denominators.

## Immutable competitor artifacts

Reuse the exact competitor assignments and row universes frozen in `orbittrace_literature_matched_v8/EXACT_ROW_PROTOCOL.md` and `COMPETITOR_FREEZE.json`.

### HDBSCAN

- SonotaCo 2023 workflow `31076062060`, assignment SHA-256 `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60`;
- SonotaCo 2025 workflow `31071589912`, assignment SHA-256 `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`.

### Sugar retained-master

- SonotaCo 2023 workflow `31076789635`, assignment SHA-256 `2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389`;
- SonotaCo 2025 workflow `31075178517`, assignment SHA-256 `77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e`.

No competitor may be rerun, retuned, re-filtered, re-ranked, or replaced after P2 outcomes are known.

## Pairwise P2 transport

Run two independent P2 transports:

1. Sugar exact-row universe using the frozen Sugar 2023 and 2025 row sets jointly;
2. HDBSCAN exact-row universe using the frozen HDBSCAN 2023 and 2025 row sets jointly.

For each pairwise transport:

1. Verify the frozen competitor-assignment hashes and extract only the immutable event-ID universe before P2 construction. Competitor cluster labels are unavailable to P2 until after the complete P2 payload is frozen.
2. Resolve every event ID to the immutable SonotaCo scientific row required by exact promoted-v8 core construction and exact P2 features. The P2 inputs are the inherited observation geometry plus the exact orbital elements required by the frozen Southworth–Hawkins implementation. Any event that becomes scientifically required by a v8 seed/template or P2 candidate pair but lacks a valid frozen P2 input is an interface/integrity failure; the row universe may not be silently shrunk after seeing labels or outcomes.
3. Remove solar longitude 20°–55° before using any retained-row geometry/orbit value.
4. Using only the allowed pairwise rows, reconstruct the exact promoted-v8 recurrent cores and exact promoted-v8 multiplicity order under source commit `c9d6c44704013ba0c9430100e98a29a56b453304`. The different row universe is the only transport change.
5. Treat 2023 and 2025 as the two cross-year directions. For every immutable recurrent family, construct the exact frozen P2 source-year observation template, OAS covariance, `d_obs`, nearest-opposite-year-seed exact `d_orb`, weighted self-supervised positives/negatives, deterministic `StandardScaler`, and fixed `LogisticRegression` exactly as in the P2 protocol.
6. The inherited P2 eligibility rule remains exact: every family direction requires at least 128 non-seed negatives in the deterministic ±5° target-year window. Failure is an input-ineligibility result for that pairwise panel; it does not authorize changing the window, negative rule, or family set after seeing outcomes.
7. Train exactly one global two-feature classifier pooled across all eligible frozen family directions in that pairwise transport, with the exact family/direction equal weighting, solver, C, tolerance, and convergence requirement already frozen by P2.
8. Freeze and SHA-256 hash the scaler state, classifier coefficients/intercept, complete candidate-pair feature payload, complete conflict responsibilities, final memberships, exact v8 seed/core identity, and exact multiplicity order before any known-shower truth or competitor cluster label is exposed to evaluation.
9. Only after the pre-truth freeze, load the frozen competitor assignments and common SonotaCo mapped truth and evaluate P2 and that comparator on identical rows under the exact prior exact-row matching/tie rules.

No P2 feature, D_SH implementation, OAS rule, negative window, classifier option, sample weight, responsibility background weight, responsibility threshold, tie rule, ranking term, event filter, year pair, or evaluator may change for SonotaCo.

## Truth and denominator discipline

Within each comparator/year, preserve the prior exact-row truth convention:

- mapped supported showers receive their audited `complex_key`;
- all other exact-row IDs are `SPORADIC` for both methods;
- every supported shower with at least four members in that year's exact-row universe is eligible;
- P2 and the comparator use the same annual truth denominator and the same size stratum.

Sugar and HDBSCAN universes remain separate. A metric from the Sugar universe may not be compared directly to a metric from the HDBSCAN universe.

If an integrity/input-eligibility failure prevents P2 from producing a valid pairwise panel, that panel cannot be counted as a superiority win and the failure may not be repaired by outcome-guided row filtering.

## Metrics

For each comparator/year report:

- exact-row universe size;
- recurrent v8 seed-family count produced before P2;
- eligible P2 family-direction count and negative-count minimum;
- P2 added-member and unassigned counts;
- eligible known-shower count;
- macro F1, macro precision, and macro recall under frozen best-match rules;
- count/fraction of eligible showers with F1 >0.5 and F1 >0.8;
- mean F1 in annual reference-size strata `4–9`, `10–24`, `25–49`, `50–99`, and `100+`;
- combined `4–24` mean F1;
- comparator and P2 noise/unassigned burden when defined on the common rows.

P2 preserves the exact v8 multiplicity ranking. Do not invent a ranking for Sugar or HDBSCAN. Ranked-discovery metrics may be reported only as P2/v8 internal diagnostics and cannot establish literature superiority.

## Frozen superiority classifications

These are the same broad/sparse bars already preregistered for v6 and P1. P2 receives no easier standard after either predecessor's result.

Every required annual condition must hold in both 2023 and 2025. A tie is not a win.

### `BROAD_CATALOGUE_SUPERIORITY`

The following must hold separately against Sugar on the Sugar exact-row universe and against HDBSCAN on the HDBSCAN exact-row universe:

1. P2 macro F1 >= comparator macro F1 +0.05 absolute in both years;
2. P2 is not below that comparator by >0.05 absolute mean F1 in any nonempty size stratum in either year;
3. P2 exceeds that comparator by >=0.10 absolute mean F1 in at least two size strata in each year;
4. P2 has at least as many eligible showers with F1 >0.5 as that comparator in each year;
5. all source, exact-row, P2-input, target-firewall, pre-truth-freeze, and evaluation-integrity gates pass.

### `SPARSE_STREAM_SUPERIORITY`

This authorizes only a scoped sparse/small-population superiority claim. Separately against both Sugar and HDBSCAN:

1. `4–9` P2 mean F1 >= comparator +0.10 in both years;
2. combined `4–24` P2 mean F1 >= comparator +0.10 in both years;
3. P2 macro F1 is no more than 0.10 absolute below that same comparator in either year;
4. P2 retains at least 80% of that comparator's F1>0.5 shower count in each year;
5. all integrity gates pass.

Any non-sparse disadvantage must be reported explicitly.

### `NO_LITERATURE_SUPERIORITY`

If neither classification passes against both comparators, P2 has not beaten the implemented literature methods. Preserve the result permanently and do not alter P2 or the benchmark from the exposed outcome.

## Information-parity claim boundary

The comparison is event-row matched and post-freeze-truth matched within each comparator universe, and no known-shower or competitor-cluster label enters P2 before membership freeze. However, the methods intentionally use their own frozen scientific feature spaces: P2 uses its two-view observation-plus-orbit representation, while Sugar and catalogue HDBSCAN retain their published/frozen inputs. Therefore a win supports superiority of the frozen target-free P2 operational method on these exact-row SonotaCo panels, not a claim that all three algorithms were supplied an identical feature representation.

Unlike catalogue-v6's matched benchmark, P2 receives no native SonotaCo shower/background designation as calibration input. Its positives are immutable self-supervised v8 family seeds and its negatives are unlabeled non-seed events selected solely by the frozen local-window rule.

## External and target boundary

A P2 literature pass does not authorize OrbitTrace target access. P2 must then pass a separately frozen no-retuning held-out/external validation. MAARSY 2020/2021 is separately reserved as an event-value-unexposed fallback panel if the normal decision tree reaches P2 and freshness remains intact, but this literature protocol itself does not authorize opening it.

Only after P2 development, literature, and external/generalization gates all pass may a final blind target-containing deployment be separately frozen and executed.

No OrbitTrace coordinate, identity, member, prior target rank/recovery, target-region event, or target-containing output may be accessed or used anywhere in this comparison.
