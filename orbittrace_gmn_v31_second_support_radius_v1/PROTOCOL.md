# OrbitTrace GMN v31 second-support-radius v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 architectural successor to the binding `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF` parent.

The exact v31 parent assigns each held-out family a signed local margin from the **single closest** positive and **single closest** nonpositive training references. That makes the score maximally local, but it also lets one idiosyncratically close reference determine each class distance. The present successor asks one fixed question:

> Does requiring the local geometry to be supported by at least **two** training references of each class preserve v31's useful locality while reducing dependence on a single atypical prototype?

The sole scientific change is therefore to replace each class's nearest-reference radius by its **second-nearest-reference radius**. No k search, weighting, averaging, metric learning, calibration, feature change, graph propagation, or global classifier is introduced.

This protocol is frozen before the first technically valid GMN outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent methodological motivation fixed before outcome

Nearest-neighbour methods are nonparametric local classifiers, and classical theory treats neighbour order/k as a structural part of the decision rule rather than a mere distance rescaling. Hall, Park & Samworth (2008), *Choice of neighbor order in nearest-neighbor classification* (`arXiv:0810.5276`), studies how neighbour order affects nearest-neighbour classification risk; Samworth (2012), *Optimal weighted nearest neighbour classifiers*, Annals of Statistics 40(5), 2733–2763 (`arXiv:1101.5783`), analyses the bias–variance consequences of using multiple local neighbours.

The OrbitTrace-specific motivation is narrower than generic kNN tuning. The successful v31 parent already establishes that local 23D geometry is useful, while the separately frozen balanced-Fisher transfer showed that stronger global supervised separation can improve GMN yet transfer poorly to SonotaCo. This successor therefore keeps the same local standardized geometry and asks for only the **minimum possible redundancy beyond one reference**.

`k=2` is fixed because it is the smallest support order that can reject dependence on a unique nearest prototype. It is not selected from a performance curve. `k=3`, `k=4`, adaptive k, weighted kNN, mean/median neighbour distances, voting, and any k search are not evaluated or authorized.

## Governance / duplicate audit fixed before outcome

This successor is not a rescue of the closed small-transform lanes:

- relative-margin, class-conditional calibration, Mutual Proximity, and margin-confidence transform or calibrate pairwise evidence; this method changes the underlying class-support order;
- Manhattan and shrinkage-Mahalanobis alter the metric while retaining one-reference support; this method retains exact Euclidean geometry and changes support multiplicity;
- Tomek editing changes the training reference set; this method deletes, relabels, prunes, or reweights no reference;
- physical-block consensus changes feature-view aggregation; this method retains the full 23D parent representation;
- nearest-feature-segment changes point prototypes into interpolated geometry; this method keeps exact observed point references;
- positive-support removes the negative-class contrast; this method keeps both classes;
- the exact 1-NPC robustness lane changes the score to full Voronoi decision-boundary perturbation and ended as a technical no-go; this method remains a direct local class-support contrast;
- the exposed v31 radius-1 graph diagnostic found no useful direct-neighbour rank uplift for missed HDB groups, so no graph propagation is used here.

The block-consensus governance consequence requiring an architectural scoring change is respected: this successor changes the class-support operator from a one-reference minimum to a two-reference support radius, rather than applying another scalar transform to the existing v31 margin.

## Authoritative deterministic GMN package

Use only the verified target-excluded GMN v31 offline package:

- package workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw Euclidean OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, raw hidden-label event mapping, SonotaCo data, target-region data, MAARSY, or DMS.

Before successor interpretation the exact evaluator must reproduce the immutable hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

It must also reproduce the exact v31 fused control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any package, hash, shape, fold, evaluator, truth, or firewall mismatch fails before successor evaluation.

## Immutable parent science

Everything below remains fixed:

- exact 226 P19 hard-family candidates and memberships;
- immutable hard order;
- exact 23D intrinsic family representation and column order;
- target-excluded GMN 2022+2023 development universe;
- deterministic five strict whole-shower folds;
- fold-training arithmetic mean / population-standard-deviation z-score, zero standard deviation mapped to 1.0;
- exact positive/nonpositive recoverability reference semantics;
- ordinary Euclidean distance;
- exact 226x8 centroid matrix used only by inherited diversity;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with immutable hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, truth, fold, feature, scaling, metric, diversity, fusion, or evaluator change is allowed.

