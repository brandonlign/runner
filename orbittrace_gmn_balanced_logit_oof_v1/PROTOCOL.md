# OrbitTrace GMN balanced logit OOF v1 — frozen protocol

## Scientific role

This is a new **target-excluded GMN development successor** to the binding balanced-shrinkage Fisher OOF parent. It is not a rescue variant of rank-Gaussian Fisher, group-balanced Fisher, QDA, diagonal Fisher, equal-block Fisher, distributed local evidence, Mahalanobis, predictive-consistency transfer, or any other closed lane.

The mechanism change is architectural: replace generative class-mean/covariance discrimination with direct conditional maximum-likelihood estimation of a linear log-odds boundary. The representation, strict whole-shower folds, candidate universe, fixed diversity stage, immutable hard-order fusion, and evaluation remain unchanged.

The rationale is fixed before outcome:

1. The Fisher parent established that the sealed 23D physical/cohesion/neighbor representation contains useful joint discriminative information.
2. Rank-Gaussian transformation degraded that signal, so this successor preserves the original feature magnitudes rather than modifying the representation.
3. Separate-class QDA, diagonal covariance, block decomposition, and group balancing are closed, so no covariance or weighting variant is justified.
4. A direct discriminative likelihood objective makes no Gaussian class-density assumption and is therefore a genuinely different estimator while retaining a simple linear decision surface and strict OOF governance.

No SonotaCo result or target information is used to define this method.

## Immutable inputs

Use only the already-sealed exact target-excluded GMN development fixture and exact frozen ranker/runtime inputs used by the verified Fisher fixture.

Required identities:

- fixture run: `31566749364`
- fixture artifact: `9129787782`
- fixture artifact digest: `sha256:14caf01be46de095ff2771cfded8034bad9fa8b6d9567285aa8e657681776a21`
- ranker run: `31344632499`
- ranker artifact: `9046896881`
- ranker artifact digest: `sha256:0143b6291b031b4de2305fc8e85ca3e1a7db1c20e72d85323fb82e9895832649`
- ranker source SHA256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- feature matrix SHA256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- hard order SHA256: `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`
- parent k=1 margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- Fisher scaled-score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`

The candidate universe is exactly 226 hard families and the feature matrix is exactly the sealed 23D matrix: 10 intrinsic structural + 7 cohesion + 6 centroid-neighbor features. No feature is added, removed, transformed, clipped, ranked, selected, interacted, or reweighted.

## Firewall

Before any candidate outcome is accepted, execution must assert:

- blind exclusion exactly `[20.0, 55.0]`;
- SonotaCo 2013/2014 access is false;
- OrbitTrace target-information access is false;
- protected target-region event access is false;
- MAARSY scientific access is false;
- DMS scientific access is false.

No raw catalogue regeneration is required or authorized for this successor; use the sealed fixture.

## Development target and folds

Use the exact cached recoverability reference target and strict group identities from the fixture.

- Positive means the already-frozen qualified-family recoverability predicate.
- Groups remain `SHOWER/<best_label>` for labelled shower families and `NEG/<family_id>` otherwise.
- Fold assignment remains the exact deterministic five-fold mapping already used by the parent.
- Every fold must be strict whole-group OOF: no group may occur in both train and test.
- Training and test data must remain finite and every training fold must contain both classes.

## Fixed estimator

For each of the five folds independently:

1. Compute ordinary per-feature population mean and population standard deviation on the **training fold only**.
2. Replace only an exactly zero training standard deviation with `1.0`.
3. Z-score training and held-out samples using those training-only statistics.
4. Fit exactly `sklearn.linear_model.LogisticRegression` with:
   - `penalty=None`
   - `solver="lbfgs"`
   - `fit_intercept=True`
   - `class_weight="balanced"`
   - `tol=1e-12`
   - `max_iter=10000`
5. Require convergence before `max_iter`; a numerical non-convergence is an engineering no-result, not authorization to alter the estimator.
6. The held-out scientific score is exactly `decision_function(z_test)`, with larger score meaning more recoverable-like.

`class_weight="balanced"` is fixed solely to preserve the Fisher parent's equal-class scientific treatment: each binary class receives equal total training mass. It does **not** equalize shower groups and does not reuse the closed group-balanced Fisher mechanism.

There is no regularization coefficient, C search, penalty search, solver search, intercept choice, class-weight search, calibration, probability threshold, feature search, interaction expansion, nonlinear basis, model ensemble, or hyperparameter selection.

## Fixed score units and ranking

The complete 226-family OOF logit vector is frozen before metrics are interpreted.

To preserve the already-fixed physical diversity stage without allowing arbitrary model-score scale to change its strength:

- let `parent_scale = median(abs(parent_k1_margin))`;
- let `logit_scale = median(abs(logit_raw))`;
- require both to be finite and strictly positive;
- define `unit_factor = parent_scale / logit_scale`;
- define `logit_scaled = logit_raw * unit_factor`.

This is the same parameter-free median-absolute unit matching already used to deploy Fisher-like successor scores against the fixed diversity stage. No alternative score calibration is allowed.

Then apply, unchanged:

1. exact inherited `diversity_order` with lambda `0.8`, scale `1.0`, and immutable hard-order tie key;
2. one exact equal 1-based rank-sum fusion with the immutable hard order;
3. the exact monotone GMN evaluator and qualified-family universe.

No diversity change, fusion change, score blend, parent/logit blend, rank window, threshold, candidate deletion, family exception, or alternate tie rule is authorized.

## Parent control

The same binding run must reproduce the exact Fisher parent before candidate interpretation:

- recovered@100: `69`
- recovered@50: `41`
- recovered@25: `24`
- top-100 dominant precision: `0.7677499561973543`
- MRR: `0.05055989766869564` (floating reproduction may equal `0.05055989766869565` at machine precision)
- qualified matches: `95`
- Fisher scaled-score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`

If these controls do not reproduce, there is no scientific outcome.

## Binding PASS gate

The **first technically valid** candidate outcome is binding.

PASS requires all of:

- recovered@100 **strictly greater than 69**;
- recovered@50 **at least 41**;
- top-100 dominant precision **at least 0.7677499561973543**;
- MRR **at least 0.05055989766869564**;
- qualified matches **exactly 95**.

Otherwise the verdict is `FAIL_GMN_BALANCED_LOGIT_OOF_V1` and this exact architecture is permanently closed.

A PASS verdict is `PASS_GMN_BALANCED_LOGIT_OOF_V1` and authorizes only preservation and separately governed downstream testing; it does not authorize SonotaCo tuning.

## No-rescue rule

After the first valid result, do not retry this lane with any alternative:

- regularization/C/penalty/solver/tolerance as a scientific parameter;
- class weighting or group weighting;
- feature subset, interaction, polynomial, spline, rank, quantile, Gaussian, clipping, robust scaling, or nonlinear representation;
- probability calibration or threshold;
- Fisher/logit/local/predictive/quality score fusion or ensemble;
- diversity coefficient/scale or fusion algebra;
- rank window, budget rule, family deletion, identity exception, or post-result diagnostic chosen to rescue the outcome.

Any future successor after a failure must change mechanism class and be separately motivated and frozen before its first valid outcome.
