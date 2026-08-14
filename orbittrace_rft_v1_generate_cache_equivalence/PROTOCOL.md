# RFT v1 cached-generate semantic equivalence audit

Status: frozen before execution. Synthetic engineering identity audit only; no meteor catalogue, shower truth, or RFT scientific endpoint is accessed.

## Purpose

The frozen RFT v1 `generate()` rebuilds atoms/tubes separately for the primary configuration and three preregistered ablations. The engineering cached runner blob `2a599c6e8247eb819a1090591d586526eda6c0c1` factors those invariant atom/tube objects into a cache and calls `generate_cached()`.

This audit tests that, **given identical tube objects for every replica and ownership mode**, `generate_cached()` is exactly equivalent to the frozen `generate()` downstream of tube construction.

## Frozen identities

- frozen RFT science Git blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- cached runner Git blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`.

## Synthetic fixture

Use deterministic synthetic event rows and deterministic `Tube` objects only. No catalogue parser, labels, metrics, candidate truth, or external data are loaded.

Monkeypatch only the frozen `atoms`, `build_tubes`, and `perturb` construction path so frozen `generate()` receives the exact same predeclared tube lists supplied directly to `generate_cached()`. Leave frozen `fit_trim`, `jaccard`, persistence calculation, scoring, family-ID hashing, output sorting, and every scientific constant unchanged.

The fixture must exercise:

- at least one tube that passes persistence;
- at least one tube rejected by the frozen persistence threshold;
- deterministic trajectory trimming/scoring on real synthetic event rows;
- both ownership modes;
- persistence enabled and disabled;
- trajectory trim enabled and disabled.

## Exact modes

Compare byte/canonical-object equality for the four frozen RFT evaluations:

1. `ownership=True, do_trim=True, do_persistence=True` (primary);
2. `ownership=False, do_trim=True, do_persistence=True` (no-path-ownership ablation);
3. `ownership=True, do_trim=True, do_persistence=False` (no-persistence ablation);
4. `ownership=True, do_trim=False, do_persistence=True` (no-trim ablation).

For every mode, the complete ordered list of output dictionaries from frozen `generate()` and cached `generate_cached()` must be exactly equal under ordinary Python object equality and canonical JSON bytes.

## Pass rule

`PASS_RFT_V1_CACHED_GENERATE_SEMANTIC_EQUIVALENCE` requires exact equality in all four modes. Any mismatch fails closed and cached `generate_cached()` cannot be treated as an exact implementation refactor.

This audit does not establish atomization equivalence, parallel-replica equivalence, or a scientific RFT result; those require separate evidence.
