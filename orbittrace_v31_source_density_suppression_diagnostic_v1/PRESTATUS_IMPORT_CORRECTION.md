# Pre-status import-plumbing correction

Workflow run `31506537600` successfully verified the corrected immutable #950 source counts (`hard=19`, `p19=53`, `p20=157`), loaded the immutable exposed v31 training truth, reproduced exact v31, and reproduced the already-frozen pre-status 229-family v31 rank vector. It then stopped before the source-density vector was created because `pretruth_count_repair.py` used a package-style Python import that is not valid when the wrapper is executed directly by file path.

Authoritative #1046 surfaced/missed status had **not** been restored, no source-density family vector existed, and no diagnostic median or PASS/FAIL statistic had been computed. Therefore run `31506537600` is an engineering execution failure, not a scientific result.

`pretruth_count_repair_v2.py` changes only module loading: it loads the already-frozen `diagnose.py` by exact sibling file path using `importlib.util`, then applies the same immutable pretruth source-count correction `{'hard':19,'p19':53,'p20':157}` and calls the unchanged `main()`.

No source-density formula, family/source identity, #1046 representative, status attachment order, median comparison, PASS gate, ranking, literature evaluation, successor, or protected-data rule changes.
