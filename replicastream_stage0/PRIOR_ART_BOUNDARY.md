# ReplicaStream prior-art and novelty boundary

## Established ingredients

None of the following is individually novel:

- stacking meteor observations into a multi-year virtual year;
- checking annual recurrence after detecting a candidate;
- Poisson excess tests;
- multiple-search calibration using simulated null catalogs;
- partial-conjunction hypothesis testing across repeated studies;
- order-statistic combination of annual evidence.

Benjamini and Heller introduced general partial-conjunction testing for claims that effects occur in at least `r` studies. Meteor surveys have also combined many observing years into one virtual year to increase weak-shower sensitivity.

## Narrow hypothesis under test

The possible domain contribution is an end-to-end **meteor-stream discovery statistic** that:

1. preserves each observing year as an independent evidence channel;
2. ranks each candidate by the `r`-th strongest annual excess before candidate selection;
3. scans location and template width adaptively;
4. calibrates the maximum over that complete search at catalog level; and
5. is demonstrably better than both virtual-year pooling and pooled detection followed by an annual-support gate.

This is not mathematically new partial-conjunction theory. It is potentially a new meteor-search formulation only if it creates a meaningful performance frontier: weak recurrent-stream sensitivity without vulnerability to one-year artifacts.

## Claims prohibited at Stage 0

Do not claim that:

- partial conjunction is new;
- annual recurrence is new;
- the method is the first recurrent meteor-stream detector;
- the method outperforms clustering or wavelet searches;
- the method is robust to persistent network artifacts;
- the method has been validated on GhostStream.

## Kill boundary

The method is rejected if it does not materially improve recurrence discrimination over the strongest conventional baseline, loses strong-stream recovery, or fails the shared-structure artifact stress test.

Even a Stage-0 pass would leave novelty provisional until a broader literature audit and comparisons against HDBSCAN, DBSCAN, wavelet searches, held-out-year confirmation, and real known weak showers are completed.
