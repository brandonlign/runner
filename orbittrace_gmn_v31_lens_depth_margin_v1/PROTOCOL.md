# OrbitTrace GMN v31 lens-depth margin v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests exactly one structural mechanism:

> Replace the parent's two single-prototype nearest-class distances with a parameter-free **maximum lens-depth class contrast** that measures how centrally each held-out family lies inside the full pairwise geometry of the positive and nonpositive training classes.

The sole local score is

`lens_margin(x) = normalized_lens_depth(x; positive references) - normalized_lens_depth(x; nonpositive references)`.

The exact parent OOF groups, fold standardization, 23D representation, centroid diversity, immutable hard order, equal rank-sum fusion, truth semantics, and evaluator remain unchanged.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent motivation fixed before outcome

The completed v31 lineage now supports a narrow structural conclusion:

- exact local two-class Euclidean geometry is useful and transfers better than global supervised Fisher geometry;
- positive-only support fails badly, so both classes matter;
- changing the same nearest positive/nonpositive distance pair by relative normalization, Mutual Proximity, or class-conditional calibration fails;
- deleting ambiguous negative references by frozen single-pass Tomek editing improves GMN recovered@100 from 66 to 67 and top-100 precision from 0.7229521515453452 to 0.7332227143 but narrowly fails MRR, showing that local two-class boundary structure matters while the exact editing lane remains closed;
- replacing point prototypes by nearest closed segments improves very-early placement but loses @100 and precision, so a hand-built local manifold interpolation is not supported;
- global Fisher improves GMN to 69 @100 but collapses in frozen SonotaCo transfer, so optimizing one survey-specific global discriminant geometry is not an acceptable direction;
- unregularized full-dimensional LFDA is technically infeasible because the within scatter is singular, and regularization/reduced-rank rescue is not allowed.

Lens depth provides a genuinely different way to use **both classes and local geometry** without deleting references, learning a metric, choosing k, fitting a threshold, or rescaling the already-failed `d_positive/d_nonpositive` pair.

Kleindessner & von Luxburg (JMLR 2017, *Lens Depth Function and k-Relative Neighborhood Graph: Versatile Tools for Ordinal Data Analysis*) define the lens spanned by two references `a,b` in a metric space as

`Lens(a,b) = {x : max(d(x,a), d(x,b)) < d(a,b)}`,

and define lens depth by counting the reference pairs whose lens contains the query. They note that the count, up to its combinatorial normalizing constant, is the probability that the query is the most central member of a triple containing the query and two uniformly sampled references. Their complete-information Algorithm 3 estimates classwise lens depth by a **relative frequency**, hence a [0,1] normalized classwise depth coordinate. The same paper explicitly identifies the simplest classification rule as assigning a query to whichever class gives it the higher lens depth.

This is also the standard maximum-depth classification principle: for equal-prior classes, compute a depth relative to each class and choose the class of maximum depth. Therefore, in a binary problem the signed statistic `depth_positive - depth_nonpositive` is the canonical maximum-depth decision contrast; no downstream classifier or learned coefficient is introduced here.

References fixed before outcome:

- Kleindessner, M. & von Luxburg, U. (2017), *Lens Depth Function and k-Relative Neighborhood Graph: Versatile Tools for Ordinal Data Analysis*, JMLR 18.
- Ghosh, A.K. & Chaudhuri, P. (2005), *On Maximum Depth and Related Classifiers*, Scandinavian Journal of Statistics 32:327–350.

## Authoritative deterministic GMN package

Use only the verified target-excluded GMN v31 offline package:

- workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, or raw hidden-label event mapping.

Before successor science, the offline evaluator must reproduce the exact immutable hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

It must also require the package's exact v31 fused control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any mismatch fails before successor evaluation.

## Immutable v31 parent science

Everything below remains fixed:

- exact 226 P19 hard-family candidates;
- exact 23D intrinsic representation;
- exact strict whole-shower groups and deterministic five folds;
- fold-training arithmetic mean / population-standard-deviation z-score, with zero standard deviation mapped to 1.0;
- exact frozen positive/nonpositive family truth semantics;
- ordinary Euclidean metric in standardized 23D space;
- exact 226x8 centroid matrix used only by the inherited diversity step;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone recovery/precision/MRR evaluator over 355 eligible labels.

No candidate, membership, truth, feature, fold, scaling, diversity, fusion, or evaluation rule changes.

## Sole successor change: normalized classwise lens depth

For each outer OOF fold independently:

1. Fit the exact parent z-score on all outer-training rows and transform outer-training and held-out rows.
2. Split standardized training references into the exact positive class `P` and nonpositive class `N`.
3. Require at least two references in each class.
4. For a held-out query `x` and a class `C` with `m_C` references, consider every unordered distinct reference pair `(a,b)` in `C`.
5. With ordinary Euclidean distance, define strict lens membership exactly as in the JMLR paper:

   `I_C(x;a,b) = 1` iff `max(||x-a||, ||x-b||) < ||a-b||`, otherwise 0.

6. Define normalized empirical lens depth

   `LD_C(x) = sum_{a<b in C} I_C(x;a,b) / choose(m_C,2)`.

This is the complete-information relative frequency/probability form of lens depth. It removes the trivial class-size dependence of raw pair counts without introducing a fitted parameter.

7. Define the sole local successor score

   `lens_margin(x) = LD_P(x) - LD_N(x)`.

Higher is better. Exact equality in a lens inequality is **not** counted as membership because the source definition uses strict `<`.

After all 226 strict-OOF lens margins are computed:

- apply the exact inherited v31 diversity step (`lambda=0.8`, `scale=1.0`);
- fuse the resulting local order with the immutable P19 hard order using the exact parent equal rank-sum;
- evaluate with the exact parent monotone evaluator.

## Explicit no-search rules

There is:

- no k parameter;
- no lens radius or bandwidth;
- no weighted lens depth;
- no local/trimmed lens subset;
- no `<=` boundary convention, epsilon, tie tolerance, or stochastic tie handling;
- no pair subsampling; every unordered same-class pair is used;
- no SVM, logistic regression, DD-classifier, polynomial boundary, or other classifier on the two depth coordinates;
- no class-prior weight or unequal-prior correction;
- no depth transform, logit, ratio, odds, rank transform, or calibration;
- no blend with v31 nearest-point margin;
- no k-RNG classifier;
- no reference deletion, relabeling, filtering, or weighting;
- no feature/metric/scaling/fold/diversity/fusion search;
- no source/year/budget-specific rule;
- no post-result second search.

If the first valid result fails, no weighted lens, local lens, DD-plot classifier, downstream linear/nonlinear classifier, boundary convention, subsampling, pair weighting, depth transform, v31 blend, or result-informed rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31 GMN parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. all package/evaluator/fold/firewall assertions pass.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and literature. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. No later SonotaCo outcome may modify this successor.

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
