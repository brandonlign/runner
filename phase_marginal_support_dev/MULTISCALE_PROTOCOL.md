# Multiscale phase-marginal support: frozen July development protocol

Status: development-only test on retired July 2026 data.

## Question

Can nested conformal calibration adapt between small and larger weak-shower structures without sacrificing the k=4 sensitivity gained by phase-marginal coherence?

## Fixed component scores

For each 128-event window, use the same radiant/speed-only four-star construction as the completed eight-star test. Sort all 128 star diameters and compute three component scores:

- negative mean of the tightest **4** stars;
- negative mean of the tightest **8** stars;
- negative mean of the tightest **16** stars.

These represent compact four-member evidence, intermediate support, and broader weak-stream support. Solar longitude remains excluded from within-window similarity and is used only for window construction and local calibration.

## Phase-local scale adaptation

For each target window and each component separately:

1. select the same 128 inner-reference windows nearest in circular solar longitude;
2. interpolate the component score within that component's empirical CDF;
3. convert it to an upper-tail coordinate;
4. take the minimum of the three component tail coordinates as the adaptive multiscale statistic.

The minimum is not treated directly as a p-value. An independent 512-window outer bank is passed through the identical three-scale procedure, and the final inferential p-value is the conservative outer conformal rank of the target statistic. Thus scale selection is included inside the calibrated procedure rather than chosen after seeing a target.

## Frozen development run

- exact retired July data, shower panel, blocks, blind interval, seeds, and window generator from PR #48;
- 512 inner windows and 512 independent outer windows per block;
- 256 negative windows per block;
- eight positive replicates for k in {4,6,8,12};
- unchanged density and DBSCAN comparators;
- candidate AUROC uses the negative locally normalized minimum-tail statistic.

This benchmark decides only whether the multiscale construction merits an untouched 2018 confirmation. It cannot authorize GhostStream application.
