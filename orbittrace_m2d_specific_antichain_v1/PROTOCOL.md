# OrbitTrace specific-M2D antichain v1

## Motivation

Two label-free structural tests showed that absolute M2D can still favor broad TopoModal ancestors. This method converts the existing internal mass into an intensive evidence-concentration score without introducing a fitted parameter.

## Frozen method

For every support>=4 node in the unchanged radius=1 TopoModal hierarchy, compute the unchanged annual-density M2D:

`M2D(S) = (1/|S|) * sum_{B subseteq S} |B| A(B)`.

Define one fixed specific score:

`D2D(S) = M2D(S) / |S| = sum_{B subseteq S} |B| A(B) / |S|^2`.

No exponent or coefficient is tuned.

Candidate extraction is a global laminar antichain:

1. sort all reportable hierarchy nodes by D2D descending, then raw M2D descending, then family hash;
2. accept a node iff its event set is disjoint from every already accepted node;
3. reject all later overlapping ancestors/descendants.

The final catalogue is ranked by the same D2D-descending order. No size threshold, target coordinate, activity interval, or fitted hyperparameter is used.

## Development firewall

First test uses exactly the frozen target-excluded GMN 2022/2023 sparse universes (d=128,1024; buckets 0..3), with solar longitude [20 deg,55 deg] removed before candidate generation and truth evaluation. OrbitTrace reveal information and SonotaCo are prohibited from method selection.

## Frozen promotion gates

Before truth: mean, p90, and max candidate member counts must each be strictly lower than baseline M2D; at least one broad ancestor must be rejected; output must be pairwise disjoint.

Then, under exact PR #1377 comparator-capacity evaluation: Sugar-route and HDBSCAN-route mean macro-F1 and F1>0.5 recovery must not fall below baseline M2D; d=128 and d=1024 F1/recovery must each not fall below baseline; the method must still beat frozen published-config Sugar and HDBSCAN. No post-result parameter search.

A structural failure stops before truth. A full GMN pass permits a no-tuning transfer to the exact 29,246-event SonotaCo symmetric benchmark. OrbitTrace is characterized only after method-level promotion and is never used to choose this normalization.