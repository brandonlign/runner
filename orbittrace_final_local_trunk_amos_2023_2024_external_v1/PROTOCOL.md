# OrbitTrace recurrent local-TopoModal-trunk v1 — conditional AMOS 2023/2024 final external protocol

## Status and activation

**FROZEN BEFORE the first technically valid GMN truth outcome of recurrent local TopoModal trunk v1 and before any AMOS 2023/2024 event-level scientific access.**

This protocol is dormant unless the exact already-frozen GMN experiment returns:

`PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`

under all 16 frozen gates, with no scientific repair or post-result method change. If that experiment returns a valid FAIL, this conditional endpoint is permanently closed without AMOS execution and the local-trunk method is not promoted by this protocol.

If activated, this protocol supersedes the still-unexecuted density-synchronous-only AMOS endpoint from PR #1268 as the sole AMOS scientific endpoint. The two endpoints must never be executed sequentially. No AMOS request is sent and no AMOS scientific row is opened by this freeze.

The matched-capacity literature adjudication is a separate claim test and is **not** an activation condition for this external endpoint. That prevents literature outcomes from becoming a hidden method-selection oracle.

## 1. Immutable selected method if activated

The final method is exactly the composition already frozen on GMN:

1. fit the exact density-synchronous recurrent-EOM parent on the complete retained two-year catalogue;
2. preserve its complete candidate slot count and slot order exactly;
3. independently inside each parent candidate, apply the exact fixed physical local TopoModal trunk rule;
4. replace that slot membership only with the largest recurrently reportable strict anchor-chain subset, otherwise retain the parent membership unchanged;
5. never add an event, move an event between slots, create an extra slot, or rerank a slot.

### Parent ranking/hierarchy

Use exact density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, transferred mechanically from years 2022/2023 to AMOS 2023/2024:

- pooled two-year GEO6 hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM extraction;
- exact recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- exact density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- density-synchronous quality `S_sync(C)=integral min(A_2023^C(lambda), A_2024^C(lambda)) d lambda`;
- rank by descending density-synchronous quality, descending ordinary stability, descending member count, ascending deterministic family ID.

### Local TopoModal membership rule

Transfer exactly the frozen GMN protocol blob `de8d040a1f9d3b0825ce56532efd5950acefc689` and canonical scientific constructor blob `cd3fb15263fd4b2e38e4b413ece9b347b64816d5`. The validated exact full-row transport is an engineering implementation of that same rule and may not remove or alter a radius edge.

For each parent independently:

- physical half-scales: solar longitude `5 deg`, radiant `4 deg`, speed `10%`;
- exact normalized 6-D embedding from the frozen local-trunk protocol;
- exact symmetric Euclidean radius graph at `r=1.0`, self included;
- local density `rho_i=|N_i|/n_parent`;
- GUDHI ToMATo manual graph/manual density, no flat cluster count and no persistence threshold;
- anchor = highest local density event, event-ID ascending tie break;
- follow the anchor leaf to its connected-component root through the complete hierarchy;
- recurrently reportable strict subset requires at least 4 events from AMOS 2023 and at least 4 from AMOS 2024;
- choose the largest such strict anchor-chain membership;
- if none exists, retain the exact parent membership.

The year labels change only from GMN `2022/2023` to AMOS `2023/2024`. Radius, physical scales, annual support floor, anchor rule, hierarchy rule, fallback rule, and rank preservation do not change.

## 2. Permanent external panel

Exactly AMOS calendar years 2023 and 2024 are allowed. The complete solved multi-station population is required, including sporadics.

No alternate year, selected subset, quality-picked sample, replacement survey, or second external chance is allowed after a technically valid AMOS outcome.

## 3. Protected receipt firewall

Reuse the already-audited staged AMOS receipt contract from the density-synchronous endpoint without modification.

### Stage 1 — blind index only

Exactly:

`event_id, utc_time, solar_longitude_deg`

Remove inclusively every event with `20.0 <= solar_longitude_deg <= 55.0` before any retained geometry or label field may be opened.

### Stage 2 — retained geometry only

For retained IDs only:

`event_id, ra_j2000_deg, dec_j2000_deg, vg_km_s`

Use the exact audited AMOS J2000-to-canonical adapter identities from PR #1268. No survey-specific alignment, velocity correction, quality cut, scale fit, or calibration is allowed.

### Stage 3 — labels only after complete pretruth freeze

For retained IDs only:

`event_id, shower_association`

Exact uppercase `SPORADIC` remains the sole no-association sentinel. Labels remain inaccessible until every candidate catalogue listed below is serialized and hash-frozen.

## 4. Candidate catalogues frozen before truth

Fit exactly one pooled HDBSCAN hierarchy to the retained AMOS 2023+2024 GEO6 rows and freeze four complete outputs before labels:

1. **ordinary HDBSCAN EOM** — primary literature/standard baseline;
2. **recurrent-EOM** — historical recurrence comparator;
3. **density-synchronous recurrent-EOM** — immediate parent comparator;
4. **recurrent local TopoModal trunk v1** — sole selected final method if this protocol activates.

The fourth catalogue has exactly the density-synchronous parent's slot count and slot order. Each final membership must be a subset of its same-rank density-synchronous parent and all final slots remain event-disjoint.

