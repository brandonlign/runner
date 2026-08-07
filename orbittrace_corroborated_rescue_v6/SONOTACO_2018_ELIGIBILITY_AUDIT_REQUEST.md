# SonotaCo 2018 v6 eligibility audit request

This stage follows the passing transport-only audit and remains **pre-scoring**.

Authorized operations:

- reconstruct the SonotaCo 2018 parser from the exact validated 2023 parser source using only audited 2018 transport constants;
- parse the 2018 catalogue using the existing GMN-MDC mapping audit and inherited quality/blind-interval rules;
- identify supported Mondrian bins;
- identify mapped eligible showers and folds;
- calculate expected counts of 512-null calibration episodes, held-out negatives, and injected positive episodes.

Prohibited operations:

- fixed4 scoring;
- Brown-family wavelet coefficients or scores;
- v3 multi-anchor scores;
- v6 decisions;
- empirical detector p-values;
- AUROC, recall, false-positive rates, threshold performance, or method comparisons.

The frozen v6 rule remains:

`(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))`.

A prospective scientific execution is not authorized until a passing eligibility result has been committed as an immutable freeze and a separate one-shot 2018 validation protocol is committed before scoring.
