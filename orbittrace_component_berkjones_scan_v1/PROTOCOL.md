# OrbitTrace component-conditioned Berk-Jones graph scan v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is a new two-stage stream detector motivated by the established zero-label/sample-size results and the binding truth pattern of the fixed-graph topomodal family:

1. The fixed 5 deg solar / 4 deg radiant / 10% speed physical radius graph yields broad connected families that remain substantially more coherent than recurrent-EOM under ~8x thinning.
2. Those broad families recover many more known streams than recurrent-EOM with higher purity and fragmentation 1, but existing peak/mean density ordering does not surface them early enough.
3. Aggressively replacing a broad family by multiparameter threshold states improves MRR but catastrophically fragments recovery.
4. Finite-mode prominence significance does not solve the problem: the frozen max-prominence permutation test retained zero finite modes in all eight sparse panels, while the broad physical components still retained the recovery advantage.

The present method therefore **keeps every broad physical component intact as the reported candidate** and uses a distribution-free internal scan statistic only as evidence for candidate ordering. No internal subset, threshold state, mode, or scan optimum becomes a separate candidate.

The evidence mechanism is the one-sided Berk-Jones goodness-of-fit / nonparametric scan statistic applied to each component's survey-relative local-density ranks. This asks whether the intact component contains an unusually large concentration of very high local-density events, even if a lower-density halo dilutes its mean density. Candidate-size calibration is performed before truth by deterministic sampling without replacement from the exact empirical rank population.

This is distinct from the closed generic multiscale subset scan, which searched 4/6/8-event nearest-neighbor subsets inside 128-event windows with conformal calibration. Here there is no window, no chosen subset size, no internal subset output, and no candidate membership optimization: the connected physical component is fixed first and remains the candidate.

The first technically valid outcome is binding. No post-result rescue is permitted.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data.

Remove inclusive solar longitude `[20.0,55.0]` before geometry, nearest-neighbor density ranks, physical graph construction, connected components, null calibration, candidate scoring/ranking, cross-scale comparison, or truth evaluation.

Forbidden:

- OrbitTrace target information or protected-region events;
- SonotaCo event/truth access during GMN development;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements in candidate construction or evidence;
- shower labels in candidate construction, score calibration, or ranking;
- result-informed p-value cutoff, scan truncation, candidate-size rule, k, graph radius, physical bandwidth, null replicate count, tie rule, metric, or promotion-gate change.

## 2. Exact sparse development panels

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Evaluate exactly eight pooled target-excluded GMN 2022+2023 subsets:

- denominator `128`, buckets `0,1,2,3` (~5.8k pooled events each);
- denominator `1024`, buckets `0,1,2,3` (~0.7k pooled events each).

No extra salt, denominator, bucket, bootstrap, or replicate panel is authorized.

## 3. Survey-relative event evidence — exact support-4 density rank

For each pooled sparse subset independently, reconstruct selected-parent GEO6:

`X = (cos(sol), sin(sol), sin(sun_lon)cos(ecl_lat), cos(sun_lon)cos(ecl_lat), sin(ecl_lat), vg/72)`.

For every event compute exact Euclidean distance `r3(i)` to its **third nearest other event**.

Sort all events from locally densest to sparsest by ascending `(r3(i), event_id)`. Assign deterministic one-based rank `rank_i` and event p-value

`p_i = rank_i/(n+1)`.

Equivalently `q_i = 1-p_i`. Smaller `p_i` means stronger local-density evidence.

The support-4/third-other-neighbor definition is inherited from the pre-outcome rank-density experiments and is not reselected here. No alternate k, annual split, ECDF convention, transform, local scaling, or smoothing is permitted.

## 4. Broad candidate construction — physical connected components only

Construct the exact #1284 physical embedding:

- `h_sol = 2 sin(5 deg/2)`;
- `h_rad = 2 sin(4 deg/2)`;
- `h_logv = ln(1.1)`;
- `Z = [cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`.

Construct the exact symmetric Euclidean radius graph at `r=1.0`, including self in stored radius-neighbor lists exactly as #1284.

Candidate memberships are **exact connected components of this fixed graph**. Report every component with membership size >=4. Components below support 4 are discarded only after graph connectivity is complete.

No ToMATo finite mode, internal merge node, MST, HDBSCAN tree, kNN graph, graph cut, spectral split, threshold state, local community, or other subcomponent is a candidate.

