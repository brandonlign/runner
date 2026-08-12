# OrbitTrace GMN–SonotaCo covariate-overlap diagnostic v1

## Status

Frozen before the first result-bearing execution. This is a truth-free feasibility diagnostic for covariate-shift importance weighting, not a scientific shower ranker and not external validation.

## Motivation

The frozen 21D GMN–SonotaCo domain diagnostic established strong survey shift (OOF ROC AUC 0.88356922921475). Subsequent simple representation fixes did not solve it: catalogue-relative percentile normalization destroyed useful absolute physical information in SonotaCo, robust scaling failed, and the rank-3 nuisance-nullspace representation reduced domain AUC by only 0.03334 while damaging GMN local neighborhoods.

A distinct, established domain-adaptation mechanism is covariate-shift correction: retain the absolute representation unchanged and reweight source-domain training observations by an estimated target/source density ratio. This can only be scientifically defensible if target-like source support is sufficient and the implied weights do not collapse the effective source sample size. This diagnostic tests that prerequisite only.

## Frozen inputs

Exactly the same truth-free representation and folds as `orbittrace_gmn_sonotaco_domainshift_diagnostic_v1`:

- target-excluded GMN 2022/2023 hard + P19 + P20: 4,504 families;
- canonical label-free SonotaCo 2013/2014 hard + P19 + P20: 334 families;
- exact same 21 generic source-blind features;
- exact same deterministic five folds balanced within survey-domain × generator-source strata;
- exact same HGB domain classifier and inverse-domain-size fold-training weights.

The authoritative prior diagnostic artifact with exact OOF AUC `0.88356922921475` must reproduce before any overlap result is accepted.

No SonotaCo shower truth, matched comparator rows, literature outcome, OrbitTrace target information/events, MAARSY, or DMS may be loaded.

## Frozen density-ratio estimator

The domain classifier is fit exactly as in the frozen diagnostic. Because inverse-domain-size training weights make the effective domain prior exactly 1/2 versus 1/2 in each fold, the held-out posterior odds are used directly as the cross-fitted density-ratio estimate:

`w(x) = P(SonotaCo | x) / (1 - P(SonotaCo | x)) ≈ p_SonotaCo(x) / p_GMN(x)`.

No clipping, trimming, temperature, calibration, exponent, normalization choice, feature subset, alternate domain model, or density-ratio method is searched. Any probability not strictly between 0 and 1 fails closed.

Only GMN rows receive density-ratio weights, because these are the source observations that would be reweighted in a later separately frozen scientific successor. Weight scale is irrelevant for ESS; normalized shares are used only for concentration diagnostics.

## Frozen overlap statistics

Report overall and separately within hard, P19, and P20:

- raw density-ratio weight quantiles on GMN rows;
- Kish effective sample size `ESS=(sum w)^2/sum(w^2)` and `ESS/n`;
- largest normalized GMN weight share `max(w)/sum(w)`;
- a domain-overlap coefficient estimated from the cross-fitted equal-prior posterior,
  `OVL = E_m[2 min(e(x),1-e(x))]`, where `m=(p_GMN+p_SonotaCo)/2`; empirically this is the equal-domain average of `2 min(e,1-e)`.

The 21D feature representation is not changed in this experiment, so there is no representation-destruction pathway: `feature_representation_changed=false` is a required firewall field.

## Frozen feasibility gates

The importance-weighting lane passes only if all conditions hold on the first technically valid execution:

1. exact baseline OOF domain AUC reproduces within `1e-12` of the authoritative artifact;
2. all cross-fitted probabilities and GMN density-ratio weights are finite with `0 < e(x) < 1` and `w(x) > 0`;
3. overall GMN ESS fraction is at least `0.25`;
4. hard, P19, and P20 GMN ESS fractions are each at least `0.20`;
5. the largest normalized GMN weight share is at most `0.01` overall;
6. the largest normalized weight share is at most `0.05` within each source stratum;
7. overall estimated overlap coefficient is at least `0.30`;
8. the overlap coefficient is at least `0.20` within each source stratum.

These are feasibility screens, not tuned performance targets. Failure permanently closes direct untrimmed domain-classifier importance weighting on this 21D representation. No rescue by clipping/winsorizing weights, changing exponents/temperatures, changing the domain classifier, choosing feature subsets, alternate density-ratio estimators, source-specific thresholds, or post-result searches is authorized from this outcome.

A PASS does not establish a better shower ranker. It authorizes exactly one separately frozen target-weighted GMN source-blind ranker using the unchanged absolute 21D representation and the exact cross-fitted density ratios, before any SonotaCo truth is seen for that successor.

## Protected-data firewall

- Protected solar longitude `[20.0,55.0]` remains excluded from GMN construction.
- SonotaCo shower truth access: false.
- Literature-comparator evaluation: false.
- Matched comparator rows used: false.
- OrbitTrace target-information access: false.
- Protected target-region events accessed: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- Feature representation changed: false.
- Scientific shower ranker trained: false.
- Post-result second search: false.
