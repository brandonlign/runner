# OrbitTrace GMN v31 complete-graph supervised OPF v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 architectural successor to exact v31. It is frozen before its first technically valid outcome.

The frozen GMN parent diagnostics establish that the dominant remaining top-100 failure is deeper class-support overlap rather than fusion or a one-boundary error: 21/29 fused misses are outside both parent constituents; all 21 have no positive-side v31 representative; and 17/21 have at least two nonpositive training references ahead of even their best nearest positive representative.

This successor therefore changes the **class-support topology**, not the 23D representation, metric, folds, diversity, or fusion. It uses the canonical complete-graph supervised Optimum-Path Forest (OPF) construction with Euclidean arc weights and the minimax path-cost function.

Primary method: Papa, Falcão & Suzuki (2009), *Supervised Pattern Classification based on Optimum-Path Forest*, International Journal of Imaging Systems and Technology 19(2), 120–131, DOI `10.1002/ima.20188`. The canonical implementation selects prototypes from cross-class MST edges, propagates minimax path costs from those prototypes, and classifies a test point by the minimum insertion cost `max(training_path_cost, distance_to_test)`.

No validation-set learning, pruning, hyperparameter search, or OPF variant is used.

## Authoritative package and immutable parent science

Use only the verified v31 offline package from workflow `31663453082`, artifact `9167087908`, digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`.

Require exactly:

- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- 226x23 feature SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- 226x8 centroid SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- raw v31 OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Keep fixed:

- exact 226 candidates/memberships and immutable hard order;
- exact 23D feature representation/column order;
- GMN 2022+2023 target-excluded development universe;
- exact five strict whole-shower OOF folds;
- fold-training mean / population-SD z-standardization, zero SD mapped to 1;
- exact positive/nonpositive truth semantics;
- ordinary Euclidean distance;
- exact centroid diversity `lambda=0.8`, `scale=1.0`;
- equal 1-based rank-sum fusion with immutable hard order;
- exact monotone evaluator over 355 eligible labels.

Require exact hard control `21/38/59`, precision `0.6884631112636006`, MRR `0.046734076055452344`, qualified `95`, and exact fused-v31 control `23/41/66`, precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95` before successor interpretation.

## Sole scientific change: canonical complete-graph OPF support

For each outer OOF fold independently, after exact parent standardization:

### 1. Deterministic complete-graph MST and prototypes

Let fold-training rows be nodes in their immutable package input order. Use all pairwise Euclidean distances as complete-graph arc weights.

Construct exactly one deterministic Prim MST, matching the canonical OPF prototype construction:

- root node = fold-training node with smallest immutable package input index;
- root key = 0, every other key = infinity;
- at each step extract the unsettled node minimizing `(key, package input index)`;
- for every unsettled node `q`, replace its key/predecessor only when `distance(p,q) < current_key(q)`; exact equal distances do not replace the existing predecessor.

For every MST edge `(node, predecessor)` whose frozen classes differ, mark **both endpoints** as OPF prototypes. Require at least one positive and one nonpositive prototype.

No alternative MST, prototype pruning, prototype weighting, density prototype, kNN graph, or validation-based prototype selection is allowed.

### 2. Canonical minimax optimum-path forest

Initialize every prototype with path cost `0`, predecessor NIL, and propagated label equal to its frozen class. Initialize every nonprototype path cost to infinity.

Repeatedly settle the unsettled node minimizing `(path_cost, package input index)`. For settled node `p` and every unsettled node `q`, if `path_cost(p) < path_cost(q)`, compute

`candidate = max(path_cost(p), distance(p,q))`.

Update `q` only when `candidate < path_cost(q)`; exact equal candidates do not replace the existing predecessor/label. When updated, `q` inherits `p`'s propagated OPF label.

Record training settlement order, costs, propagated labels, predecessors, prototype IDs, and MST provenance. There is no evaluation-set `learn()` step and no pruning.

### 3. Canonical test insertion costs and signed ranking margin

For held-out standardized query `z`, for every trained node `s` define the standard OPF insertion cost

`J_s(z) = max(C_s, ||s-z||_2)`

where `C_s` is the trained minimax path cost.

The canonical OPF predicted class is the propagated label of the node minimizing `(J_s(z), settlement_order_position)`.

For ranking, expose the two class-specific minima already implicit in that same canonical test competition:

`J_pos(z) = min_{s: propagated_label(s)=positive} J_s(z)`

`J_neg(z) = min_{s: propagated_label(s)=nonpositive} J_s(z)`.

The sole raw successor score is

`m_OPF(z) = J_neg(z) - J_pos(z)`.

Higher is better. When the two class minima differ, the sign must exactly agree with the canonical OPF predicted class. Exact class-cost ties are allowed, produce score zero, and use canonical settlement-order tie-breaking only for the discrete predicted-class provenance field.

This class-cost difference is not a new classifier or tuned confidence function; it is the signed difference between the two competing costs in the fixed canonical OPF test rule.

In the same execution, recompute exact v31 nearest-reference OOF margin and require its full frozen SHA before interpreting OPF.

## Frozen score-unit preservation and post-score machinery

Because inherited diversity is additive in score units, fix before outcome:

- `S_parent = median(abs(m_parent))`;
- `S_OPF = median(abs(m_OPF))`;
- require both finite and strictly positive;
- `unit_factor = S_parent / S_OPF`;
- sole score entering inherited diversity = `m_OPF * unit_factor`.

If `S_OPF` is zero/nonfinite, this exact method is a technical no-go. No fallback scale is permitted.

Then exactly:

1. apply inherited diversity `lambda=0.8`, `scale=1.0`;
2. equal-rank-fuse that diversified OPF order with immutable hard order;
3. evaluate once with the exact parent evaluator.

Local-only OPF metrics and forest diagnostics are descriptive only.

## Fixed diagnostics

Record only:

- prototype count and class counts by fold;
- MST total weight/hash;
- training path-cost min/median/max and propagated-label counts;
- training propagated-label disagreement count versus frozen truth (diagnostic only; canonical OPF remains valid regardless);
- per held-out query `J_pos`, `J_neg`, raw OPF margin, canonical predicted label, and winning node IDs;
- count of exact class-cost ties;
- raw/scaled score hashes and unit factor.

No diagnostic changes the candidate or promotion gate.

## Explicit no-search / no-rescue rules

There is no:

- OPF validation-set learning or sample swapping;
- OPF pruning;
- kNN/sparse-graph OPF;
- alternative path-cost function;
- alternative prototype policy or MST tie rule;
- prototype weighting/deletion/addition;
- class prior/cost weighting;
- distance-metric or feature/scaling search;
- OPF score calibration, clipping, exponent, threshold, temperature, or blend;
- parent/OPF blend;
- graph-density augmentation;
- diversity/fusion search;
- source/year/budget-specific rule;
- post-result OPF variant.

If this first valid result fails, no sparse OPF, kNN-OPF, alternative prototype/MST/path-cost, validation-learned OPF, pruned OPF, class-weighted OPF, or result-informed OPF rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires all:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact package/evaluator/parent-margin/fold/firewall checks pass.

Failure of any gate permanently rejects this exact complete-graph OPF successor.

## SonotaCo and firewall

Only a GMN PASS may authorize a separately frozen one-shot exposed SonotaCo 2013/2014 comparison using the already-established exact 23D GMN→SonotaCo mapping. SonotaCo remains EXPOSED DEVELOPMENT ONLY.

Every execution must assert protected solar longitude `[20,55]` remains excluded; no OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, DMS, raw GMN event rows, raw event IDs, or raw hidden event-label mapping are accessed.
