# Shared latent-flux scan protocol

## Motivation

The multiscale leave-one-network-out score failed because removing the largest contribution discards legitimate evidence whenever survey sensitivity or observed stream amplitude differs across networks. The replacement must model heterogeneity rather than simply weakening the dominance penalty.

## Primary statistic

For candidate center `c`, scale `r`, and network `n`:

- `k_n(c,r)` is the inner-neighborhood count;
- `b_n(c,r)` is the network-specific expected count estimated from an outer shell;
- `w_n` is the prespecified effective-exposure weight, set to one in the equal-sample surrogate.

Under the null:

`k_n ~ Poisson(b_n)`.

Under a shared physical component:

`k_n ~ Poisson(b_n + phi * w_n)`, with one latent stream rate `phi >= 0` shared across networks.

The candidate score is the profile log-likelihood ratio after maximizing over `phi`. At least two networks must independently have positive local excess evidence. The complete maximum over candidate locations and scales `{0.70, 0.90, 1.10, 1.30}` is calibrated under real null scenes.

This is a joint model, not a sum of independently thresholded detections. It permits unequal observed counts because each network retains a different background while preventing a component supported by only one network.

## Independent test design

- 96 calibration-null scenes;
- 96 independent test-null scenes;
- 128 paired injection scenes per condition;
- new random seeds unused by either previous surrogate;
- real 20-degree solar-longitude background windows outside M2026-A1;
- 600 sampled background events per network and scene.

## Weak-signal conditions

Across compact, nominal, and diffuse intrinsic dispersions, evaluate:

- balanced amplitudes `(4,4,4,4)`;
- moderate heterogeneity `(4,6,3,3)`.

Additional nominal-dispersion controls:

- strong survey dominance `(2,8,2,2)`;
- three-network signal `(4,5,0,4)`;
- GMN-only artifact `(0,10,0,0)`;
- strong shared signal `(8,8,8,8)`;
- balanced signal after GMN is removed entirely.

## Baselines

Every comparison method receives the same multiscale candidate search and separate null threshold:

- pooled scan;
- maximum single-network score;
- second-network replication score;
- failed hard leave-one-network-out score;
- unprotected sum of network scores.

## External control

After thresholds are frozen, scan the M2026-A1 activity region and compare the accepted maximum with the published trajectory. It is not a tuning target.

## Statistical reporting

- independent null false-positive rate with Wilson 95% interval;
- paired recovery decisions for every method;
- paired bootstrap interval for mean primary gain over the strongest baseline;
- selected scale distribution;
- no-GMN dropout analysis.

## Frozen continuation gates

The shared latent-flux statistic earns a full known-stream benchmark only if every gate passes:

1. test-null false-positive rate <= 0.10 and Wilson upper 95% bound <= 0.15;
2. mean recovery over all six balanced/moderately heterogeneous dispersion conditions exceeds the strongest baseline by >= 0.10 with paired-bootstrap lower 95% bound > 0;
3. primary recovery is not more than 0.10 below the strongest baseline in any individual weak condition;
4. recovery of the strongly dominant `(2,8,2,2)` shared signal exceeds pooled recovery by >= 0.05;
5. recovery of the three-network signal is at least 0.50;
6. GMN-only artifact recovery <= 0.10;
7. strong shared recovery >= 0.90;
8. the untouched M2026-A1 control is accepted near its published trajectory;
9. after excluding GMN, balanced weak recovery is at least 0.50 and at least 0.05 above pooled search.

Failure means the shared-network methodology direction is not yet strong enough to attach to GhostStream. Passing permits only a larger parent-stream-disjoint and known-stream benchmark.
