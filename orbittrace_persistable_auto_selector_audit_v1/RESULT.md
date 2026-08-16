# OrbitTrace deterministic Persistable selector — synthetic audit result

## 🔴 NEGATIVE

Authoritative run: `31954525009`

Job: `95182985906`

Artifact: `orbittrace-persistable-auto-selector-audit-v1` (`9265587300`)

Artifact digest: `sha256:a9c1fed40fd728f7cb94316145ce000c9f47f21016f2dea32c99e02d21085392`

Result SHA-256: `a18d0b6c6f11bbde5a62a87b1d8f9e60b02e09ebc641a9abdb9b27c4829c5ca4`

Verdict: `FAIL_PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_FEASIBILITY`

The run used no meteor data and no target information.

Three of four frozen nested-sample replicates passed all gates. Their dense-vs-sparse adjusted Rand indices were:

- seed `202608160`: `0.7788932469`;
- seed `202608161`: `0.9963186939`;
- seed `202608162`: `0.9751363096`.

The fourth replicate failed the predeclared cluster-count stability gate:

- seed `202608163` cross-scale ARI: `0.5962527787` (ARI gate passed);
- dense requested/returned clustering: gap `5`, returned `5` clusters;
- sparse requested/returned clustering: gap `2`, returned `2` clusters;
- absolute cluster-count difference: `3`, exceeding the frozen maximum `2`.

All runs had valid finite prominence structures, valid default slices, no insufficient-neighbor warning, and at least two returned clusters. The failure is therefore a selector-stability failure rather than a package/runtime failure.

The exact automatic rule—default vineyard slices plus mean normalized nontrivial prominence-gap selection—is closed. It may not be rescued by changing the gap statistic/range, default slices, vineyard resolution, tie rules, neighbor policy, flattening mode, synthetic panel, seeds, or gates.

Because the pre-frozen conditional GMN protocol `agent/orbittrace-persistable-crossscale-v1` requires an exact synthetic PASS, that GMN execution is permanently blocked and must not run.

The result does **not** close multiparameter persistence as a whole. It specifically shows that reducing the hierarchy to one automatically selected global flat cluster count can itself be unstable under thinning. A genuinely distinct future architecture would need to use the persistent hierarchy/candidate features directly rather than rescue this flat-selector rule.