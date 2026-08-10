# Final SonotaCo 2013/2014 frozen-#839 external applicability result

## Frozen conclusion

`NOT_EVALUABLE_FROZEN_839_EXTERNAL_APPLICABILITY_FAILURE`

The preregistered final SonotaCo 2013/2014 literature comparison cannot reach a #839 primary catalogue under the already-frozen #839 architecture. This is **not** a loss to Sugar or catalogue HDBSCAN and **not** a truth-based performance result.

The decisive failure occurs before known-shower truth opens, inside the frozen hard-v8 sparse-support multiplicity stage. The frozen multiplicity implementation requires an exact 128-event local episode for every hard family/year, using the inherited 10-degree local window. On the authorized SonotaCo pairwise row universes, at least one hard family in each comparator-matched universe has fewer than 128 available events:

- Sugar-matched pairwise universe: family `Gc21a7e41ce3d`, year 2013, local-window count = **58**.
- catalogue-HDBSCAN-matched pairwise universe: family `G7211c7f43e2b`, year 2013, local-window count = **49**.
- frozen required episode size = **128**.

The frozen implementation fails closed when `len(window_events) < EPISODE_SIZE`; no fallback to fewer events, family deletion, window widening, imputation, or other post-access adaptation was preregistered. None is introduced here.

## Execution provenance

- final execution PR: `#902`
- final execution workflow: `OrbitTrace final SonotaCo 2013/2014 one-shot v2`
- workflow run: `31354363306`
- execution trigger commit: `0c9e04810c27924eec08d9e8830f3d87ffa4da1a`
- repaired/audited execution base before r4: `191152d537996f32cfefdf9e90f43e55cd37b338`
- pair-portable generator source: PR `#862`, commit `7dd59b5d2be7c0040f42ee494c9bd8b71ccb0d8b`
- frozen v8 support/runtime checkout: `c9d6c44704013ba0c9430100e98a29a56b453304`
- frozen multiplicity source: `orbittrace_sparse_support_multiplicity_v5/run_holdout.py`
- frozen `EPISODE_SIZE`: `128`
- inherited local-window width: `10.0` degrees

Both #839 candidate jobs completed all source/runtime/model restoration and began label-free SonotaCo candidate generation before stopping at the frozen episode-size requirement. No #839 candidate primary output was produced.

## Comparator-side engineering status

Comparator execution issues are separate from the decisive #839 applicability failure:

- Sugar 2013 and Sugar 2014 both successfully produced and froze truth-free comparator primary outputs in r4.
- r4 catalogue HDBSCAN reached its exact frozen `fit_predict` call but hit the scikit-learn keyword rename (`ensure_all_finite` versus `force_all_finite`). This is an execution-compatibility issue, not a clustering result.
- PR `#903` adds only a fail-closed argument-name compatibility shim while preserving exact scikit-learn 1.4.2, HDBSCAN 0.8.44, inputs, and clustering settings; both SonotaCo source audits passed and PR #903 was merged at `4aacd75cd990c9ca87ba2f50687b5971a4401719`.

Completing comparator plumbing cannot rescue the final comparison because the frozen #839 side cannot emit a primary catalogue on either preregistered pairwise universe.

## Truth and firewall state

- final pretruth all-output freeze completed: **false**
- post-output known-shower truth opened: **false**
- frozen #854 evaluator executed on SonotaCo: **false**
- OrbitTrace target information accessed: **false**
- OrbitTrace target region opened: **false**
- MAARSY scientific data accessed: **false**

The workflow's `freeze` and `truth_and_evaluate` jobs were skipped. It therefore produced no matched-performance verdict and no basis for claiming that #839 beat or lost to either comparator.

## Scientific interpretation

The external test has established a specific architectural incompatibility: frozen #839 assumes enough local event density to construct a 128-event episode for every hard family/year, but the preregistered SonotaCo pairwise universes violate that prerequisite.

Because this incompatibility was learned from the authorized external SonotaCo run, the existing #839 methodology must remain frozen. It is scientifically invalid to lower the episode size, widen the local window, skip insufficient families, alter pairwise filtering, or otherwise revise #839 and then reuse SonotaCo 2013/2014 as if it were still an untouched final test.

Any successor addressing sparse external panels must be treated as a new method, developed without SonotaCo-derived outcome tuning on target-excluded development data, and eventually evaluated on a different untouched external dataset. SonotaCo 2013/2014 is no longer pristine for development of such a successor.

## Status of the final literature claim

The strongest defensible conclusion from this final test is:

> Frozen #839 was not evaluable in the preregistered matched SonotaCo 2013/2014 comparison because its fixed 128-event local-episode requirement failed on both comparator-specific pairwise universes before truth access. Therefore no claim of superiority, inferiority, or non-inferiority to Sugar or catalogue HDBSCAN is supported by this test.