Candidate prefix: `CBJ1`.

### Membership identity audit

Before truth, direct connected-component memberships must match the broad/root memberships from the immutable significance-pruned fixed-graph prelabel (`bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a`) for all eight sparse panels, after support >=4 and ignoring rank/evidence fields. This is an engineering identity audit only; no prior truth metric or verdict enters the successor.

## 5. One-sided Berk-Jones component evidence

For a candidate component `C` containing `m` events, sort its frozen event p-values:

`p_(1) <= ... <= p_(m)`.

For each `k=1..m`, let `x=k/m` and `a=p_(k)`.

If `a < x`, define the one-sided binomial log-likelihood ratio

- for `x < 1`:

`BJ_k = m * [ x log(x/a) + (1-x) log((1-x)/(1-a)) ]`;

- for `x = 1`:

`BJ_k = m * log(1/a)`.

If `a >= x`, set `BJ_k=0`.

The component's raw scan evidence is

`BJ(C) = max_k BJ_k`.

Record the earliest `k` attaining the maximum as `BJ_argmax_k` solely for audit; it never changes candidate membership and is not a ranking tie-break.

There is **no alpha truncation**, no maximum scan fraction, no selected p-value threshold, no Higher-Criticism alternative, and no internal subset output. The maximum uses the full frozen one-sided Berk-Jones statistic.

## 6. Size-conditioned label-free calibration

Raw Berk-Jones null distributions vary with component size. Calibrate candidate evidence before truth while conditioning exactly on the observed global empirical p-value population and each candidate size.

Use exactly `B=999` null draws for every distinct reportable component size `m` in each sparse panel.

For null replicate `b=1..999`, seed NumPy `PCG64` with

`uint64_be(SHA256('ORBITTRACE_COMPONENT_BJ_V1|' + denominator + '|' + bucket + '|' + m + '|' + b)[0:8])`.

Draw exactly `m` event indices uniformly without replacement from the panel's `n` events using `Generator(PCG64(seed)).choice(n, size=m, replace=False, shuffle=False)`. Apply the exact same one-sided `BJ` function to those sampled empirical p-values.

For observed component `C` of size `m`, define

`p_BJ(C) = (1 + #{b: BJ_null(m,b) >= BJ(C)}) / 1000`.

This null does not search graph subsets or alter geometry. It asks only whether an already-fixed component's internal density-rank tail is unusually enriched relative to a random size-m subset of the same survey sample.

No significance threshold is applied: all support>=4 connected components remain candidates regardless of `p_BJ`.

## 7. Frozen candidate ranking

Rank all reportable connected components lexicographically by:

1. ascending `p_BJ`;
2. decreasing raw `BJ(C)`;
3. decreasing maximum event density rank `q_max = max(1-p_i)`;
4. deterministic family hash ascending.

`q_max` is only a deterministic deep tie-break after identical Monte Carlo p-value and raw Berk-Jones evidence. No component size, mean density, year balance, recurrence, graph spectral quantity, detector score, learned model, or weighted blend enters ranking.

## 8. Exact recurrent-EOM comparator

On each identical subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- GEO6 exactly;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary HDBSCAN condensed hierarchy;
- exact annual-normalized recurrent-EOM contribution;
- exact FOSC/EOM extraction;
- selected-parent ranking by recurrent stability, ordinary stability, member count, deterministic family ID.

Comparator candidate membership/count summaries must reproduce the immutable #1284 structural artifact before truth opens.

## 9. Immutable prelabel boundary

Before known-shower truth is loaded, serialize and SHA-256 seal for every sparse panel:

- event-universe hash and annual totals;
- `r3`, empirical rank, and p-value hashes;
- exact physical graph hash, edge count, and degree summaries;
- every support>=4 connected-component membership;
- every raw `BJ`, `BJ_argmax_k`, component size, `p_BJ`, `q_max`, and final rank;
- all 999 null BJ values for every distinct component size and their hashes;
- comparator memberships and ranks;
- candidate-budget sufficiency;
- frozen cross-scale metrics below;
- all source/artifact/firewall hashes.

Write `COMPONENT_BERKJONES_SCAN_V1_PRELABEL.json`, verify it in an independent workflow step, and only then load truth.

A failure before the sealed prelabel exists is an engineering no-result. Any repair must preserve every scientific definition above exactly.

