# Prior-art and novelty boundary

## Closest established approaches

Meteor-stream searches already use:

- orbital similarity criteria and pair-excess statistics;
- DBSCAN and HDBSCAN clustering;
- wavelet or binned radiant-density maps evaluated across solar longitude;
- radiant-drift fitting after a candidate is found;
- synthetic or KDE sporadic backgrounds and multiple-testing corrections;
- matched filters for detecting individual meteor streaks in images.

None of those ingredients is individually novel.

## Narrow hypothesis being tested

The possible contribution is a **catalog-search detector that integrates subthreshold evidence along an entire physically constrained radiant-drift tube**, scans duration, width, and drift jointly, and calibrates the maximum over the complete adaptive template bank at catalog level.

This is materially different only if it recovers sparse drifting streams that do not create a significant static peak, at matched false-catalog probability.

## Claims prohibited at Stage 0

Do not claim that:

- matched filtering is new;
- radiant drift is new;
- likelihood-ratio testing is new;
- catalog-level multiple-testing correction is new;
- the detector is better than clustering;
- the method has been validated on GhostStream;
- the method is the first of its kind.

## Kill boundary

If the drifting bank does not materially outperform the otherwise identical zero-drift bank, the method is merely a larger scan with a larger look-elsewhere penalty and should be killed.

Even if Stage 0 passes, novelty remains provisional until a literature-complete review and independent comparisons against HDBSCAN, DBSCAN, wavelet/pair-excess searches, and known weak showers are completed.
