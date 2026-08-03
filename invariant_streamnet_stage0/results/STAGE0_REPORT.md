# InvariantStreamNet Stage-0 result

**Verdict:** `KILL_OR_REDESIGN_INVARIANT_STREAMNET`

The neural detector was trained on CAMS, EDMOND, and SonotaCo backgrounds only. GMN was held out entirely for labeled evaluation; only unlabeled GMN background patches set the one-percent operating threshold.

## Primary held-out unseen-morphology comparison

- Neural TPR / FPR: 0.579 / 0.016
- Engineered baseline TPR / FPR: 0.239 / 0.018
- TPR gain: +0.340
- Neural segmentation F1: 0.648
- Neural ECE: 0.064

## Real ESV holdout

- Conservative ESV members in selected GMN patch: 48
- Neural negative percentile: 0.9645
- Engineered baseline negative percentile: 0.9094
- Neural member F1: 0.000

## Frozen gates

- PASS — `heldout_unseen_fpr_at_most_0_03`
- PASS — `heldout_unseen_tpr_gain_at_least_0_10`
- PASS — `heldout_unseen_neural_tpr_at_least_0_50`
- PASS — `heldout_unseen_segmentation_f1_at_least_0_60`
- PASS — `heldout_unseen_ece_at_most_0_10`
- FAIL — `real_esv_score_above_99th_percentile`
- FAIL — `real_esv_member_f1_at_least_0_50`

## Interpretation

A pass would only justify a larger parent/shower-disjoint benchmark and full catalog scan. It would not establish novelty or permit applying the detector to GhostStream. A failure means the current architecture or synthetic-training formulation is rejected.
