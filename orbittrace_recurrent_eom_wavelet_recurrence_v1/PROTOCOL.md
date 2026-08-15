# OrbitTrace recurrent-EOM wavelet-recurrence v1 — frozen protocol

## Status and authority

This protocol is frozen before implementation and before the first scientific outcome.

The owner explicitly reopened method development after the earlier method-selection closure because the current recurrent-EOM method has not demonstrated strong enough cross-survey generalization. This new work does not rewrite or invalidate any prior result, and it does not alter the sealed AMOS protocol or access AMOS data.

Exact parent: recurrent-EOM HDBSCAN v1 selected in PR #1243.

Binding parent GMN development evidence: run `31827903547`, artifact `9229646556`.

- parent prelabel SHA-256: `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`
- parent result SHA-256: `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`
- exact recurrent-EOM kernel Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- exact recurrent-EOM development runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- binding candidate count: `2,097`

## Independent motivation

A previously frozen OrbitTrace multi-anchor wavelet-energy statistic, developed independently of the current recurrent-EOM lineage, beat the frozen Brown-family wavelet continuous ranking on SonotaCo 2025 and then again under unchanged transfer to SonotaCo 2023.

Exact v3 source Git blob: `2ba4835db23f8f623cdd28d0a4e6113b7954ecb2`.

The v3 statistic uses the frozen Brown-family local geometry but replaces a single strongest anchor with the L2 energy of the four strongest positive leave-one-out anchor coefficients. Its constants are already fixed:

- angular probe: `4 deg`
- speed probe: `10%` of test-location geocentric speed
- truncation radius: `4`
- kernel dimension: `3`
- top anchors: `4`

This successor asks a new catalogue-scale question: can the cross-survey-transferable local wavelet evidence improve the ordering of already-selected recurrent-EOM families when recurrence is enforced across years?

## Scientific change

This is a rank-only successor. It consumes the exact binding recurrent-EOM candidate membership universe and must not refit HDBSCAN, alter the hierarchy, change membership, change GEO6, or add/remove candidates.

For each binding candidate `C`:

1. Split its exact member events by year into `C_2022` and `C_2023`.
2. For each year independently, compute the exact frozen v3 multi-anchor wavelet-energy statistic on only that year's members using sun-centered radiant longitude, ecliptic latitude, and geocentric speed.
3. If a year contains fewer than four candidate members, define that year's v3 energy as exactly `0.0`, matching the frozen v3 statistic's minimum supported episode size rather than extrapolating it.
4. Define the catalogue recurrence score

   `R_wave(C) = min(W_2022(C), W_2023(C))`.

5. Rank candidates descending by:

   - `R_wave`;
   - parent recurrent stability;
   - parent ordinary stability;
   - member count;
   - deterministic family ID.

No normalization by family size, exponent, pseudocount, blending weight, learned coefficient, fitted threshold, ECDF transform, rank fusion, or post-result adjustment is allowed.

The method is intentionally simple: candidate generation remains recurrent-EOM; ranking asks for strong frozen v3 local evidence in both years.

## GMN development corpus and firewall

The sole first development outcome uses target-excluded GMN 2022+2023 through the exact frozen runtime utility already used by the binding recurrent-EOM experiment.

The following remain inaccessible:

- protected solar-longitude interval `[20.0 deg, 55.0 deg]`, inclusively;
- OrbitTrace target information and target events;
- SonotaCo 2013/2014 until and unless the GMN activation gate below passes;
- AMOS scientific data;
- MAARSY scientific data;
- DMS scientific data.

The complete successor order must be persisted and hash-frozen before known-shower truth is opened. The first technically valid GMN outcome is binding.

## Exact parent metrics

### 2022

- recovered@25: `22`
- recovered@50: `45`
- recovered@100: `89`
- recovered@500: `193` (reporting only)
- top-100 dominant precision: `0.7856486012780942`
- MRR: `0.022498269587309373`
- qualified matches: `236`
- median top-500 fragmentation: `1.0`

### 2023

- recovered@25: `23`
- recovered@50: `46`
- recovered@100: `89`
- recovered@500: `192` (reporting only)
- top-100 dominant precision: `0.7867680236864514`
- MRR: `0.0220239288966045`
- qualified matches: `244`
- median top-500 fragmentation: `1.0`

## Strong GMN promotion gate

A GMN development PASS requires all of the following:

1. mechanism active: successor order differs from parent order;
2. exact candidate count remains `2,097`;
3. exact membership universe remains identical to the binding recurrent-EOM parent;
4. in each year separately, successor must not regress parent on:
   - recovered@50;
   - recovered@100;
   - top-100 dominant precision;
   - MRR;
   - median top-500 fragmentation;
5. total recovered@100 across 2022+2023 must improve by at least `+2` over the parent total of `178`.

The stronger `+2` requirement is deliberate. A one-candidate gain is no longer sufficient after the density-synchronous lineage showed that such a gain could disappear under perturbation.

A GMN PASS is development evidence only, not external validation.

## Pre-frozen SonotaCo contingency

Only if the first technically valid GMN result passes the strong gate above may this exact unchanged successor be evaluated on the already-exposed SonotaCo 2013/2014 benchmark.

The SonotaCo role remains `EXPOSED_DEVELOPMENT_VALIDATION_ONLY`, never pristine external validation.

The SonotaCo successor must use the exact same v3 constants, annual minimum rule, and tie-breaking rule. No parameter or formula may change after GMN.

For SonotaCo promotion over recurrent-EOM, require:

- no macro-F1 regression versus recurrent-EOM on any of the four established Sugar/HDBSCAN year panels;
- no recovered-count regression versus recurrent-EOM on any panel;
- strict macro-F1 improvement on at least two of the four panels;
- continued superiority over the corresponding frozen literature comparator on all four panels.

If GMN fails, this SonotaCo contingency remains dormant and must not execute.

## Robustness requirement before any final-method claim

Even if both GMN and SonotaCo pass, this method is not yet a final externally validated method. Before replacing recurrent-EOM in a paper claim, it must also survive a separately frozen perturbation/robustness diagnostic showing that its GMN improvement does not collapse under deterministic training perturbations.

AMOS remains untouched and cannot be used to develop, rescue, tune, or choose this method.

## Permanent no-rescue rule

After the first technically valid GMN outcome, this exact version may not be rescued by changing:

- top-anchor count;
- angular or speed scale;
- truncation radius or kernel dimension;
- annual combiner (`min`);
- minimum annual member count;
- score normalization;
- parent-score blend;
- family-size adjustment;
- thresholds or gates;
- HDBSCAN settings;
- candidate membership;
- tie-breaking;
- metric definition.

A failure is a binding negative result. Any scientifically distinct successor must be separately motivated, separately named, and frozen before its own first outcome.
