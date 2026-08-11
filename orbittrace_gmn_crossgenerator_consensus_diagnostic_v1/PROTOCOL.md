# OrbitTrace GMN cross-generator consensus diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 mechanism diagnostic only**. It defines no successor order, suppression rule, merged membership, or external/SonotaCo evaluation.

The motivation predates the current diagnostic outcome:

- #838 established that the fixed 4,504-family P19+P20 union covers 256 eligible GMN showers and that a truth-aware one-representative-per-label ceiling reaches recovery@100 = 100, while exact event-set duplicate families are absent; the remaining redundancy is geometric/physical fragmentation.
- #839 explicitly identified the next architectural problem as **consensus consolidation plus a single final membership layer**.
- #977 subsequently established the current clean GMN ranking parent: 21D source-blind purity + exact #839 diversity, with recovery@100 = 82, recovery@50 = 47, recovery@25 = 24 and top-100 dominant precision = 0.8558407874228419.

This diagnostic asks one narrower question before any consolidation architecture is allowed: **do independently generated P19 and P20 fragments form a high-purity, label-free consensus relation that captures a material share of duplicate recoverable GMN shower labels?**

## Immutable development universe

Use only frozen target-excluded GMN 2022/2023 development inputs:

- hard families: 226
- P19 soft families: 1,075
- P20 soft families: 3,203
- union: 4,504 unique family IDs
- P19 prelabel SHA-256: `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`
- P20 prelabel SHA-256: `8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734`
- exact #839 ranker source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`
- protected solar-longitude exclusion: `[20.0, 55.0]`

No SonotaCo catalogue, SonotaCo feature payload, MAARSY, DMS, OrbitTrace target information, or target-region event may enter this diagnostic.

## Pretruth consensus graph

The graph MUST be completely frozen from the P19/P20 **prelabel** payloads before GMN shower labels are loaded or attached.

Only cross-generator soft-family pairs are eligible: one endpoint from P19 and one from P20. Hard-hard, hard-soft, P19-P19 and P20-P20 edges are excluded from this diagnostic.

An undirected P19-P20 edge exists iff BOTH frozen conditions hold:

1. the two family memberships share at least one exact GMN event ID; and
2. their exact #839 two-year centroid distance is `<= 1.0`.

The #839 distance is inherited unchanged. For each year 2022 and 2023, with circular longitude deltas:

- solar-longitude term: `delta(sol) / 10`
- sun-longitude term: `delta(sun_lon) / 4`
- ecliptic-latitude term: `abs(delta(ecl_lat)) / 4`
- geocentric-speed term: `abs(delta(log(|vg|))) / log(1.10)`

The annual distance is the Euclidean norm of those four terms and the two-year family distance is the maximum of the 2022 and 2023 annual distances.

The threshold `1.0` is inherited from #839's already-selected diversity scale. It is not searched or fitted here.

The pretruth graph artifact records only family IDs, source identities, shared-event count, and frozen centroid distance. It records no label, F1, positive/negative status, first-rank statistic, or candidate order.

## Sole post-freeze diagnostic

Only after the complete graph artifact and its SHA-256 are frozen may the existing target-excluded GMN development labels be attached using the exact #839 truth/eligibility machinery.

A family is `qualified` exactly when the frozen GMN development evaluator marks its fixed membership positive. Its `best_label` is the evaluator's fixed dominant eligible shower label.

Compute exactly these quantities:

1. `qualified_edge_count`: graph edges whose two endpoints are both qualified.
2. `same_label_qualified_edge_count`: qualified graph edges whose two endpoints have the same `best_label`.
3. `qualified_edge_same_label_precision = same_label_qualified_edge_count / qualified_edge_count`.
4. `crossgenerator_duplicate_label_count`: eligible labels having at least one qualified P19 family AND at least one qualified P20 family in the fixed union.
5. `captured_crossgenerator_duplicate_label_count`: such labels for which at least one frozen graph edge joins a qualified P19 and qualified P20 family carrying that same label.
6. `crossgenerator_duplicate_label_capture = captured / crossgenerator_duplicate_label_count`.
7. `all_duplicate_label_count`: eligible labels having at least two qualified union families from any source.
8. `captured_all_duplicate_label_count`: all-duplicate labels captured by at least one same-label frozen graph edge.
9. `all_duplicate_label_capture = captured_all_duplicate_label_count / all_duplicate_label_count`.

No top-k subset, ranking, suppression simulation, component construction, threshold sweep, source quota, or alternative graph is evaluated.

## Preregistered PASS gate

PASS iff ALL hold:

- `qualified_edge_count >= 20`;
- `qualified_edge_same_label_precision >= 0.95`;
- `crossgenerator_duplicate_label_count >= 20`;
- `crossgenerator_duplicate_label_capture >= 0.50`;
- `all_duplicate_label_capture >= 0.25`.

Otherwise FAIL.

These gates are frozen before the first truth-aware diagnostic outcome. They are intended to require both very low false-merge risk and material consolidation headroom before any membership-merging successor is authorized.

## Consequence

A PASS authorizes only a **separately frozen target-excluded GMN consolidation successor** based on this exact graph relation. It does not choose how to merge memberships, choose a representative, aggregate scores, or alter #977 ranking; those would require a new protocol frozen before outcome.

A FAIL permanently closes this exact cross-generator shared-event + #839-distance consensus relation as the general consolidation mechanism. Do not rescue it with a different distance threshold, Jaccard/shared-event-count cutoff, P19-P19/P20-P20 edges, source-specific thresholds, top-k conditioning, label-conditioned edges, or post-result graph search.

## Firewall

- `sonotaco_2013_2014_access = false`
- `sonotaco_feature_access = false`
- `target_information_access = false`
- `target_region_events_accessed = false`
- `maarsy_scientific_access = false`
- `dms_scientific_access = false`
- `blind_exclusion = [20.0, 55.0]`

Labels may enter only after the complete label-free consensus graph is frozen.