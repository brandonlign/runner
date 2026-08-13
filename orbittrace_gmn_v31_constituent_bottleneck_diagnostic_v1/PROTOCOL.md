# OrbitTrace GMN v31 constituent bottleneck diagnostic v1 — frozen protocol

## Scientific role

This is a **GMN 2022+2023 target-excluded diagnostic only** for the passed v31 local-geometry parent. It evaluates no successor, creates no alternative rank, and authorizes no SonotaCo access.

The purpose is to answer one predeclared mechanism question before another successor is proposed:

> Among qualified shower labels that the exact v31 fused order still misses at the fixed top-25, top-50, and top-100 budgets, how often is the label already surfaced by at least one of the parent's two frozen constituents (immutable hard order or diversified v31 local order) but suppressed by equal rank-sum fusion, versus absent from both constituent budgets?

This distinguishes a **fusion bottleneck** from a **constituent/scoring bottleneck** using only ranks that already exist inside the frozen v31 parent. It does not test a new fusion rule or a new local score.

The diagnostic definition is frozen before its first result.

## Authoritative offline package

Use only the verified target-excluded v31 package:

- package workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains only the already-frozen family-level development representation/truth summaries and no raw events, event IDs, hidden event-label mapping, SonotaCo, protected target-region, MAARSY, or DMS data.

## Parent reproduction required before diagnosis

Reconstruct exactly from the package:

1. the immutable P19 hard-family order;
2. the v31 strict-whole-shower OOF raw local margin `d_nonpositive - d_positive` in the exact 23D fold-standardized representation;
3. exact inherited diversity (`lambda=0.8`, `scale=1.0`) applied to that raw margin;
4. exact equal 1-based rank-sum fusion of the diversified local order with the hard order;
5. exact monotone evaluator over the 355 eligible labels.

Require the raw parent margin vector SHA-256 exactly:

`f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Require exact hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

Require exact fused v31 control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any package/hash/fold/evaluator/firewall mismatch fails before the diagnostic.

## Exact label-level representation

The package exports each family's frozen truth summary, including `positive` and `best_label`. A family is eligible to represent a recovered label only when its frozen truth has `positive == true` and its `best_label` is in the frozen eligible-label universe.

For each of the three already-existing parent orders `O` in `{hard, local_diversified, fused}`, define a label's first rank

`r_O(label) = min rank_O(family)`

over all eligible positive families whose `best_label` equals that label.

Before interpreting the diagnostic, the first-rank construction must independently reproduce each order's evaluator `recovered_at_25`, `recovered_at_50`, and `recovered_at_100` counts by counting labels with `r_O <= budget`.

No alternate truth assignment, family representative, label substitution, or hidden event mapping is used.

## Sole predeclared diagnostic statistics

For each budget `B in {25,50,100}` and every one of the 95 qualified labels, classify constituent availability by the two **already-frozen** constituent first ranks:

- `BOTH`: `r_hard <= B` and `r_local <= B`;
- `HARD_ONLY`: `r_hard <= B` and `r_local > B`;
- `LOCAL_ONLY`: `r_hard > B` and `r_local <= B`;
- `NEITHER`: `r_hard > B` and `r_local > B`.

Also record whether `r_fused <= B`.

For labels **missed by fused** (`r_fused > B`), report exactly:

1. count and fraction with `LOCAL_ONLY`;
2. count and fraction with `HARD_ONLY`;
3. count and fraction with `BOTH`;
4. count and fraction with `NEITHER`;
5. `CONSTITUENT_AVAILABLE = BOTH + HARD_ONLY + LOCAL_ONLY`;
6. `CONSTITUENT_ABSENT = NEITHER`.

Interpretation is fixed:

- a high `CONSTITUENT_AVAILABLE` fraction means the existing equal fusion suppresses labels that at least one frozen constituent already places inside the same budget;
- a high `CONSTITUENT_ABSENT` fraction means neither existing constituent reaches the label within that budget, so changing fusion alone cannot recover that label **from an already-in-budget constituent placement**.

This is a bottleneck diagnostic only; it is **not** an oracle-achievable performance estimate and must not be described as one.

For context only, also report:

- exact local-only parent metrics from the already-existing diversified local order;
- hard→fused label gains and losses at each budget;
- local→fused label gains and losses at each budget;
- among fused-missed labels, count with `r_local < r_hard`, `r_local == r_hard`, and `r_local > r_hard`;
- median `r_local - r_hard` for fused-missed labels.

No alternate budget, threshold, weighting, subset, feature, metric, fold, label rule, or post-result second statistic is authorized by this protocol.

## Diagnostic outcome categories

This diagnostic has no PASS/FAIL successor gate. It reports one of three descriptive outcomes at top-100, determined only by the exact predeclared fractions:

- `FUSION_DOMINANT` if strictly more than half of fused-missed qualified labels are `CONSTITUENT_AVAILABLE` at B=100;
- `CONSTITUENT_DOMINANT` if strictly more than half are `CONSTITUENT_ABSENT` at B=100;
- `MIXED` if exactly half are constituent-available and half constituent-absent.

This label does not authorize any specific successor. Any future method still requires independent scientific motivation and freezing before its first valid result. In particular, the diagnostic may not be used to tune a hard/local weight, RRF constant, confidence function, budget-specific fusion, threshold, or feature choice.

## Explicit no-search rules

There is:

- no new scientific rank;
- no successor selected;
- no alternate fusion evaluated;
- no hard/local weight or interpolation evaluated;
- no RRF constant;
- no threshold or cutoff search;
- no alternate budgets beyond 25/50/100;
- no feature/metric/scaling/k/reference change;
- no truth/label/representative search;
- no source/year subgroup search;
- no post-result second diagnostic chosen from this outcome.

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
- `new_rank_evaluated = false`;
- `successor_selected = false`.
