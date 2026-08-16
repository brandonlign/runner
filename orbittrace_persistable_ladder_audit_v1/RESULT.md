# OrbitTrace Persistable persistence-ladder synthetic audit v1 — binding result

## 🟢 POSITIVE

Authoritative run: `31954790384`

Job: `95183657085`

Artifact: `orbittrace-persistable-ladder-audit-v1` (`9265656748`)

Artifact digest: `sha256:781d2ca3d86395ea107e3dc0d0de5a08bd3b564823ccbf96d3020e8580abec75`

Verdict: `PASS_PERSISTABLE_LADDER_SYNTHETIC_FEASIBILITY`

No meteor data or target information was accessed.

The exact default-midpoint persistence-ladder architecture passed every frozen gate in all four deterministic nested 6,144 -> 768 synthetic replicates.

Symmetric dense/sparse mean-best-Jaccard by seed:

- `202608160`: **0.7963808139534885**
- `202608161`: **0.7888105149552882**
- `202608162`: **0.8116099200435339**
- `202608163`: **0.7852104212670428**

Directional means remained above the frozen 0.50 floor in every replicate. Dense exact-membership-union candidate counts were only `6, 6, 6, 7`; sparse counts were `5, 5, 4, 6`, all far below the architectural ceiling 119.

This contrasts with the separately closed automatic-flat-selector result in PR #1280: no global `n_clusters` or prominence-gap choice exists here. Candidate memberships are the exact union of conservative persistence flattenings for all counts 2..15 on the package-default midpoint hierarchy.

This PASS authorizes only the separately pre-frozen zero-label target-excluded GMN cross-scale diagnostic on branch `agent/orbittrace-persistable-ladder-crossscale-v1`. That protocol and implementation were committed before this synthetic outcome and may not change from this result.