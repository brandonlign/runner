# Frozen GhostStream fixed-4° candidate-recovery execution

## Scientific question

Can the separately developed, immutable fixed-4° coverage-normalized Mondrian anchored four-clique detector recognize the canonical GhostStream members as sparse coherent episodes in real local GMN background data?

This is a **targeted candidate-recovery test**. It is not represented as the original GhostStream discovery and is not a complete blind catalogue scan.

## Immutable inputs

- Final detector source SHA-256: `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`
- Baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`
- Mondrian scorer SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`
- Canonical GhostStream artifact ID: `8814798136`
- Canonical artifact ZIP SHA-256: `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`
- Canonical member table: `reconstruction/exact_downstream/primary/april_candidate_members.csv` inside the exact expert bundle.

No canonical membership, event geometry, method constant, threshold, seed namespace, or interpretation rule may be altered after execution.

## Application years and canonical counts

The fixed application years are the five significant GMN years `2022, 2023, 2024, 2025, 2026`, with expected canonical counts `10, 8, 14, 34, 29` respectively.

Only a `(year, k)` pair with at least `k` canonical members is eligible. The complete frozen `k` family is `4, 6, 8, 12`. Every eligible pair receives exactly four replicates, matching the final methodology benchmark.

## Real background construction

For every application year, official GMN monthly trajectory files for April and May are downloaded during the run. Valid events must have finite:

- solar longitude in `[0°, 360°]`;
- geocentric ecliptic longitude in `[0°, 360°]`;
- geocentric ecliptic latitude in `[-90°, 90°]`;
- geocentric speed in `[5, 75] km/s`.

Only GMN events whose IAU code maps to `SPORADIC` are background. All exact canonical GhostStream event IDs are removed from the background before any window is sampled. Background events are retained only for solar longitude `[10°, 70°]`, which supplies the full ±10° support for the fixed Mondrian bins 2–5 (`[20°,60°)`). No geometry-based background pruning or subsampling is allowed.

## Calibration and negative windows

For each year and each Mondrian bin `2, 3, 4, 5`:

- exactly 128 independent calibration negatives are drawn;
- exactly 64 independent test negatives are drawn;
- every episode contains exactly 128 real sporadic events from the fixed ±10° local window;
- the seeds are deterministic SHA-256 seeds from fixed namespaces and the year, bin, and replicate index;
- calibration and test-negative streams are disjoint by namespace.

The fixed empirical p-value remains:

`p = (1 + number of calibration scores >= observed score) / 129`.

False-positive gates are inherited unchanged from final development:

- overall test-negative FPR at `alpha=0.05` must be `<= 0.06`;
- overall test-negative FPR at `alpha=0.01` must be `<= 0.02`.

## Candidate episode construction

Canonical members are represented only by their preserved event geometry and identity. For each eligible `(year, k, replicate)`:

1. The exact frozen positive-window constructor selects one canonical member as the center.
2. It selects `k-1` additional canonical members within the unchanged ±10° activity window.
3. It fills the episode to 128 events with real local GMN sporadics.
4. The 128-event ordering is deterministically shuffled by the frozen baseline.
5. The detector scores the episode without receiving membership labels.
6. Only after score and quartet indices are fixed is membership revealed to count how many selected quartet events are canonical.

The primary score is the exact fixed 4° score. The original 2° score is retained only as a locked comparator and cannot replace the primary result.

## Frozen recovery summaries and gates

For every `k`, report pooled recall across all eligible year-replicate episodes at `alpha=0.05` and `alpha=0.01`, selected-quartet canonical count, raw score, empirical p-value, and rank among the 64 independent test negatives in the same year and Mondrian bin.

The full-recovery gates are inherited unchanged from final development:

- `k=4`: recall `>=0.15` at 0.05 and `>=0.05` at 0.01;
- `k=6`: recall `>=0.30` at 0.05 and `>=0.15` at 0.01;
- `k=8`: recall `>=0.45` at 0.05 and `>=0.25` at 0.01;
- recall must be nondecreasing across `k=4,6,8,12` at both alpha levels;
- both false-positive gates must pass.

Verdicts:

- `FULL_FROZEN_GHOSTSTREAM_RECOVERY`: every inherited calibration, recall, and monotonicity gate passes.
- `PARTIAL_FROZEN_GHOSTSTREAM_RECOVERY`: both FPR gates pass, at least one candidate episode has `p<=0.05`, and its selected quartet contains four canonical members, but the full gate set does not pass.
- `NO_FROZEN_GHOSTSTREAM_RECOVERY`: otherwise.

## Claim boundary

A full or partial result connects the novel detector to GhostStream as an independent, frozen recognition test. It does not prove a blind catalogue rediscovery, establish a new IAU shower, resolve parent/branch status, or convert this detector into the historical discovery method.

Any failure is final for this formulation. No post-result scale, threshold, seed, calibration, year, k, membership, background, or gate change is allowed.