Before truth, serialize and hash-freeze at minimum:

- retained IDs/counts by year;
- canonical geometry and GEO6 hashes;
- shared condensed-tree hash;
- ordinary stability map;
- recurrent and density-synchronous annual/scalar quality maps;
- all three parent selected-node/order outputs;
- complete local-trunk topology summary for every final-method parent;
- anchor, anchor chain, annual support counts, replacement/fallback decision, and final membership for every slot;
- complete final-method ordered-membership hash;
- changed-slot count/mechanism-active flag;
- exact source/blob/runtime identities;
- declarations of zero shower-truth and zero protected-target access.

No final-method membership may be constructed or recomputed after labels become visible except byte-for-byte verification of the frozen pretruth.

## 5. External truth semantics

After the complete pretruth freeze, open only retained-ID shower associations.

For each AMOS year independently:

- eligible known shower: at least 4 retained labeled events;
- candidate qualifies only with overlap >=4 and precision >=0.5;
- each eligible shower contributes its first qualifying rank;
- report full-catalogue recovered/qualified showers;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- reciprocal-rank mass and zero-filled eligible-query MRR;
- historical conditional MRR for continuity only;
- median top-500 fragmentation.

Zero-filled eligible-query MRR is the primary retrieval statistic for the local-trunk increment, matching its frozen GMN gate.

## 6. Primary AMOS external-generalization gate

The selected local-trunk method passes primary external validation only if all conditions below hold.

### Versus ordinary HDBSCAN, each year separately

For both 2023 and 2024:

1. full-catalogue recovered/qualified showers are not lower;
2. recovered@50 is not lower;
3. recovered@100 is not lower;
4. top-100 dominant precision is not lower;
5. zero-filled MRR is not lower;
6. median top-500 fragmentation is not higher.

Across the two years:

7. recovered@100 is strictly higher than ordinary HDBSCAN in at least one year;
8. final-method catalogue differs from ordinary HDBSCAN, proving the method is active.

### Versus density-synchronous immediate parent, each year separately

For both 2023 and 2024:

9. full-catalogue recovered/qualified showers are not lower;
10. recovered@50 is not lower;
11. recovered@100 is not lower;
12. top-100 dominant precision is not lower;
13. zero-filled MRR is not lower;
14. median top-500 fragmentation is not higher.

A strict local-trunk improvement over the density-synchronous parent is **not required for the primary external-generalization PASS**. This avoids making a small incremental membership effect a prerequisite for demonstrating that the final fixed method generalizes as a detector.

Primary token:

`PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

Otherwise:

`FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

A technically valid FAIL means pristine cross-survey generalization is not established. No AMOS rerun, method switch, gate relaxation, or replacement external survey is authorized.

## 7. Separately predeclared local-trunk incremental result

Report whether the membership-cleaning mechanism itself transfers beyond GMN.

Incremental PASS requires:

- every no-regression condition 9–14 above;
- final local-trunk membership differs from the density-synchronous parent for at least one slot; and
- zero-filled MRR is strictly greater than the density-synchronous parent in at least one AMOS year.

Token:

`PASS_LOCAL_TOPOMODAL_TRUNK_INCREMENT_AMOS`

otherwise:

`NO_DEMONSTRATED_LOCAL_TOPOMODAL_TRUNK_INCREMENT_AMOS`

The second token does not by itself negate primary external validation; it narrows the claim to the incremental membership mechanism.

## 8. Relationship to matched-capacity literature testing

The separately frozen GMN matched-capacity local-trunk literature audit may establish superiority to the tested Sugar-core and catalogue-HDBSCAN implementations on development data. It does not substitute for AMOS.

If the optional AMOS comparator fields from the already-frozen PR #1248 supplement are present in the **same initial provider transfer**, the single AMOS receipt may also run a separately frozen matched-capacity literature supplement. Missing optional fields cannot trigger a second request after primary outcomes are known.

## 9. Technical no-result boundary

A run is technical no-result, not a scientific outcome, if any source pin, runtime pin, receipt schema, protected-region exclusion, shared-hierarchy identity, candidate-order identity, local-trunk exact-rule invariant, pretruth hash seal, or label-ordering firewall fails before a valid result is produced.

Engineering-only repairs are allowed only when they provably preserve the frozen scientific bytes/rules and are frozen before retry.

## 10. Permanent no-rescue rule

After the first technically valid AMOS endpoint, do not change or search:

- method selection;
- HDBSCAN parameters;
- recurrent/density-synchronous formulas;
- local TopoModal radius, physical scales, density, support floor, anchor, hierarchy or fallback rule;
- slot rank/order;
- coordinate transform;
- quality filters;
- truth thresholds;
- evaluator metrics/gates;
- year/sample/survey selection;
- comparator implementation;
- fusion or reranking;
- external dataset.

## 11. Authorization boundary

This protocol authorizes **only pre-data implementation, source freezing, and zero-data audits**.

It does not authorize:

- sending the AMOS provider request;
- opening AMOS event-level rows;
- opening AMOS shower associations;
- accessing the protected OrbitTrace region;
- executing a scientific AMOS endpoint.

Those remain separately owner-authorized and require a compliant provider transfer plus a final zero-data execution freeze.
