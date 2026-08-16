# OrbitTrace Persistable persistence-ladder full-scale feasibility v1

## Activation condition

This protocol is frozen before the target-excluded GMN cross-scale ladder outcome. It may execute only if the exact pre-frozen cross-scale diagnostic on `agent/orbittrace-persistable-ladder-crossscale-v1` returns `SUPPORTS_PERSISTABLE_LADDER_CROSS_SCALE_COHERENCE`.

## Purpose

This is an engineering/structural feasibility stage, **not a shower-recovery experiment**. It asks whether the exact ladder architecture that passed synthetic and cross-scale structural gates can be computed on the complete target-excluded GMN 2022+2023 catalogue without changing its sample-size-adaptive upstream neighbor policy.

No shower truth may be read or evaluated. No SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, OrbitTrace target information, or protected-region event may be accessed.

## Frozen full-scale input

- exact target-excluded GMN 2022+2023 parser used by recurrent-EOM;
- exact retained pooled event count must be **738,682**;
- exact GEO6 representation unchanged;
- protected `[20°,55°]` exclusion verified before hierarchy construction.

## Frozen ladder architecture

Pinned upstream: `LuisScoccola/persistable@7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

Use exactly:

- `Persistable(X, n_neighbors="auto", n_jobs=1)`;
- package uniform measure and Euclidean metric;
- package `_find_end()` and `compute_defaults()` midpoint slice;
- one midpoint `lambda_linkage` hierarchy;
- every conservative persistence flattening for `g=2..min(15,B)`, where B is the number of strictly positive-persistence bars;
- exact-membership union of non-noise memberships with >=4 events;
- no preferred g, no ranking, no alternative neighbor count, no subsample, no batching approximation, no year split, and no fallback.

The pinned package's `auto` rule is expected to choose 500 neighbors at n=738,682. That behavior is part of this feasibility test and may not be reduced to fit memory after seeing execution behavior.

## Frozen feasibility gates

PASS only if all are true in one first technically valid execution:

1. all 738,682 target-excluded rows are represented exactly once;
2. Persistable auto-neighbor count equals **500**;
3. hierarchy and all ladder flattenings complete without process OOM, timeout, exception, insufficient-neighbor warning, NaN/Inf, or manual intervention;
4. at least one >=4-member ladder candidate is produced;
5. exact-membership-union candidate count is <=119;
6. no target/shower truth is read.

The workflow timeout is frozen at **180 minutes** on the standard GitHub `ubuntu-22.04` hosted runner. A process OOM or timeout after exact input/provenance guards and before a hierarchy result is an **architecture-feasibility FAIL**, not permission to change `n_neighbors`, subsample, shard, or runner class under this version.

A PASS authorizes only a separately frozen target-excluded GMN recovery/ranking experiment. A FAIL closes this exact full-scale auto-neighbor implementation. Any future scalable approximation would have to be a separately motivated/frozen architecture, not an implementation rescue claimed equivalent to this result.