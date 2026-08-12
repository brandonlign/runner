# OrbitTrace GMN group-balanced Fisher OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor** to the binding `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF` method. It is frozen before outcome and uses no SonotaCo 2013/2014 result, OrbitTrace target information, protected 20°–55° event, MAARSY, or DMS information to choose its mechanism.

The Fisher parent is already strict whole-shower OOF, so fragments from one recurrent shower can never leak across train and test. However, inside a training fold it still treats every candidate family as one statistical observation. The exact authorized GMN fixture contains 226 families but only 201 OOF groups. Its recoverability target contains 111 positive families spread across only 95 positive class-groups and 115 nonpositive families across 114 nonpositive class-groups. Eight shower groups contain both a positive and a nonpositive fragment. Thus prolific fragmented showers can contribute more than one observation to a class mean/covariance even though leakage is prevented.

This successor tests one parameter-free correction: **each OOF group contributes at most one training prototype per recoverability class**. It changes only the training reference measure used to fit Fisher. Every held-out candidate remains an individual family and the 226-family ranking/evaluation universe is unchanged.

## Authoritative parent and fixture

Binding parent: `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`.

Use only the exact `PASS_GMN_DEVELOPMENT_FIXTURE_V1` artifact and fail closed unless it reproduces:
- candidate count: `226`;
- feature dimension: `23`;
- feature SHA256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- immutable hard-order SHA256: `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`;
- k=1 parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- scaled Fisher parent SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`;
- Fisher recovered@100: `69`;
- Fisher recovered@50: `41`;
- Fisher top-100 dominant precision: `0.7677499561973543`;
- Fisher MRR: `0.05055989766869564`;
- qualified families: `95`.

The fixture is an engineering cache of already-authorized target-excluded development information, not a scientific change. Candidate generation and memberships are immutable.

Before candidate interpretation, use the exact fixture Fisher score with the frozen diversity/fusion machinery and require all five Fisher parent metrics above to reproduce exactly.

## Exact OOF setup

Use the fixture's exact:
- 226×23 intrinsic feature matrix;
- recoverability-positive vector;
- whole-shower OOF group strings and deterministic five folds;
- centroid matrix;
- memberships, truths, eligible recurrent-label universe, IDs, and hard order.

The full fixture structure must contain exactly:
- 201 distinct OOF groups;
- 111 positive families and 115 nonpositive families;
- 95 distinct groups containing at least one positive family;
- 114 distinct groups containing at least one nonpositive family;
- 8 groups containing both classes.

These are provenance controls on the already-authorized development fixture, not tunable thresholds.

For each fold:
1. fit arithmetic mean and population standard deviation (`ddof=0`) on **all individual training families** in all 23 dimensions, exactly as in the Fisher parent;
2. replace only exactly-zero SD by `1.0`;
3. transform all training and held-out individual families to that training z-space;
4. retain the exact recoverability class and OOF group associated with every training family.

## Sole scientific change: class-conditional group prototypes

Within each training fold and for each recoverability class separately:

1. enumerate the distinct OOF group strings represented by training families of that class, sorted lexicographically only for deterministic construction;
2. for each `(group, class)` pair, take the arithmetic mean of all training z-vectors in that group that belong to that class;
3. that mean is one **class-conditional group prototype**;
4. a group with multiple positive fragments contributes exactly one positive prototype;
5. a group with multiple nonpositive fragments contributes exactly one nonpositive prototype;
6. a mixed-class group contributes one positive prototype and one nonpositive prototype, each computed only from members of its own class.

No family is deleted from the held-out ranking universe. No majority class, group relabeling, group exclusion, prototype weighting, multiplicity cap search, medoid, robust centroid, or alternate mixed-group treatment is allowed.

Fit the exact balanced shrinkage Fisher architecture to those prototypes:
- `mu_pos` and `mu_neg` are prototype-class means;
- fit `LedoitWolf(assume_centered=False, store_precision=False)` separately to positive and nonpositive prototypes;
- form `Sigma = 0.5*Sigma_pos + 0.5*Sigma_neg`;
- require finite, symmetric, positive-definite pooled covariance;
- `w = solve(Sigma, mu_pos - mu_neg)`;
- equal-prior midpoint `m = 0.5*(mu_pos + mu_neg)`;
- held-out **individual family** score `g(x) = dot(x-m,w)`.

There is no sample-weight search, group-weight search, class-prior search, covariance-estimator search, regularization search, group-size feature, prototype/family blend, dimensionality reduction, feature selection, or nonlinear model.

## Frozen score-unit preservation

The parent diversity routine subtracts a fixed proximity penalty directly from the score. Therefore restore the group-balanced raw score to the typical absolute scale of the exact binding Fisher parent:

- `A_parent = median(abs(fisher_parent_scaled))`;
- `A_group = median(abs(g))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_group`;
- sole successor diversity input `g_scaled = g * unit_factor`.

This is a positive scalar multiplication only and cannot change the pre-diversity group-balanced ordering or sign. No alternate scale statistic or calibration is allowed.

## Frozen ranking and binding gate

Apply exactly the parent:
- centroid geometry;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- exactly one equal rank-sum fusion with immutable P19 hard order.

The first technically valid outcome is binding.

PASS requires the sole fused group-balanced Fisher order simultaneously to:
- recover **strictly more than 69** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7677499561973543`;
- MRR at least `0.05055989766869564`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact group-balanced architecture. No prototype/family interpolation, alternate group weighting, mixed-group treatment, prototype statistic, covariance change, feature change, score calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

A PASS is target-excluded GMN development only. It does not automatically authorize another SonotaCo transfer; cross-dataset use requires a separately frozen governance decision and should be reserved for a materially stronger GMN advance.

## Firewall

- blind exclusion `[20.0,55.0]` remains mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
