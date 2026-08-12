# DP-TBD v1 exact-pair engineering equivalence

This document freezes an engineering-only acceleration of the already-frozen `orbittrace_gmn_dp_track_before_detect_v1` method. It does not alter any scientific constant, event field, blind exclusion, emission definition, dynamic-programming transition, candidate construction, ranking rule, truth interpretation, comparator, or promotion gate.

Frozen scientific source Git blob: `fd25455d90720e81bc3ee4cb74bed9975533f808`.
Engineering wrapper Git blob: `e76656ffa4137ce805911ca3716e2b1763eb1b5e`.
Equivalence test Git blob: `ac162c290cbe983cc1b82d88a30670a991e7c90d`.

## Sole execution change

The frozen `exact_radius_counts` routine is invoked only as a self-neighborhood count with identical query/reference physical states and `subtract_self=True`.

The frozen implementation asks the KD-tree for every endpoint's radius-neighbor list, exact-filters every directed candidate with the frozen angular+log-speed physical metric, and then subtracts the self count. Therefore every non-self qualifying unordered pair contributes exactly one count to each endpoint, but its physical distance is evaluated twice.

The engineering implementation instead calls the same KD-tree at the same prefilter radius to enumerate every non-self unordered pair once, applies the exact same frozen `exact_d2 <= 1 + 1e-12` condition, and increments both endpoints once. This is algebraically identical to the frozen directed-list count.

The wrapper fails closed if it is ever called outside the frozen self-neighborhood shape/identity conditions.

## Pre-full-data equivalence evidence

Workflow `OrbitTrace DP-TBD v1 exact-pair equivalence`, run `31652746088`, completed successfully before any accelerated full-data result.

It verified all source pins and compared the original and engineering counts on deterministic broad random clouds, a dense shower-like cloud, duplicate states, exact physical-radius boundary cases, and just-inside/just-outside cases. Across 617,392 directed qualifying neighbor counts, the arrays were bit-identical.

Binding equivalence statement: an accelerated full-data run is an execution replica of the already-frozen DP-TBD v1 method, not a scientific successor. If it is the first technically valid DP-TBD v1 output, that output is governed by the original frozen DP-TBD v1 protocol and gates. No outcome may motivate engineering or scientific changes to v1.

Protected solar longitude 20-55 degrees, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS remain inaccessible beyond the original target-excluded GMN development protocol.