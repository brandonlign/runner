# OrbitTrace v31 quality × component joint-signal diagnostic v1

## Scientific role

Post-result diagnostic only after binding v41 failed 0/4. The purpose is to test whether two **independently frozen and independently positive** diagnostics identify the same recoverable-but-missed HDB groups more selectively than either signal alone:

1. #1086 quality suppression: the immutable pre-SonotaCo #839/#853 quality order ranks the same HDB representative better than exact v31 (`quality_suppression > 0`).
2. #1072 component closure: the representative's frozen cross-route connected component contains some Sugar/HDB member with a strictly better normalized exact-v31 percentile (`component_closure_opportunity = true`).

This diagnostic evaluates no new candidate order, score, replacement, cutoff, or successor. It only tests the predeclared logical intersection of the two already-defined binary directions.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

## Authoritative inputs

Consume only:

- #1086 run `31456339844`, artifact `9088169870`, zip digest `sha256:b0f9499280f9e8cc4d1f6f8a04d4871a306ea085a8eaee03bba0d002c35d5641`, result JSON SHA-256 `b7b1acc48472deb4faa0867a8414260c52b87378d20f380d824272de7b36b9ec`;
- #1072 run `31455141716`, artifact `9087743465`, zip digest `sha256:8c45c00fd70300efb2f6f32bbb339141f8c34884ee5b1098c1bbb45ccf1a59cc`, result JSON SHA-256 `a886977139074a1c2e8beaca54c065fd16fed5bce4c00e888ac2081dabed7222`.

Require both source diagnostics to have their recorded PASS verdicts and diagnostic-only/firewall states.

## Exact joint signal

For each annual recoverable HDB strict-group representative already present in both authoritative diagnostics, require exact agreement on:

- year;
- strict group;
- representative family ID;
- exact v31 representative rank;
- surfaced/missed status.

Define exactly:

- `positive_quality_suppression = (quality_suppression > 0)` from #1086;
- `component_closure_opportunity` exactly as frozen in #1072;
- `joint_signal = positive_quality_suppression AND component_closure_opportunity`.

No suppression magnitude, threshold, component size, calibrated q, rank window, top-k, distance, overlap, or alternate Boolean combination is evaluated.

## Predeclared interpretation gate

For 2013 and 2014 separately, among the fixed 9 surfaced and 9 missed recoverable HDB groups, report joint-signal counts and fractions.

The joint direction is supported only if **both years** satisfy:

1. at least one missed recoverable group has `joint_signal=true`; and
2. the joint-signal fraction among missed groups is strictly greater than the joint-signal fraction among surfaced groups.

No minimum effect size beyond strict inequality is selected.

A PASS means only that this parameter-free intersection deserves a separately frozen candidate-level successor design. It does not select how candidates should be promoted, where they should enter a total order, how many corrections to make, or any budget-specific action.

A FAIL closes this exact AND mechanism. No OR, weighted combination, suppression threshold, component-score threshold, or post-result alternate Boolean rule is authorized within this diagnostic.

## Explicit non-search commitments

No:

- new rank, score, selector, replacement, or panel evaluation;
- oracle identity hard-coding;
- threshold or effect-size search;
- AND/OR/XOR/weighted-combination search;
- suppression magnitude transform;
- component-size or component-score rule;
- rank window or top-k rule;
- route/year/budget-specific rule;
- graph/component redefinition;
- feature/model/k/scaling/diversity/fusion/source-quota search;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
