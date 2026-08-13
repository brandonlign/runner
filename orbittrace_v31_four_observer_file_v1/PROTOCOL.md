# OrbitTrace GMN v31 four-observer confirmation v1

Binding target-excluded GMN 2022+2023 successor, frozen before the first official-file observer-count availability outcome and before any hard-family observer-count distribution is inspected.

Dormant prerequisite: the first valid `PASS_GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_V1` artifact from `agent/orbittrace-v31-observer-count-file-v1`. If that gate fails, this successor is not executed.

## Independent physical motivation

Vida et al. (2021) report median GMN radiant precision of about 0.47 degrees over all trajectories and about 0.32 degrees for meteors observed from **4 or more stations**. The official GMN schema defines `Num (stat)` as the number of stations observing a meteor. The frozen final SonotaCo normalizer independently exposes native `ncam`; therefore the same >=4 observer/camera definition is portable without using SonotaCo outcomes.

## Immutable parent

Exact passed GMN v31-principle parent source blob `b4e2d72e532e47aa95ed335f690748423d11ea59` and authoritative offline package artifact `9167087908`.

Parent controls must reproduce exactly:
- 226 candidates, 23D feature matrix SHA `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid SHA `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent margin SHA `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- fused @25/@50/@100 `23/41/66`, precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95`;
- exact five whole-shower folds, fold-training ordinary z-score, Euclidean k=1, margin `d_nonpositive-d_positive`, diversity lambda 0.8/scale 1.0, equal rank-sum with immutable hard order.

## Sole new coordinate

For immutable family i and year y:

`c_i,y = number of immutable members with observer_count >= 4 / number of immutable members in that year`.

GMN `observer_count` is native official monthly `Num (stat)` from the already-frozen availability mapping. The sole new coordinate is:

`observer_confirmation_i = min(c_i,2022, c_i,2023)`.

Append exactly this one scalar to the exact 226x23 parent matrix, producing 226x24. The annual minimum is frozen because recurrence requires support in both years and the feature is intended to reflect the weaker year's high-confirmation support.

No >=3/>=5 threshold, continuous/raw observer count, mean/median/max count, alternate annual fraction statistic, mean/geometric/harmonic cross-year combiner, station identity/geography, fit error, Qc, uncertainty, brightness/height, interaction, event weighting, feature-specific scaling, or second quality feature is allowed.

Run the exact parent OOF local-margin, nominal centroid diversity, hard-order fusion, and evaluator unchanged. Hash the observer-confirmation vector, 24D matrix, candidate margin, local order and fused order before metrics are emitted.

## Binding gate

PASS requires all:
- @25 >=23
- @50 >=41
- @100 >66
- top100 precision >=0.7229521515453452
- MRR >=0.050244164168646674
- qualified=95
- all provenance/firewall controls pass.

PASS `PASS_GMN_V31_FOUR_OBSERVER_CONFIRMATION_V1`; otherwise `FAIL_GMN_V31_FOUR_OBSERVER_CONFIRMATION_V1`.

A FAIL permanently closes this exact observer-confirmation lane and all nearby listed variants. No SonotaCo benchmark after FAIL. PASS only authorizes a separately frozen one-shot SonotaCo compatibility run using the exact same >=4 and annual-min-fraction rule with native `ncam`; SonotaCo remains exposed development, never external validation.