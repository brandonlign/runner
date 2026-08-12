# OrbitTrace GMN cross-generator consensus spacing v1 — binding result

## Verdict

`FAIL_GMN_CROSSGENERATOR_CONSENSUS_SPACING_V1`

This is a clean scientific failure of the sole preregistered direct-edge first-pass spacing/backfill successor. It is not a technical failure and it does not invalidate the preceding cross-generator graph diagnostic PASS.

## Frozen provenance

- pre-outcome protocol freeze commit: `8080c8a1b7ad377e3127b3acac22ab078e352256`
- frozen implementation commit: `be227c38bdf85d93ecaea96d000f846fdb948e74`
- execution-plumbing commit: `989fe741a7c88b0fc38492807fcd4f37e5d52de4`
- first technically valid binding run: `31614302577`
- binding artifact: `orbittrace-gmn-crossgenerator-consensus-spacing-v1`
- artifact ID: `9148642691`
- artifact digest: `sha256:f2a5b692dc3bac93cd8fd6bbb17b39fac20026c54cd2413a55bf11195c6f77b6`

The exact #1194 source, OOF order, 4,504-family universe, P19/P20 inputs, #839 ranker source, frozen graph and protected-data firewall all reproduced before interpretation.

## Immutable graph used

- edge count: **698**
- graph file SHA-256: `1d7ccb41800b222df053e1f8240ceb2c21020ae160e0c6e6b33eda0b546b03ac`
- canonical edge SHA-256: `319d1a868d68148221caba82e28ca17b9a7f55b0f1f7b0f1c02a8fc9e5c28bb0`
- no graph threshold or relation was changed;
- no connected-component closure or graph score was used.

## Exact parent reproduction

The #1194 representative-share parent reproduced exactly:

- recovered@25: **22**
- recovered@50: **43**
- recovered@100: **80**
- recovered@500: **171**
- top-100 dominant precision: **0.8075287489258385**
- MRR: **0.02016666446026534**
- qualified matches: **256**
- parent order SHA-256: `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`

## Sole successor outcome

Direct-edge spacing accepted **4,040** families on the first pass and deferred **464** families, then appended every deferred family in exact parent relative order. No family was deleted and no membership changed.

Successor metrics:

- recovered@25: **22**
- recovered@50: **43**
- recovered@100: **80**
- recovered@500: **171**
- top-100 dominant precision: **0.8075287489258385**
- MRR: **0.020166855231029714**
- qualified matches: **256**
- successor order SHA-256: `507ed212ae005e400e142465bfeeda68b51a515909ee52147e83bb7ee998167d`

Gate results:

- recovered@100 > 80: **FAIL**
- recovered@50 >= 43: PASS
- recovered@25 >= 22: PASS
- recovered@500 >= 171: PASS
- top-100 precision >= parent: PASS
- MRR >= parent: PASS
- qualified matches == 256: PASS

The successor changed the global order substantially enough to defer 464 directly conflicting families, but it did not change any preregistered recovery-budget metric or top-100 precision. The only movement was a very small MRR increase (`+1.90770764374e-7` approximately), which is insufficient under the frozen gate.

## Scientific interpretation

The preceding diagnostic established that the frozen P19↔P20 shared-event + centroid relation is a high-purity redundancy signal. This experiment shows that **hard ordering-level removal of one side of those direct conflicts from the first pass is not the missing mechanism for #1194's early catalogue recovery**. The directly linked duplicate families are not occupying enough decisive early #1194 slots for spacing alone to improve @25/@50/@100/@500 recovery.

Therefore the exact direct-edge first-pass spacing/backfill lane is closed. Do not rescue this result with graph radius/overlap changes, connected-component closure, degree/component scoring, alternate representatives, top-k-only suppression, source quotas, score bonuses/penalties, fusion weights, membership merging, candidate deletion, alternate backfill positions, alternate parent rankers, or post-result graph searches.

The graph diagnostic PASS itself remains valid as a mechanism characterization; this FAIL only rejects the preregistered downstream spacing rule.

## Protected-data firewall

Throughout the binding run:

- protected solar-longitude exclusion remained `[20.0, 55.0]`;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no post-result second search was performed.
