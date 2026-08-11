# OrbitTrace group-dense pairwise shower-recoverability SonotaCo OOF ranker v1

## Scientific role

This is a separately named exposed-SonotaCo development successor after the clean no-go in PR #1006. It does not rescue or retune #1004/#1006. The motivating evidence is limited to already-recorded exposed-development diagnostics: #1002 localized the HDBSCAN bottleneck to failure to surface recoverable shower groups, and #1004 showed that copying the already-frozen two-year recoverability label to every fragment in a strict shower group materially improved the HDBSCAN near miss while still failing 4/4.

## Sole scientific change

Keep the exact #1004 group-dense binary target, but replace pointwise probability classification with one strict-group pairwise ranking objective.

A strict `SHOWER/<label>` group is positive iff any stacked Sugar/HDBSCAN family in that group satisfies the already-frozen benchmark event `F1_2013 > 0.5 AND F1_2014 > 0.5`. Every family in that positive group receives target 1; all other families receive 0. The threshold 0.5 is inherited from the frozen recovered-shower literature evaluator and is not selected here.

For each deterministic whole-shower OOF training fold:

1. use the exact #839 inverse-group family weights already used by #1004;
2. form every positive-family versus negative-family training pair from different strict groups;
3. include both orientations `Xi-Xj` and `Xj-Xi`;
4. pair weight is exactly the product of the two inherited family group weights, so each positive-negative strict-group pair contributes equal total training mass regardless of fragmentation;
5. fit one `ExtraTreesClassifier` with the exact #997/#1004 capacity: 600 trees, depth 4, leaf 5, all features, seed 20260809, no class weight;
6. score each held-out family by antisymmetrized pairwise win probability against all fold-training families, averaged with the exact inherited group weights so each reference strict group has equal total mass.

The held-out shower group is absent from both the pair-training set and reference panel. No pair threshold, pair subsampling, pair margin, pair-weight exponent, class weight, calibration, resampling, feature selection, model-capacity search, or reference-panel search is authorized.

## Everything else frozen

- exact v22 71-dimensional pretruth features;
- exact fixed v19-expanded memberships and candidate universes;
- exact shared Sugar+HDBSCAN strict whole-shower five-fold assignment;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exact frozen v19 order as identity control and one parameter-free equal rank-sum fusion;
- only the fused order is a promotion candidate;
- exact #854-compatible equal-budget one-to-one annual literature evaluation.

## Binding gate

The first technically valid execution is binding. PASS requires the single fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel. Otherwise this exact group-dense pairwise objective is a permanent no-go. No post-result alternate pair weighting, classifier, diversity, fusion, or second search is authorized.

A full exposed-SonotaCo pairwise model/reference panel may freeze only after a 4/4 OOF PASS. In-sample full-fit scores may never determine promotion.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.