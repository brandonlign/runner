# InvariantStreamNet frozen-model diagnostic

This is a post-hoc diagnosis of the failed real-ESV transfer gates. It does not alter, rerun, or override the frozen Stage-0 verdict.

## Original published center

- Raw global logit: 0.1854
- Frozen membership threshold: 0.70
- Member-probability median / maximum: 0.3254 / 0.4463
- Predicted members at frozen threshold: 0
- Best post-hoc threshold F1: 1.000 at 0.05

## Fair center scan

- Best center: [7.199999999999999, 208.4, -19.3, 29.6]
- Best raw logit: 0.8169
- Percentile against null catalogs scanned over the identical offset bank: 0.8917
- Predicted members at frozen threshold: 0
- Best post-hoc threshold F1: 1.000 at 0.05

## Dense synthetic controls

- train: member F1 0.721, predicted members 27.0 per 48
- unseen: member F1 0.650, predicted members 23.1 per 48

## Decision use

If the fair scan remains non-significant and membership probabilities remain far below the frozen threshold while dense synthetic controls succeed, the failure is synthetic-to-real morphology transfer rather than center choice or stream occupancy. The current model must remain rejected.
