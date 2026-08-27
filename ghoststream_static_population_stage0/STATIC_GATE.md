# GhostStream versus NOP solution 004: frozen static population audit

Status: runner-only classification audit. This is not a discovery-method claim and cannot establish common origin. GhostStream is excluded from control selection, metric selection, matching, and thresholds.

## Why this test exists

The exact NOP solution-004 lookup table was shown to be observationally coherent. Public-source recovery produced 118 exact member orbits across CAMS, EDMOND, SonotaCo, and GMN, but the prospectively frozen recovery gate did not authorize backward dynamics.

The recovered population can still answer a narrower question: is the present-day orbital separation between GhostStream and NOP solution 004 more consistent with established branch pairs or with unrelated shower pairs matched on present-day distance and activity separation?

A static result is descriptive evidence only. It cannot prove or disprove shared ancestry, identify a parent, or replace expert classification.

## Frozen inputs

- canonical GhostStream artifact `8814798136`, ZIP SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`;
- real-shower audit artifact `8871850235`, ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- final NOP multisource artifact `8875235491`, ZIP SHA-256 `978e59f2e6b9c63644b0640d21662ab56307633da25d298bbb4d870dfb897ab7`;
- exact GhostStream population: all 101 canonical members;
- exact NOP population: all 118 recovered source-matched members, with no outlier removal or source reweighting.

Use q, e, inclination, argument of perihelion, and node with the Southworth-Hawkins distance exactly as implemented in the previous recovery audits.

## Frozen primary branch controls

- Southern/Northern Taurids: IAU `2/17`;
- Northern/Southern delta-Cancrids: `96/97`;
- Northern/Southern chi-Orionids: `256/257`.

Every component must contain at least 100 complete real GMN orbits across at least three frozen years.

## Frozen matched-distinct controls

Select one unrelated pair for each branch control from eligible real GMN showers. Selection occurs before any population-separation score is computed.

A candidate pair must:

- contain two showers from different MDC complex/parent units;
- exclude IAU 149 and every primary or sensitivity branch component;
- have at least 100 complete orbits per shower across at least three years;
- match the corresponding branch pair's representative-medoid `D_SH` within `0.08`;
- match its circular activity-center separation within `35°`;
- not reuse a shower selected for another distinct control.

Among eligible candidates, choose the deterministic minimum of

`(distance difference / 0.08)^2 + (activity-separation difference / 35)^2`,

with lexicographic IAU-number tie breaking. GhostStream and NOP are not used in selection.

## Frozen sampling

For every control and target pair:

- use 80 events per population for the primary score;
- select the primary sample deterministically, stratified proportionally by observing year for GMN populations;
- stratify GhostStream by observing year;
- stratify the combined NOP population by source;
- perform 400 stratified bootstrap replicates with replacement, preserving the primary sample's stratum counts.

CAMS-only and EDMOND-only NOP sensitivity tests use 40 events per population and 400 stratified bootstrap replicates. They are required because source-specific orbit reductions could otherwise drive the combined result.

## Frozen separation metrics

For two sampled populations A and B, calculate all pairwise `D_SH` distances.

Primary metric, normalized energy separation:

`E = max(0, 2*mean(D_AB) - mean(D_AA) - mean(D_BB)) / max((mean(D_AA)+mean(D_BB))/2, 1e-6)`.

Secondary metric, median separation ratio:

`R = median(D_AB) / max((median(D_AA)+median(D_BB))/2, 1e-6)`.

Within-population means and medians use only unique off-diagonal pairs.

## Frozen calibration gate

The static classifier is valid only if all hold before GhostStream-NOP is interpreted:

1. all three primary branch controls and all three matched-distinct controls pass the data gate;
2. every matched-distinct control has a larger point-estimate E than its corresponding branch control;
3. for every matched pair, the bootstrap 95% lower bound of `E_distinct - E_branch` is greater than zero;
4. the six control pairs have branch-versus-distinct AUROC `1.0` under E;
5. the six control pairs also have branch-versus-distinct AUROC `1.0` under R;
6. no one branch/distinct comparison contributes more than half of the total positive E gap.

If any calibration gate fails, verdict is `STATIC_CLASSIFIER_NOT_VALID`, and no GhostStream-NOP classification is reported.

## Frozen target interpretation

Only after calibration passes:

- define the branch envelope as the maximum 97.5th-percentile E across the three branch controls;
- define the distinct floor as the minimum 2.5th-percentile E across the three matched-distinct controls.

Combined NOP classification:

- `STATICALLY_DISTINCT_LIKE` only if GhostStream-NOP's 2.5th-percentile E exceeds the branch envelope and its median E is at least the distinct floor;
- `STATICALLY_BRANCH_COMPATIBLE` only if its 97.5th-percentile E is no greater than the branch envelope;
- otherwise `STATICALLY_AMBIGUOUS`.

Source robustness:

- run the same comparison against the recovered CAMS-only and EDMOND-only NOP subsets;
- a final `STATICALLY_DISTINCT_LIKE` result requires both source-specific 2.5th-percentile E values to exceed the branch envelope;
- a final `STATICALLY_BRANCH_COMPATIBLE` result requires both source-specific 97.5th-percentile E values to be no greater than the branch envelope;
- any disagreement forces `STATICALLY_AMBIGUOUS`.

## Claim boundary

Even a `STATICALLY_DISTINCT_LIKE` result means only that present-day orbital populations are more separated than the calibrated established branch controls. It does not prove different parentage. `STATICALLY_BRANCH_COMPATIBLE` means only that static separation cannot reject a branch-like relationship. `STATICALLY_AMBIGUOUS` leaves the classification unresolved.

No metric, control pair, sample size, source subset, bootstrap count, confidence bound, or threshold may change after execution.
