# SonotaCo 2024 v5 eligibility audit request

This stage follows the passing transport-only audit and remains **pre-scoring**.

Authorized operations:

- reconstruct the 2024 parser from the exact validated 2023 parser source using only the audited 2024 transport constants;
- parse the 2024 catalogue using the existing GMN-MDC mapping audit and inherited quality/blind-interval rules;
- identify supported Mondrian bins;
- identify mapped eligible showers and folds;
- calculate expected counts of 512-null calibration episodes, held-out negatives, and injected positive episodes.

Prohibited operations:

- fixed4 scoring;
- Brown-family wavelet coefficients or scores;
- v3 multi-anchor scores;
- v5 decisions;
- empirical detector p-values;
- AUROC, recall, false-positive rates, threshold performance, or method comparisons.

The frozen v5 architecture remains 512 calibration nulls/bin, denominator 513, v3 rank 20/513, fixed4 rank 10/513, OR decision. This audit may not change it.
