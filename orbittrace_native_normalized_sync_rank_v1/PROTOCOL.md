# OrbitTrace native normalized density-synchronous stability rank v1 — frozen protocol

## Scientific goal
Test one narrowly defined ranking correction on the **exact frozen 179 candidate universe**. HDBSCAN's native `get_clusters` implementation returns a normalized stability/coherence score for every selected cluster, but the OrbitTrace recurrent-EOM wrapper discards that score and orders selected families by the raw density-synchronous stability integral instead.

Raw stability is extensive in both persistence and cluster membership mass, so very large background-rich families can rank highly simply because they contain many meteors. The immediately preceding preregistered `max_cluster_size=1%` experiment confirmed that hard-removing those broad families is too destructive (164 total recovered@100), despite increasing top-100 precision. v1 therefore leaves every frozen winner membership intact and tests the native HDBSCAN normalization rather than deleting or splitting families.

The project goal is unchanged: a GMN PASS requires total recovered@100 >= **184** (+5 over the frozen 179 winner), with no annual regression in recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation. Only a clean GMN pass may earn a separately frozen SonotaCo transfer test.

## Native HDBSCAN basis fixed before outcome
In HDBSCAN 0.8.43, `get_clusters` computes each selected cluster's returned stability score as:

`stability[node] / (cluster_size * max_lambda)`

when `max_lambda` is finite and positive. For a fixed condensed tree, `max_lambda` is the same positive constant for all selected clusters. Therefore the exact ordering induced by HDBSCAN's native returned stability scores is identical to ordering by:

`normalized_sync_score = density_synchronous_stability / member_count`.

This experiment uses that rank-equivalent quantity because the original winner artifact persisted exact density-synchronous stability and exact memberships/member counts but did not persist the tree-wide `max_lambda`. No approximation or fitted quantity is introduced.

A repository search before freezing found no prior OrbitTrace experiment that ranks density-synchronous recurrent-EOM candidates by `synchronous_stability/member_count`, HDBSCAN native returned stability scores, or an equivalent per-member recurrent stability.

## Binding frozen candidate universe
Read only the exact frozen density-synchronous recurrent-EOM winner artifact:
- workflow run `31852836840`;
- artifact `9238142199`;
- prelabel SHA256 `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- result SHA256 `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`;
- exact ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`;
- exact candidate count **2,094**;
- baseline 2022 recovered@100 = 89;
- baseline 2023 recovered@100 = 90;
- baseline total recovered@100 = **179**.

No HDBSCAN hierarchy is recomputed. No membership may change. No candidate may be added, removed, split, merged, filtered, or altered.

## Sole scientific change
For every exact frozen winner candidate `C`, compute:

`native_rank_equivalent(C) = synchronous_stability(C) / member_count(C)`.

Require `member_count >= 10`, finite nonnegative synchronous stability, and finite nonnegative normalized score for every candidate.

Create exactly one new order:
1. descending `native_rank_equivalent`;
2. descending raw `synchronous_stability`;
3. descending `ordinary_stability`;
4. descending `member_count`;
5. ascending immutable `family_id`.

The first key is the sole scientific change. Remaining keys are deterministic tie-breakers inherited from the winner where possible.

## Pretruth freeze
Before known-shower labels are indexed, persist:
- exact winner artifact hashes;
- candidate count;
- proof that every candidate's membership is byte-for-byte unchanged;
- unordered membership-set SHA256 equal to the winner;
- new ordered-membership SHA256;
- per-candidate raw synchronous stability, member count, normalized rank-equivalent score, and immutable family ID;
- mechanism-active flag requiring the new order differ from the frozen winner;
- firewall state.

Known-shower labels cannot influence score construction or ordering.

## Binding structural gates
Require:
1. exactly 2,094 candidates;
2. exact candidate membership multiset identical to the frozen winner;
3. no candidate content changed except addition of the derived normalized score;
4. new order differs from the frozen winner;
5. every normalized score is finite and nonnegative;
6. all source pins and firewall checks pass.

## Binding GMN success gate
PASS requires all of:
1. total recovered@100 >= **184**;
2. 2022 recovered@50 not below the frozen winner and recovered@100 >=89;
3. 2023 recovered@50 not below the frozen winner and recovered@100 >=90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. every structural, source-pin, reproducibility, and firewall gate passes.

Anything else is FAIL.

## Transfer rule
A GMN PASS is only the first goal-level step. Freeze this exact ranking rule before one exposed SonotaCo 2013/2014 transfer benchmark. On another survey, run the same recurrent/density-synchronous candidate construction and order selected families by their native returned normalized recurrent stability, equivalently synchronous stability divided by selected membership count on that survey. No GMN identities or scores transfer.

Broad generalization still requires a genuinely untouched external survey after exposed SonotaCo evidence.

## No rescue
If v1 fails, permanently close this exact native-normalized recurrent stability rank. Do not retry after outcome with:
- `sqrt(member_count)`, log-size, or any alternative size exponent;
- blends of raw and normalized stability;
- rank sums or Pareto fusion;
- size bins or thresholds;
- background weights;
- candidate filtering or splitting;
- geometry/HDBSCAN changes;
- route/year-specific ranking rules;
- target-guided exceptions.

Any later successor must have a distinct independently motivated mechanism.