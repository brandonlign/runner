# OrbitTrace v41 component-minimum multiplicity-calibrated representative selector v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after exact v31, failed v39/v40, diagnostic #1083, and diagnostic #1086. SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**.

The fixed 229-family HDB universe already has sufficient joint nested headroom (#1071): one nested top-9 subset of a top-11 set can clear both HDB literature pair gates, and only two distinct incoming strict groups are required by the truth-aware oracle. Those identities are diagnostic-only and non-promotable.

v40 established that cross-route connected-component evidence is scientifically relevant but its raw minimum member percentile is too broad and damaged HDB14. Diagnostic #1083 then identified a concrete structural defect in that raw component minimum: **best-of-many multiplicity bias**. Component size had strong negative Spearman correlation with raw minimum rank percentile, and the canonical minimum-order-statistic calibration

`q(C) = 1 - (1 - p_min(C))^m(C)`

reduced the absolute size dependence in all three preregistered component universes (all, Sugar-bearing, HDB-bearing) without evaluating any q-based order or SonotaCo panel.

v41 tests exactly one successor implied by #1083: retain v40's frozen physical components and representative architecture, but rank components by the calibrated `q(C)` instead of the biased raw minimum percentile `p_min(C)`.

Diagnostic #1086 independently showed that missed recoverable HDB groups are often suppressed by v31 relative to the immutable pre-SonotaCo #839/#853 quality order, but **v41 does not use that quality-suppression statistic at all**. It is reserved as an independent diagnostic signal for possible later work if v41 fails. This avoids an arbitrary two-signal fusion.

## Immutable parent and provenance

The exact failed v40 scientific source is mounted read-only from commit `31704c312c09be2765ad3f65a0685d1acfd2b055` and its `train_evaluate.py` blob must equal `710944a43111e72ed286b3a5c06010db619c807f`.

v41 reuses from that exact source without modification:

- the immutable #950 71D pretruth features and family memberships;
- exact #1064 radius-1 Sugar↔HDB graph construction;
- exact #1072 ordinary connected-component identity;
- strict whole-shower five-fold OOF assignment;
- fold-training z-score;
- Euclidean k=1 annual positive-vs-nonpositive distance margin;
- annual `min` combiner;
- exact #839 diversity (`lambda=0.8`, `scale=1.0`);
- one equal rank-sum with exact v19;
- one best-own-route representative per component;
- all representatives emitted before any secondary fragment;
- exact candidate memberships, evaluator, literature budgets, and pair-gate definition.

The pretruth graph must reproduce SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25` and the pretruth component identity must reproduce SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd` before exposed truth is loaded.

## Exact v31 parent controls

Before v41 is scientifically evaluated, exact v31 must reproduce:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and produces no v41 scientific outcome.

## Sole v41 scientific change

Let route `r` contain `N_r` candidates and let `rank_r(i)` be candidate `i`'s one-indexed exact v31 fused rank. Define the normalized rank percentile

`p_r(i) = (rank_r(i)-1)/(N_r-1)`.

For every frozen connected component `C`, define

`p_min(C) = min p_r(i)`

over every Sugar and HDB member `i` of `C`.

Let

`m(C) = total number of frozen Sugar + HDB candidate vertices in C`.

The sole v41 component evidence is the canonical minimum-order-statistic calibration diagnosed in #1083:

`q(C) = 1 - (1 - p_min(C))^m(C)`.

For each route `r`, define its representative exactly as v40:

`R_r(C) = own-route member of C with the smallest exact v31 fused rank`.

Construct one complete v41 total order per route in two fixed phases:

1. **Primary component representatives.** Sort every component having an own-route member by `(q(C), rank_r(R_r(C)), component_id)` and emit exactly `R_r(C)` once.
2. **Secondary fragments.** After every own-route component has emitted one representative, append all remaining candidates in their original exact v31 fused order.

No other score, coefficient, threshold, exponent, pseudocount, effective component size, clipping, rank window, or quality-prior term is permitted.

## Why this is a distinct successor rather than a v40 rescue

v40's exact raw-minimum ordering is permanently rejected. v41 exists only because a **separate, preregistered post-v40 diagnostic (#1083)** identified a specific statistical defect in that minimum and fixed one canonical correction before any q-based order or panel was evaluated. v41 is therefore a separately frozen successor with a new scientific score definition, not a post-result parameter tweak inside v40.

## Binding development gate

Exactly one v41 total order per route is evaluated. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires both:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- candidate recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires **4/4** panel wins.

If v41 fails, this exact `q(C)` component evidence plus v40 representative/two-phase ordering is permanently rejected. No alternate exponent, effective-size fit, pseudocount, component-size cap, route-specific calibration, quality-suppression fusion, secondary insertion change, component representative change, graph pruning, threshold, rank window, or budget/year-specific rescue is authorized within v41.

If v41 passes 4/4, freeze only the exact exposed-development reference material required to reproduce it. A pass is **not external validation** and does not authorize a protected cross-survey claim.

## Explicit non-search commitments

No:

- q exponent/coefficient/pseudocount/effective-size search;
- component-size threshold/cap;
- alternative order-statistic calibration;
- route/year/budget-specific calibration;
- quality-prior fusion or suppression threshold;
- radius/metric/feature search;
- graph pruning or expansion;
- alternate component definition;
- representative-family search;
- secondary-fragment insertion search;
- k/scaling/annual-combiner/diversity/fusion/source-quota search;
- candidate-generation or membership change;
- oracle identity rule;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053/#1071 may not enter the score or order.
- Candidate generation and memberships remain unchanged.