## 10. Frozen cross-scale generalization gates

Use the exact #1284 fine->coarse candidate-mean best-Jaccard semantics on the broad connected-component candidate memberships.

For each bucket:

1. denominator-1024 is the fine event universe;
2. restrict denominator-128 components to that fine universe and discard restricted memberships below support 4;
3. for every fine successor component compute maximum Jaccard against retained restricted coarse successor components;
4. compute the identical measure for recurrent-EOM.

Require before truth:

**S1.** successor pooled fine->coarse mean-best-Jaccard strictly greater than recurrent-EOM;

**S2.** successor strict fine->coarse bucket wins in at least `3/4` buckets.

The cross-scale result is frozen in the prelabel and cannot modify component evidence or ranking.

## 11. Truth semantics and equal reporting budget

After prelabel seal only, use the selected recurrent-EOM parent's existing `metrics(...)` semantics unchanged, separately for 2022 and 2023 within every pooled subset.

For each subset let `K` be the number of recurrent-EOM candidates.

Promotion requires at least K successor components before truth. Evaluate:

- all K recurrent-EOM candidates;
- exactly the first K frozen component-BJ candidates.

No component may be padded, split, or replaced if candidate count is insufficient.

Truth semantics remain exactly:

- annual shower eligibility >=4 events;
- positive candidate/shower match requires precision >=0.5 and overlap >=4;
- qualified matches;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- MRR;
- median top-500 fragmentation.

## 12. Frozen truth gates

Use exactly the same ten truth gates as the recent fixed-graph sequence.

### Fine sparse scale d=1024

T1. successor qualified total strictly greater than recurrent-EOM;
T2. qualified matches nonlower in at least 6/8 annual panels;
T3. mean MRR not lower;
T4. mean top-100 dominant precision not lower;
T5. mean fragmentation not higher.

### Coarse scale d=128

T6. successor qualified total not lower;
T7. qualified matches nonlower in at least 6/8 annual panels;
T8. mean MRR not lower;
T9. mean top-100 dominant precision not lower;
T10. mean fragmentation not higher.

## 13. Promotion verdict

Return

`PASS_COMPONENT_BERKJONES_SCAN_V1`

iff:

- candidate budget is sufficient in all eight sparse subsets;
- structural gates S1-S2 both pass;
- truth gates T1-T10 all pass.

Otherwise return

`FAIL_COMPONENT_BERKJONES_SCAN_V1`.

There is no partial promotion and no post-result rescue.

## 14. Distinction from closed lanes

This architecture is not:

- complete/rank-density ToMATo plus a new hierarchy rank: there is no finite hierarchy at all;
- significance-pruned ToMATo: no finite-mode prominence or significance threshold exists;
- bivariate density persistence: no annual threshold lattice or exact-state candidates;
- generic multiscale subset scan: no 128-event windows, 4/6/8 subset search, or conformal scale search;
- rank-density MST/EOM: no MST, branch lifetime, branch mass, or FOSC/EOM extraction;
- null-calibrated persistence: candidate membership is direct physical connectivity and Berk-Jones is component-internal evidence, not post-selection calibration of an existing detector score;
- local-background/trajectory contrast: no local background window, trajectory statistic, or density subtraction is used;
- recurrent/cross-year hard confirmation: year identity does not enter candidate construction or BJ evidence.

## 15. Conditional exposed SonotaCo transfer

Before the first technically valid GMN truth result, freeze a separate conditional SonotaCo 2013/2014 transfer protocol using the exact historical four-panel evaluator and selected recurrent-EOM controls. Execute only if GMN returns full PASS.

SonotaCo remains EXPOSED DEVELOPMENT ONLY.

## 16. Interpretation

A PASS would be the first method in this sequence to combine:

- broad physical-component membership stable under severe sample-size change;
- internal distribution-free evidence sensitive to a dense stream core without fragmenting the reported family;
- superior sparse known-stream recovery;
- noninferior early ranking/MRR;
- noninferior purity and fragmentation.

A FAIL closes this exact third-neighbor empirical-p + fixed radius-1 physical connected components + full one-sided Berk-Jones + B=999 size-conditioned calibration + frozen ranking architecture. Do not rescue via scan truncation, alpha, B, component-size priors, k, graph scale, candidate splitting, BJ variants, Higher Criticism, rank-sum replacement, or alternative tie-breaks.