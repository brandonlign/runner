# Prior-art and novelty boundary

## Established ingredients

The following are not individually novel:

- virtual-year pooling;
- annual support checks;
- Poisson excess tests;
- partial-conjunction testing;
- order-statistic or product combination of study-level p-values;
- catalog-level calibration by simulated maxima;
- robust calibration against a specified null family.

ReplicaStream PR #8 already tested a meteor-search statistic based on the third-strongest annual evidence and failed against pooled detection plus annual confirmation. This Stage-0 does not reinterpret that result.

## Narrow contribution under test

The possible domain contribution is a leave-one-year-out recurrent meteor-stream scan that:

1. discards the strongest annual evidence channel to make one arbitrary year incapable of driving detection;
2. combines the next two strongest annual evidence channels instead of retaining only the weakest of the three;
3. calibrates the full adaptive search against both independent annual backgrounds and shared smooth annual structure; and
4. materially improves the recurrence-versus-artifact frontier over pooled, pooled-plus-confirmation, and hard partial-conjunction baselines.

This is potentially useful only if the complete frozen performance gates pass. Even a pass would leave novelty provisional until real known-shower, held-out-year, alternative-network, clustering, and wavelet comparisons are complete.

## Prohibited claims

Do not claim that truncated products, leave-one-out robustness, annual recurrence, or partial conjunction are new. Do not claim superiority to existing meteor-shower methods, robustness outside the tested null family, or validation on GhostStream.
