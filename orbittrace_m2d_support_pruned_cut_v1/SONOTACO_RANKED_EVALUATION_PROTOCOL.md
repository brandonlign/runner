# Support-pruned M2D SonotaCo ranked-only evaluation

## Scope

This is an engineering-only execution wrapper for the already-frozen support-pruned M2D SonotaCo transfer. It may not recompute candidate generation, support pruning, M2D scores, ranking, parameters, comparator values, or scientific gates.

The complete candidate ranking must come only from GitHub Actions run `32288839233`, produced from support-pretruth SHA-256 `6ae27f985340eaa41870ab4c4f8cd15d6a1cd97e03ef828254f4c24d7896176a` with truth absent. The ranked artifact must contain exactly 907 candidates and must carry its own SHA-256 seal. If that ranking run does not finish successfully, this evaluation is not authorized.

The scientific evaluator is the already-committed `orbittrace_m2d_support_pruned_cut_v1/evaluate_sonotaco_ranked.py`, Git blob `0572a001624b951dda6231d6046508f14ccc0e36`. The baseline/evaluation helper is exact pre-result internal-mass SonotaCo source commit `5b9cf92ae598f72ffd8167ecbc26de0de4e709e7`, whose `run_binding.py` Git blob is `b44e0222e08ae4e85f0ea9a91c95f7b9141f3fb9`.

## Inputs

- label-free common-universe rows: artifact `orbittrace-final-sonotaco-label-free-preparation-v2`, run `31354363306`;
- sealed support-pruned candidate pretruth: artifact `orbittrace-m2d-support-pruned-cut-v1-sonotaco-pretruth`, run `32287719630`, SHA-256 `6ae27f985340eaa41870ab4c4f8cd15d6a1cd97e03ef828254f4c24d7896176a`;
- sealed exact M2D ranking: artifact `orbittrace-m2d-support-pruned-cut-v1-sonotaco-ranked-pretruth`, run `32288839233`; its exact file SHA must be read from and checked against the artifact's `RANKED_PRETRUTH_SHA256.txt` before truth access;
- immutable exposed SonotaCo truth package: artifact `orbittrace-v15-exposed-matched-sonotaco-literature-result-v1`, run `31405109267`.

The truth package above is the same package used by the binding internal-mass SonotaCo reproduction run `32259703637`; this wrapper changes no truth semantics.

## Firewall order

1. Verify source identities and exact runtime.
2. Download rows, support pretruth, and sealed ranked pretruth only.
3. Verify all pretruth identities, candidate count, rank sequence, truth flags, and exact ranked SHA while `input/truth` does not exist.
4. Only after those checks pass, download the immutable truth artifact.
5. Run `evaluate_sonotaco_ranked.py` exactly once.
6. Preserve the resulting PASS/FAIL artifact and provenance.

No technical failure before a result exists may alter scientific source, ranking, thresholds, baselines, comparators, or gates. A technically valid scientific FAIL is binding.