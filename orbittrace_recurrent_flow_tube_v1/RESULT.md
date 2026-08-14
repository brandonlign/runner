# OrbitTrace Recurrent Flow-Tube v1 — binding GMN 2022 development result

## Verdict

`FAIL_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY`

RFT v1 does **not** authorize GMN 2023 access. The frozen development gate failed decisively, so the already-frozen 2023 evaluator must remain dormant.

## Frozen provenance

- scientific protocol blob: `515362e69bec642a891e44dfd87dce9693942574`
- frozen scientific implementation blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`
- exact-equivalent direct-matrix execution head: `a9c4a9080034a95bfd234ae90fd197ecc5af85e8`
- first completed exact-equivalent matrix run: `31552655213`
- aggregate artifact: `9127201160`
- aggregate artifact digest: `sha256:0bd10203a15ad364f912c2edc058cb1775ecc987f4f1785eef3362615f3232b4`
- result JSON SHA-256: `e8d08ee421be680b6ae7ae11aa2f44897f61d649301ae7d2de5e87990929f817`
- candidate JSON SHA-256: `aa599faf4676d573f0e90a6d2691181df2503fc7d398a1041e89506bce7876fa`
- engineering report SHA-256: `adebcbb8cc44aa0ed02dc5269f404b4ff8c51b545e530b6f04c3fccd7dd59a9a`
- engineering report records `scientific_changes=false`, 17 exact replicas, and no GMN-2023 or SonotaCo access.

## Frozen main RFT v1 outcome

- retained candidates: **35**
- qualified known-shower matches: **20**
- recovered@25: **16**
- recovered@50: **20**
- recovered@100: **20**
- recovered@500: **20**
- top-100 dominant precision: **0.4856598221583339**
- MRR: **0.16750713557064975**
- median qualified candidates per recovered shower at top 500: **1.0**
- mean qualified candidates per recovered shower at top 500: **1.0**
- top-100 persistence `P>=0.75` share: **0.22857142857142856**

Frozen GMN-2022 viability required:

- qualified matches >=120 — **FAIL (20)**
- recovered@100 >=55 — **FAIL (20)**
- top-100 dominant precision >=0.60 — **FAIL (0.48566)**
- fragmentation median <=3.0 — PASS (1.0)
- at least 75% of top-100 retained candidates with persistence >=0.75 — **FAIL (22.86%)**

Only the fragmentation gate passed. The method therefore terminates before GMN 2023 exactly as preregistered.

## Preregistered explanatory ablations

### No perturbation persistence

- qualified matches: **133**
- recovered@25/50/100/500: **13 / 24 / 33 / 107**
- top-100 precision: **0.670272900136203**
- MRR: **0.025643930254796967**
- fragmentation median: **1.0**

Removing the persistence requirement restores substantial catalogue coverage, showing that the frozen perturbation-survival stage is strongly selective. However, even this explanatory ablation reaches only 33 recovered showers at rank 100 and is not an authorized successor.

### No path ownership

- qualified matches: **39**
- recovered@25/50/100/500: **2 / 8 / 29 / 39**
- top-100 precision: **0.7530672586627197**
- MRR: **0.04250117689029309**
- fragmentation median: **1.0**

Path ownership also suppresses coverage, though less dramatically than persistence.

### No trajectory trim

- qualified matches: **20**
- recovered@25/50/100/500: **17 / 20 / 20 / 20**
- top-100 precision: **0.48533038220625235**
- MRR: **0.16747583353934772**
- fragmentation median: **1.0**

Trajectory trimming is nearly outcome-neutral and is not the primary bottleneck.

## Interpretation and closure

RFT v1 succeeds at preventing fragmentation but does so by discarding far too much recoverable shower support. Coverage, early recovery, purity, and perturbation-persistence viability fail simultaneously. Under the frozen protocol this does not authorize a parameter rescue or GMN-2023 diagnostic.

Do not rescue RFT v1 by lowering persistence thresholds, changing perturbation amplitudes/counts, loosening reciprocal-neighbor atoms, changing k/bin width/physical scales, altering path ownership, lowering event/strata/span minima, changing the score, or using the explanatory ablations as post-result candidate methods. A future method must be independently motivated and separately frozen.

## Firewall

The binding artifact records:

- protected `[20.0,55.0]` excluded;
- `gmn_2023_access=false`;
- `sonotaco_2013_2014_access=false`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`.