## Sole scientific change: second-nearest class support radius

For each exact outer OOF fold independently, fit the parent z-score on fold-training rows only and apply it to training and held-out rows.

Let `P` be all positive training references and `N` all nonpositive training references. For a held-out standardized query `z`, compute ordinary Euclidean distances to every reference.

Write the sorted positive distances as

`d_pos_(1)(z) <= d_pos_(2)(z) <= ...`

and sorted nonpositive distances as

`d_neg_(1)(z) <= d_neg_(2)(z) <= ...`.

The exact parent margin is recomputed for provenance:

`m_parent(z) = d_neg_(1)(z) - d_pos_(1)(z)`.

The sole successor raw score is

`m_support2(z) = d_neg_(2)(z) - d_pos_(2)(z)`.

Higher is better, preserving the parent sign convention: a query receives a stronger score when the radius required to reach two positive references is smaller than the radius required to reach two nonpositive references.

Distance ties are ordered only by immutable hard-family rank and then family ID before selecting the first and second reference. No label-favouring tolerance or jitter is used.

Every fold must contain at least two positive and two nonpositive training references. Otherwise the method is technically invalid before a scientific result.

The complete recomputed 226-vector `m_parent` must hash exactly to the frozen parent margin SHA before `m_support2` is interpreted.

## Frozen metric-unit preservation

The inherited diversity routine subtracts a fixed proximity penalty directly from the local score. The second-support radius can have a different numerical scale from the parent nearest-reference margin even though the physical metric is unchanged. To isolate the support-order mechanism while preserving the already-frozen diversity strength, use the same preregistered positive-scalar unit-preservation principle used in prior v31 metric successors:

- `S_parent = median(abs(m_parent))`;
- `S_support2 = median(abs(m_support2))`;
- require both finite and strictly positive;
- `unit_factor = S_parent / S_support2`;
- sole successor score entering diversity: `m_support2_scaled = m_support2 * unit_factor`.

This scalar cannot change the raw support2 sign or pre-diversity ordering. No alternate scale statistic, centering, clipping, nonlinear transform, or calibration is allowed.

## Frozen post-score machinery

After all 226 strict-OOF `m_support2_scaled` values are computed:

1. apply exact inherited diversity with `lambda=0.8`, `scale=1.0` and exact centroid matrix;
2. produce exactly one candidate by equal 1-based rank-sum fusion of the diversified support2 order with the immutable P19 hard order;
3. evaluate with the exact parent monotone evaluator.

The support2 local-only order is recorded as a diagnostic but cannot rescue failure of the fused promotion candidate.

## Explicit no-search / no-rescue rules

There is:

- support order `k=2` only;
- no k search;
- no first/second-neighbour blend;
- no mean, median, maximum, trimmed mean, weighted average, vote, or kernel over neighbours;
- no adaptive k or density-dependent k;
- no class-specific k;
- no distance weighting;
- no reference editing, deletion, relabeling, pruning, weighting, or prototype construction;
- no metric change or metric learning;
- no feature subset/block search;
- no robust scaling;
- no relative-margin or class-conditional calibration;
- no graph propagation;
- no threshold, clipping, exponent, temperature, or confidence transform;
- no diversity or fusion search;
- no source/year/budget-specific rule;
- no post-result second search.

If the first technically valid result fails, `k=3`, `k=4`, adaptive k, averaged-neighbour distance, weighted kNN, first/second blends, or any result-informed support-order rescue is forbidden from this result.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact package/evaluator/parent-margin/fold/firewall assertions pass.

Failure of any gate permanently rejects this exact second-support-radius successor.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. The already-established exact 23D GMN→SonotaCo correspondence from the v62/v63 lineage must be reused unchanged. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. No SonotaCo outcome may modify this method.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_accessed = false`;
- `raw_event_ids_accessed = false`;
- `raw_hidden_label_mapping_accessed = false`.
