# OrbitTrace GMN v31 negative-intrusion-depth diagnostic v1 — frozen protocol

## Role

This is a **GMN 2022+2023 target-excluded parent diagnostic only**. It creates no successor score or rank and authorizes no SonotaCo access.

Two already-frozen GMN-only diagnostics establish the current v31 mechanism state:

- at top 100, 21 of 29 qualified labels missed by exact fused v31 are outside the top 100 of both hard and diversified-local constituents;
- all 21 of those constituent-absent labels have no positive representative with raw v31 margin `d_nonpositive-d_positive > 0`.

The remaining question is whether this sign rejection is **shallow**—typically one nonpositive reference intrudes ahead of the nearest positive—or **deep**, with multiple nonpositive references closer than the nearest positive. This matters mechanistically because shallow intrusion is a boundary/local-support problem, whereas deep intrusion indicates stronger overlap of the frozen 23D class representation.

The diagnostic definition is frozen before its first output.

## Authoritative package and exact parent reproduction

Use only the verified v31 offline package from run `31663453082`, artifact `9167087908`, digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`.

Require exactly:

- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- 226x23 feature SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- 226x8 centroid SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- raw v31 OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- hard controls @25/@50/@100 = `21/38/59`, precision `0.6884631112636006`, MRR `0.046734076055452344`, qualified `95`;
- fused v31 controls @25/@50/@100 = `23/41/66`, precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95`.

Recompute the exact parent strict-whole-shower 5-fold OOF geometry using the frozen 23D representation, fold-training mean/population-SD z-score, Euclidean distances, exact positive/nonpositive truth semantics, diversity `lambda=0.8, scale=1.0`, and equal hard/local rank-sum fusion.

Any mismatch fails before diagnosis.

## Exact family-level intrusion count

For each held-out **positive** family `z`, consider all fold-training references in the exact standardized parent geometry.

Let `p*` be the nearest positive training reference under deterministic ordering `(Euclidean distance, immutable hard rank, family ID)`.

Define the family-level negative intrusion count

`I(z) = number of nonpositive training references ordered strictly before p* under the same deterministic ordering over all training references`.

Thus:

- `I(z)=0` iff the deterministic nearest training reference is positive;
- `I(z)=1` means exactly one nonpositive reference intrudes before the nearest positive;
- `I(z)>=2` means multiple nonpositive references intrude before the nearest positive.

This definition uses no threshold, distance ratio, calibration, k choice, or new score. The exact nearest-positive distance, nearest-nonpositive distance, parent raw margin, and all-reference rank of `p*` are recorded for provenance only.

The implementation must independently verify for every positive held-out family that `I(z)=0` exactly when the deterministic parent nearest-class comparison has the positive reference ordered before every nonpositive reference. For strict negative parent margins `m<0`, require `I(z)>=1`. Exact distance ties follow immutable hard-rank/family-ID ordering and are reported separately.

## Exact label-level summaries

For each of the 95 qualified labels, collect all positive family representatives for that label and record:

- representative count;
- `min_I(label)` = minimum intrusion count across its positive representatives;
- median intrusion count;
- maximum intrusion count;
- count of representatives with `I=0`, `I=1`, and `I>=2`;
- first rank in exact hard, diversified-local, and fused parent orders.

`min_I` is descriptive only: it asks how shallow the best available representative is. It does not define a new rank.

## Predeclared subsets and statistics

At top 100 only, exactly reproduce:

1. the 29 qualified labels missed by fused v31;
2. the 21-label `CONSTITUENT_ABSENT` subset with hard first rank >100 and diversified-local first rank >100;
3. within that 21-label subset, the previously frozen condition that every label has no representative with raw v31 margin >0.

For the exact 21 constituent-absent labels, report:

- the complete integer histogram of `min_I(label)` with no bin merging;
- min, 25th percentile, median, 75th percentile, and max of `min_I`;
- count/fraction with `min_I=1` (**SINGLE_INTRUDER**);
- count/fraction with `min_I>=2` (**MULTIPLE_INTRUDERS**).

The split at one versus multiple is fixed because one is the minimal possible intrusion among sign-rejected labels; it is not a fitted cutoff.

Also report the same statistics for all 25 top-100 fused-missed labels previously shown to have `NO_POSITIVE_SUPPORT`, requiring exact reproduction of that count before interpretation.

For context only, report the histogram and five-number summary of `min_I` for all 29 top-100 fused misses and for all 95 qualified labels.

## Predeclared descriptive outcome

Within the exact 21 constituent-absent/sign-rejected labels:

- `SINGLE_INTRUDER_DOMINANT` if strictly more than half have `min_I=1`;
- `MULTIPLE_INTRUDERS_DOMINANT` if strictly more than half have `min_I>=2`;
- `MIXED_INTRUSION_DEPTH` if exactly half fall in each category.

This outcome does **not** authorize any successor. It only distinguishes shallow boundary intrusion from deeper representation overlap.

## No-search / no-rescue rules

There is no:

- new score or rank;
- alternate budget;
- distance threshold or ratio;
- intrusion-count threshold beyond the preregistered natural split `1` versus `>=2`;
- feature, metric, scaling, k, reference, diversity, fusion, or truth change;
- source/year subgroup search;
- successor selection;
- post-result second diagnostic chosen from the outcome.

## Firewall

Every execution must assert:

- `scientific_role = GMN_TARGET_EXCLUDED_PARENT_DIAGNOSTIC_ONLY`;
- `blind_exclusion = [20.0,55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_accessed = false`;
- `raw_event_ids_accessed = false`;
- `raw_hidden_label_mapping_accessed = false`;
- `new_score_created = false`;
- `new_rank_evaluated = false`;
- `successor_selected = false`.
