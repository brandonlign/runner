# M2D fixed4-seeded drift halo v1 — dormant SonotaCo transfer

## Activation

This protocol is frozen before the GMN development outcome exists. It is dormant unless PR #1401 returns the exact verdict:

`PASS_M2D_FIXED4_DRIFT_HALO_V1_GMN_DEVELOPMENT`

A GMN scientific FAIL permanently disables this transfer. No GMN result may change any rule or gate below.

## Immutable scientific method

Transfer the exact scientific semantics frozen on the GMN branch:

- protocol Git blob `c11e82664d49f4d18ef974491b1696c3c8fd3454`;
- halo-builder Git blob `3d2d47c72f703a95713c4f17979f38a8aa3ac75c`;
- paired evaluator Git blob `c80c71b9ec72e9fbb778cb2393a9c9a085779f61`;
- binding runner Git blob `751f3200594c7d981bcf3000d169185c8d3e6c46`;
- exact fixed4 seed-builder Git blob `140f21736ea6615fe111e02d91eaa99b19422da7`.

The transfer keeps the parent M2D catalogue unchanged and applies, per parent candidate/year:

1. exact two-anchor fixed4 consensus seed;
2. Sun-centered affine drift with the same fixed scales: solar longitude /5 deg, radiant longitude/latitude /4 deg, log-speed /log(1.1);
3. unweighted `numpy.linalg.lstsq(..., rcond=None)` with the same rank-deficient zero-slope fallback;
4. `sklearn.covariance.OAS` on the 3D seed drift residuals;
5. exact `chi2.ppf(0.95, df=3)` Mahalanobis region;
6. explicit retention of every fixed4 seed member;
7. halo restricted to the immutable parent envelope.

No confidence-level change, covariance substitution, clipping, background-density term, orbital feature, mixture/component split, recursion, event-size cap, parent rerank, or fallback is permitted.

## Frozen SonotaCo parent

Use the already-frozen **baseline internal-mass M2D SonotaCo catalogue** from PR #1372, not the later support-pruned failure:

- ranked pretruth Git blob `e558023e9bb00f75e34a83b84e578012176ce721`;
- ranked pretruth SHA-256 `9be0e77d650cabd94eccf0623f005705bb86e84793c76190b0065621631f2ecd`;
- candidate count `888`;
- exact common universe `29,246` events from years 2013 and 2014.

The label-free common-universe transport is the existing artifact `orbittrace-final-sonotaco-label-free-preparation-v2` from run `31354363306`.

Known-shower truth/evaluation transport is the immutable artifact `orbittrace-v15-exposed-matched-sonotaco-literature-result-v1` from run `31405109267`, artifact digest `sha256:cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`.

Support-pruned candidate membership/ranking/results are prohibited from this transfer.

## Firewall order

If activated:

1. verify exact GMN PASS artifact and every source identity above;
2. load only the label-free 29,246-event SonotaCo common universe and exact 888-candidate baseline M2D ranked pretruth;
3. construct every fixed4 seed, annual drift fit, OAS covariance, per-event Mahalanobis distance, and halo membership;
4. serialize and SHA-256 freeze the complete 888-candidate parent/seed/halo mapping while known-shower truth is absent;
5. only then open the immutable SonotaCo truth/evaluator artifact;
6. run the same-parent paired utility evaluation exactly once;
7. preserve the first technically valid scientific PASS/FAIL.

A technical failure before a scientific result may receive only transport/provenance repair. Scientific method, parent rank, halo membership rule, confidence level and gates may not change.

## Frozen transfer gates

Copy the exact GMN gates for each established SonotaCo comparator route independently:

1. at least 20 parent-recovered paired assignments;
2. halo nonempty fraction >=0.75;
3. mean halo precision >=0.80;
4. mean halo precision strictly higher than parent mean precision;
5. mean halo F1 >=0.75 x parent mean F1;
6. among nonempty halos, >=50% have precision no lower than the parent;
7. mean halo F1 strictly higher than the exact fixed4-seed mean F1 on the same paired assignments.

The exact baseline parent discovery metrics must reproduce before any halo result is accepted. Halo rematching is diagnostic only and cannot rescue a same-parent gate failure.

## Claim boundary

A PASS is meaningful no-retuning cross-survey transfer of the membership/characterization layer, but SonotaCo remains an exposed benchmark rather than pristine external validation.

Only a PASS may authorize a separately frozen target-reference-absent application to the already-blind baseline M2D OrbitTrace catalogue. A FAIL closes this architecture; no SonotaCo-informed rescue is authorized.