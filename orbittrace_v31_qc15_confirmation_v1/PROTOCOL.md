# OrbitTrace GMN v31 Qc>15 convergence-confirmation v1

Binding target-excluded GMN 2022+2023 successor protocol, frozen before the first four-observer outcome and before any immutable-family Qc distribution is inspected.

This protocol executes only if: (a) the four-observer successor has a binding FAIL or no scientific execution, and (b) the first valid `PASS_GMN_V31_QC15_AVAILABILITY_V1` artifact exists. It is not a threshold rescue of observer count; the physical mechanism and 15-degree threshold were selected independently from published trajectory-quality practice before that outcome.

## Independent physical motivation

Sugar et al. (2017) require camera–meteor–camera angle `Q* > 15 deg` when constructing their meteor-shower detection data set, excluding poorly measured trajectories. The GMN methodology uses maximum convergence angle in trajectory solving and performs additional Monte Carlo effort below 15 degrees. Official GMN schema defines native `Qc (deg)` as maximum convergence angle between all stations.

The frozen final SonotaCo normalizer exposes native `qcdeg` as `q1`, so the same >15-degree criterion is portable to a later separately frozen compatibility run without using SonotaCo outcomes.

## Immutable parent

Exact passed GMN v31-principle parent and authoritative offline package artifact `9167087908`. Parent 23D feature matrix SHA `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`, centroids SHA `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`, parent margin SHA `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Parent controls remain unchanged: 226 candidates; five exact whole-shower folds; fold-training ordinary z-score; Euclidean k=1 margin `d_nonpositive-d_positive`; nominal centroid diversity lambda 0.8 / scale 1.0; equal rank-sum with immutable hard order; @25/@50/@100 23/41/66; precision 0.7229521515453452; MRR 0.050244164168646674; qualified 95.

## Sole new coordinate

For immutable family i and year y:

`q_i,y = (# immutable members in year y with native maximum convergence angle Qc > 15 degrees) / (# immutable members in year y)`.

The sole appended coordinate is:

`qc15_confirmation_i = min(q_i,2022, q_i,2023)`.

Append exactly this one scalar to the exact 226x23 parent matrix, yielding 226x24. The weaker-year minimum is frozen because recurrence is required in both years.

Scientific execution requires valid Qc for **all 8,794 immutable members**. Missing values cause a pre-science stop; no imputation, deletion or denominator change.

No >=/>, 10/12/20-degree alternate threshold, raw/mean/median/min/max Qc, continuous transform, alternate annual summary, mean/geometric/harmonic cross-year combiner, observer-count interaction, fit-error companion, uncertainty, station identity/geography, event weighting, feature-specific scaling, or second quality feature is allowed.

Run exact parent OOF margin, nominal centroid diversity, hard-order fusion and evaluator unchanged. Hash the feature vector, X24, candidate margin, local order and fused order before metrics.

## Binding promotion gate

PASS requires @25>=23, @50>=41, @100>66, top-100 precision>=0.7229521515453452, MRR>=0.050244164168646674, qualified=95, and all provenance/firewall controls.

PASS `PASS_GMN_V31_QC15_CONFIRMATION_V1`; otherwise `FAIL_GMN_V31_QC15_CONFIRMATION_V1`.

A FAIL permanently closes this exact convergence-confirmation lane and nearby result-motivated variants listed above. No SonotaCo benchmark after FAIL. PASS only authorizes a separately frozen one-shot SonotaCo compatibility run of the exact >15 / annual-min-fraction rule; SonotaCo remains exposed development only.