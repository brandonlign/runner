# OrbitTrace survey-null calibrated persistence v1 — frozen protocol

## Goal

Test one generalization-focused successor to the current density-synchronous recurrent-EOM GMN champion.

The failure we are trying to fix is specific: a cluster can look persistent in one survey because the survey's own nonuniform sporadic background makes that region dense. Meteor-stream literature treats this as a statistical-null problem. Sugar et al. (2017) validated density clustering against simulated sporadic populations; Shober & Vaubaillon (2024) proposed KDE-based false-positive calibration; Shober (2025, 2026) used synthetic/KDE sporadic nulls and solar-longitude randomization to quantify significance, including multi-network GMN/CAMS/EDMOND/SonotaCo analyses.

This successor therefore asks: **is a candidate's combination of size and density-synchronous persistence rarer than structures produced by the same survey after its seasonal coherence is destroyed?**

This is the only mechanism authorized by this protocol.

## Parent

Exact PR #1263 density-synchronous recurrent-EOM HDBSCAN v1, binding head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

The real-data HDBSCAN hierarchy, selected parent memberships, and parent synchronous stability are unchanged.

## Survey-preserving null

For each of exactly `B = 16` null replicates:

1. start from the complete target-excluded GMN 2022+2023 accessible event population;
2. keep each event's year, Sun-centered radiant longitude, ecliptic latitude, geocentric speed, and event identity fixed;
3. within each observing year separately, deterministically permute the observed solar-longitude values among events;
4. therefore preserve exactly, year by year:
   - event count;
   - the complete empirical solar-longitude exposure distribution;
   - the complete empirical radiant/speed distribution;
   - all one-dimensional feature marginals;
5. destroy the event-level joint association between activity phase and radiant/speed that makes a meteor shower seasonally coherent;
6. build the exact same pooled GEO6 representation and exact same HDBSCAN fit;
7. apply exact #1263 density-synchronous recurrent-EOM node selection;
8. record every selected null family's `(member_count, synchronous_stability)`.

Permutation seeds are not tunable. For replicate index `r in 0..15`, the seed is the unsigned 64-bit integer represented by the first eight bytes of:

`SHA256("ORBITTRACE_NULL_CALIBRATED_PERSISTENCE_V1|" + str(r))`.

The same seed is used to initialize NumPy `PCG64`, with independent `permutation()` calls for the sorted 2022 and sorted 2023 event-index arrays.

No hidden shower label, target information, external survey, literature shower template, or post-result quantity may enter a null replicate.

## Parameter-free empirical null-surprise score

For each real #1263 candidate `C`, let:

- `n(C)` be its member count;
- `S(C)` be its exact density-synchronous stability.

For null replicate `r`, containing `M_r` selected families, define:

`d_r(C) = count{N in null_r : n(N) >= n(C) and S(N) >= S(C)}`.

Define the replicate tail rate with a fixed finite-sample pseudocount:

`p_r(C) = (1 + d_r(C)) / (1 + M_r)`.

Define the candidate's survey-null surprise as:

`P_null(C) = mean_r p_r(C)`.

This is an empirical two-dimensional Pareto-tail false-positive rate: a candidate is more significant when structures at least as large **and** at least as persistent are rare in survey-preserving scrambled backgrounds.

No weight between size and persistence is introduced. No bins, KDE bandwidth, threshold, learned model, exponent, z-score cutoff, or fitted coefficient is used.

## Successor ranking

Memberships remain exactly the #1263 real-data memberships.

Sort real candidates by:

1. ascending `P_null(C)`;
2. descending exact #1263 `synchronous_stability`;
3. descending ordinary HDBSCAN stability;
4. descending member count;
5. stable family ID.

The complete successor order must be persisted before hidden known-shower labels are opened.

## Why this is not another arbitrary quality multiplier

Previous failed successors used internal candidate properties (year mixing, rate balance, wavelet score, year shift) to guess which families were better. This method instead estimates the **false-positive background produced by the survey itself** under a frozen coherence-destroying null. It directly targets the demonstrated cross-survey problem: absolute density structures and false positives depend on network sampling and local sporadic background.

The real hierarchy and memberships are intentionally held fixed in this first test so the only question is whether statistically calibrating persistence against each survey's own background improves catalogue ordering. If this fails, this exact null-calibration scheme is closed; it may not be rescued by changing the number of replicates, permutation target, Pareto dimensions, pseudocount, or score combination.

## Protected-data firewall

Before every real or null HDBSCAN fit:

- remove inclusive solar longitude `[20.0,55.0]`;
- OrbitTrace target information/events remain inaccessible;
- SonotaCo 2013/2014 is inaccessible during GMN selection;
- ASFN and EFN are not used for design/tuning/rescue;
- AMOS remains pristine and inaccessible;
- MAARSY and DMS remain inaccessible.

Known-shower truth is opened only after the full real successor order and all null evidence are persisted.

## Frozen GMN success gate

The parent total recovered@100 is `179` (`89` in 2022 and `90` in 2023).

PASS requires **all** of:

1. null mechanism active: successor order differs from parent order;
2. total recovered@100 across 2022+2023 improves by at least `+5`, i.e. successor total >= `184`;
3. recovered@100 not lower in either year;
4. recovered@50 not lower in either year;
5. top-100 dominant precision not lower in either year;
6. MRR not lower in either year;
7. median top-500 fragmentation not higher in either year.

A smaller improvement is a FAIL. The project goal is meaningful superiority, not another +1 development result.

## If and only if GMN passes

Before any SonotaCo execution, freeze a direct SonotaCo 2013/2014 transfer protocol that reconstructs the same survey-preserving null **within each SonotaCo panel itself** and compares against the exact current recurrent-EOM benchmark and frozen literature comparator.

Transfer PASS must require:

- no regression on all four established SonotaCo panels in macro-F1 or recovered count;
- strict improvement on at least two of four panels in macro-F1 or recovered count;
- continued superiority over the corresponding frozen literature comparator on all four panels.

No SonotaCo tuning/rerun is allowed.

Only a method passing both stages may be considered for the single untouched AMOS final test under a separately frozen protocol.

## Permanent failure rule

A technically valid GMN FAIL permanently closes survey-null calibrated persistence v1. No rescue by changing `B`, using KDE instead, using uniform rather than empirical solar longitude, scrambling another feature, altering the Pareto comparison, adding weights, blending with the parent rank, or selecting a favorable subset is authorized from this result.
