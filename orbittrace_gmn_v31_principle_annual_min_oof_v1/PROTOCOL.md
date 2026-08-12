# OrbitTrace GMN v31-principle annual-min OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 successor diagnostic** to the already-passed GMN v31-principle local-geometry OOF diagnostic. It does not access SonotaCo, the protected OrbitTrace target region, target information, MAARSY, or DMS.

The motivation is frozen before outcome. The parent GMN diagnostic showed that the v31 nearest-positive / nearest-nonpositive reference geometry principle generalized strongly using one overall recoverability target on the exact 23D intrinsic family representation. The original SonotaCo v31 architecture, however, is explicitly recurrence-robust: it computes year-specific local-geometry margins and conservatively combines them with a minimum. This diagnostic asks whether **annual robustness itself adds independent value on GMN**, while keeping the successful parent representation and every other ranking choice fixed.

This is not a response to any SonotaCo panel result and no SonotaCo data are used to choose the rule.

## Immutable parent

Parent: `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF`.

Binding parent metrics:
- recovered@100: `66`
- recovered@50: `41`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified families: `95`
- overall OOF margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

The candidate universe remains exactly the same 226 P19 hard families with unchanged memberships and immutable hard order.

## Representation

Use exactly the parent 23D intrinsic representation, unchanged:
- ten intrinsic structural features;
- seven cohesion features;
- six centroid-neighborhood descriptors.

No feature, metric, scaling, representation, or membership change is permitted.

## Annual fixed-label recovery target

Use exactly the same target-excluded GMN eligible recurrent-shower universe and each family's frozen overall `best_label` from the parent GMN evaluator.

For a family that is not overall qualified under the frozen GMN definition (`precision >= 0.5` and overlap >= 4), or has no best eligible label, both annual F1 values are exactly zero.

Otherwise, for each year separately (2022, 2023), compute event-level F1 against that **same fixed best label** using only the family's members from that year and only truth events from that year:
- annual precision = annual overlap / annual family member count;
- annual recall = annual overlap / total eligible events for that fixed label in that year;
- annual F1 is the harmonic mean.

An annual reference is positive exactly when `annual F1 > 0.5`; otherwise it is nonpositive. No annual threshold search or alternate label selection is allowed.

## Strict OOF geometry

Use exactly the parent deterministic five-fold whole-shower groups and exact parent training-only z-standardization.

For each fold and each year separately:
- `k=1` ordinary Euclidean distance to nearest annual-positive training reference;
- `k=1` ordinary Euclidean distance to nearest annual-nonpositive training reference;
- annual margin = `d_nonpositive - d_positive`.

The sole annual combination is the exact v31 conservative rule:

`combined_margin = min(margin_2022, margin_2023)`.

Then apply exactly the parent diversity (`lambda=0.8`, `scale=1.0`) and exactly one equal rank-sum fusion with the immutable hard order.

No mean/max/product annual combiner, k change, metric change, calibration, threshold, weight, diversity, or fusion alternative is evaluated.

## Parent provenance control

In the same execution, reconstruct the already-frozen parent **overall** OOF margin from the same 23D matrix and require exact SHA256 equality to `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`. Its fused metrics must reproduce the five binding parent values above before the annual-min candidate is accepted as a technically valid outcome.

This reconstruction is a provenance control, not a second candidate search.

## Binding gate

The first technically valid outcome is binding.

PASS requires annual-min fusion to simultaneously:
- recover **strictly more than 66** families in the top 100;
- recover at least 41 in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly 95 qualified families.

Failure of any gate permanently rejects this exact annual-min GMN successor. No alternate annual threshold, annual label rule, combiner, k, metric, features, diversity, fusion, or post-result rescue is authorized.

A PASS would motivate, but not itself authorize, any future separately frozen cross-dataset successor.

## Firewall

- blind exclusion remains `[20.0,55.0]`;
- SonotaCo 2013/2014 access: false;
- OrbitTrace target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
