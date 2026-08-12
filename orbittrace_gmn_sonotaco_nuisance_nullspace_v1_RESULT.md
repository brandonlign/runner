# OrbitTrace GMN–SonotaCo nuisance-nullspace representation v1 — binding result

## Verdict

`FAIL_NUISANCE_NULLSPACE_V1_TRUTH_FREE_REPRESENTATION_GATE`

This is a clean scientific failure of the sole preregistered truth-free nuisance-nullspace representation diagnostic. It is not a technical failure. The authoritative GMN–SonotaCo domain-shift baseline reproduced exactly, the frozen projection executed in all five strict OOF folds, all provenance and protected-data assertions passed, and the artifact uploaded successfully.

## Frozen provenance

- protocol freeze commit: `c2c073bfd1879da7a6e80d726ce2eeeadb976952`
- implementation freeze commit: `d9998cf8a9aba7d0c355e263b2361855826c15ff`
- execution workflow commit: `6f3828315114478864c86769cb3dcafeb93e1537`
- first technically valid binding run: `31631011817`
- binding job: `94229452812`
- binding artifact: `orbittrace-gmn-sonotaco-nuisance-nullspace-v1`
- artifact ID: `9155183244`
- artifact digest: `sha256:52136a1b47c4b4bbacc9f7c4ec4b17d351e7dbfdbd699a8198a40128741d6b57`

## Sole scientific change

Using only survey identity and the already-frozen 21D generic source-blind representation, each fold:

1. applied pooled fold-training ordinary z-scaling;
2. computed SonotaCo-minus-GMN fold-training mean-difference vectors separately for hard, P19, and P20;
3. stacked those three vectors into a 3×21 nuisance matrix;
4. removed its complete numerical row-space by orthogonal projection using SVD tolerance `1e-12`;
5. trained the exact frozen HGB survey classifier on the projected training rows and predicted the held-out rows.

The nuisance rank was 3 in every fold. No shower truth, comparator outcome, feature subset, component-count search, robust scaling, threshold search, or scientific ranker was used.

## Exact baseline reproduction

- OOF ROC AUC: `0.88356922921475`
- balanced accuracy: `0.7082254230437881`

## Binding projected outcome

- OOF ROC AUC: `0.8502249497452696`
- balanced accuracy: `0.7045686601929356`
- AUC reduction: `0.033344279469480376`

Truth-free structure retention:

- GMN pairwise-distance Spearman: `0.9770113868566086`
- SonotaCo pairwise-distance Spearman: `0.9559691713946422`
- GMN mean 10-NN retention: `0.6758402195802807`
- SonotaCo mean 10-NN retention: `0.814314789687924`

Gate results:

- baseline exact reproduction: PASS
- AUC reduction >= 0.10: **FAIL**
- GMN pairwise-distance Spearman >= 0.90: PASS
- SonotaCo pairwise-distance Spearman >= 0.90: PASS
- GMN 10-NN retention >= 0.70: **FAIL**
- SonotaCo 10-NN retention >= 0.70: PASS
- nuisance rank 1–3 in every fold: PASS

## Scientific interpretation

The three generator-stratified survey mean-shift directions are real but insufficient. Removing their complete rank-3 span preserves global pairwise geometry very well, especially in GMN, yet reduces survey discriminability only modestly and perturbs GMN local neighborhoods beyond the frozen tolerance. Therefore the strong GMN↔SonotaCo shift is not well approximated by this small linear first-moment nuisance subspace.

This exact lane is permanently closed. Do not rescue it by choosing rank 1 or 2 after this result, changing SVD tolerance, source stratification, standardization, classifier, folds, feature subsets, neighborhood k, structure thresholds, weighting, nonlinearizing this same mean-difference projection, or selecting another projection/alignment variant from this outcome.

A later successor must introduce a genuinely distinct representation mechanism and be separately frozen before its first outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar-longitude exclusion `[20.0, 55.0]`;
- SonotaCo shower truth access: false;
- literature evaluation: false;
- matched comparator rows used: false;
- OrbitTrace target-information access: false;
- protected target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false;
- post-result second search: false.
