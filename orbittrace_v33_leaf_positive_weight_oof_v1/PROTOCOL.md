# OrbitTrace v33 exact-v24 positive-leaf-weight OOF ranker v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after exact-v24 regression, v31 local geometry, v32 binary leaf-support presence, and full-covariance geometry all failed the four-panel literature gate. Diagnostic #1024 isolated one narrower mechanism not tested by those successors: many missed annual-recoverable HDB families enter exact-v24 leaves containing positive training families, but those positives carry a much smaller fraction of the inherited group-balanced training weight than they do for surfaced groups. Binary support presence (#1032) subsequently failed, so this experiment tests the weight-fraction quantity itself and nothing else.

SonotaCo 2013/2014 remains exposed development-only.

## Sole successor score

Reuse the exact immutable #950/v24 71D pretruth payload, exact annual F1 targets, strict whole-shower folds, exact #839 inverse-group training weights, and exact v24 annual ExtraTrees regression forests.

For each deterministic OOF fold, year, held-out family, and each of the exact 600 v24 trees:

1. identify the exact terminal leaf reached by the held-out family;
2. among fold-training families in that same leaf, sum the inherited #839 training weights;
3. sum the same weights only for training families whose unchanged annual F1 is strictly greater than the frozen literature recovery threshold 0.5;
4. define that tree's positive-weight fraction as positive weight divided by total leaf weight;
5. average the positive-weight fraction over all 600 trees.

Every held-out leaf necessarily contains training samples in an sklearn fitted tree; zero total leaf weight is invalid and fails closed. No conditioning on positive presence is applied: leaves with no annual-positive training family contribute exactly zero.

The two annual scores combine by the already-frozen conservative rule `min(weight_fraction_2013, weight_fraction_2014)`. The exact #839 diversity rule (`lambda=0.8`, `scale=1.0`) follows, then one parameter-free equal rank-sum with the exact frozen v19 order. Only that fused order is the promotion candidate.

## Everything else frozen

- exact immutable #950/v22 71D features, memberships, family IDs, candidate universes, and centroids;
- exact v24 annual F1 regression targets and exact strict shared `SHOWER/<label>` five-fold assignment;
- exact v24 ExtraTrees capacity and random seed through the frozen #839 `model()` helper;
- exact #839 inverse-group sample weights;
- exact 600-tree forest; no tree subset;
- annual-positive threshold exactly `F1_y > 0.5` from the literature evaluator;
- no use of v24 regression predictions in the successor score;
- no use of binary leaf-presence support, conditional positive fraction, local geometry, leaf size, positive-group count, target mean, or any mixture;
- exact #839 diversity and exact v19 fusion;
- exact equal-budget one-to-one annual literature evaluator.

The same OOF forests must first reproduce all four exact v24 control metrics. Failure to reproduce is technical and yields no successor result.

## Binding gate

The first technically valid execution is binding. PASS requires the sole fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel.

Otherwise this exact positive-leaf-weight score is a permanent no-go. Failure does not authorize conditioning on positive presence, alternate weight definitions, thresholds, nonlinear transforms, leaf-size corrections, support mixtures, regression mixtures, geometry mixtures, tree subsets, target thresholds, model/feature changes, annual combiners, diversity/fusion changes, route-specific rules, source quotas, or a post-result search.

A full exposed-development forest/reference package may freeze only after a 4/4 OOF PASS. In-sample full-fit scores may never determine promotion.

No MAARSY, DMS, OrbitTrace target information, target-region event, or protected solar-longitude 20°–55° content may be accessed.