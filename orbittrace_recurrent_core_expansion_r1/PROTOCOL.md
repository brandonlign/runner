# OrbitTrace recurrent-core expansion R1 — frozen development protocol

## Status and purpose

R1 is a **new, separately isolated research program**, not a v8 successor, v8 retune, or modification of the frozen v8 blind-discovery protocol.

The already-exposed v8 development and literature evidence identifies one broad unresolved architectural problem: recurrent fixed4/v8 families often behave as high-purity but incomplete seeds, and the matched literature gap grows strongly with shower size. R1 therefore changes only **final member assignment**. It does not change seed generation, components, cross-year family topology, v8 pooled centroids, multiplicity scoring, or v8 ranking.

The exposed SonotaCo 2023/2025 Sugar/HDBSCAN outcomes may justify investigating final membership, but they may not choose any R1 threshold, radius, weight, scale, endpoint, or variant.

## Immutable seed architecture

R1 must reproduce the exact promoted v8 development architecture on target-excluded GMN 2022/2023:

- exact v8 parent commit `c9d6c44704013ba0c9430100e98a29a56b453304`;
- exact 226 recurrent families;
- exact v8 family IDs, component IDs, seed event IDs, pooled year centroids, multiplicity scores, and multiplicity order;
- exact v8 baseline: 95 qualified known showers, recovery@100 = 58, top-100 dominant precision = 0.6884631112636006, MRR = 0.045531138942766655;
- no seed event may be removed or reassigned;
- newly added members may never become seeds and may not alter ranking.

## Pre-scientific physical-input audit

Schema-only workflow `31233525610`, artifact `9014633429`, digest `sha256:c748ead99c08f69a80f1c2a5202c9d4fe08579dba0a961f078fcc389b9058113`, passed without parsing an event row or shower-label value. The exact GMN monthly schema exposes `q`, `e`, `i`, `peri`, and `node`, so the already-frozen Southworth–Hawkins orbital dissimilarity implementation can be used without inventing a new physical metric.

The exact comparator source is `orbittrace_literature_comparison/literature_comparators.py`, SHA-256 `ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2`, with the pre-existing `D_SH = 0.05` criterion.

## One and only R1 membership rule

For each frozen v8 within-year seed component `C_y`:

1. Consider only components from the **other development year** that are in the same frozen v8 family and are **directly linked** to `C_y` under the inherited centroid-distance rule `D <= 1.5`.
2. For every directly linked opposite-year component with at least four valid orbital records, compute the exact pairwise Southworth–Hawkins matrix among its original seed events and select the **actual seed event with minimum median D_SH** as that component's orbital medoid; deterministic event-ID tie break.
3. A non-seed event from year `y` may be proposed for `C_y` only if:
   - its exact frozen geometry distance to `C_y`'s centroid is `<= 1.5`; and
   - its `D_SH` to at least one eligible directly linked opposite-year orbital medoid is `<= 0.05`.
4. The event's best physical proposal is the smallest `D_SH`, with deterministic partner-component / medoid-ID tie breaks.
5. Original seed events have absolute priority and can never be reassigned.
6. If a non-seed event is proposed to multiple frozen families, assign it exactly once by lexicographic order:
   - smaller `D_SH`;
   - smaller exact geometry distance;
   - better already-frozen v8 multiplicity rank;
   - stable family ID;
   - stable component ID.
7. Added events do **not** seed another growth step. There is no transitive expansion.
8. The final R1 family membership is the frozen v8 seed union plus resolved added events. The exact v8 ranking is unchanged.

There is no alternative medoid definition, D_SH threshold, geometry radius, weighting rule, iterative growth rule, conflict rule, or candidate variant.

## Blindness and parser order

- Development years: GMN 2022 and 2023 only.
- Solar longitude 20°–55° remains inaccessible to R1.
- The frozen v8 parser removes 20°–55° before label normalization.
- The R1 raw orbital parser interprets only stable event ID and solar longitude before the blind cut; `q/e/i/peri/node` are converted only after the event is outside 20°–55° and is confirmed to belong to the exact target-excluded v8 scan-ID universe.
- The R1 orbital parser never reads a shower-label token.
- No OrbitTrace coordinate, member, identity, prior target family/rank, target-region event, Stage A output, or Stage B output may enter development.
- Expansion membership and conflict resolution must be immutable before shower-label evaluation.

## Frozen development gates

R1 passes only if every integrity gate and every scientific gate passes.

Integrity:

1. exact v8 226-family universe and exact v8 multiplicity order reproduced;
2. exact v8 baseline metrics reproduced;
3. no frozen seed event removed or reassigned;
4. newly added events never seed growth;
5. orbital values decoded only after the blind exclusion and exact-v8 scan-ID gate;
6. orbital parser accesses zero shower-label values;
7. exact pre-existing `D_SH <= 0.05` rule and exact inherited geometry `D <= 1.5` rule;
8. no parameter, radius, weight, threshold, or variant search.

Scientific:

1. R1 macro F1 across qualified known showers must improve by **at least +0.05 absolute** over exact frozen-v8 seed membership;
2. qualified known-shower matches must be **>= 95**;
3. recovery@100 under the unchanged v8 ranking must be **>= 58**;
4. top-100 dominant precision must be **>= 0.65**;
5. on the fixed subset of showers that were already qualified by frozen v8 and contain at least 100 target-excluded 2022/2023 events, R1 mean recall must be **>= 1.5x** the frozen-v8 mean recall;
6. that same fixed large-shower subset must retain mean precision **>= 0.80**;
7. expansion must add at least one non-seed event.

Failure is `FAIL_RECURRENT_CORE_EXPANSION_R1_NO_GO` and permanently rejects this exact rule. Development failure does not authorize changing a threshold or trying a nearby variant on the same evidence.

## Validation and claim boundary

A development pass does **not** establish superiority over Sugar/HDBSCAN and does not alter promoted v8. It authorizes only a separately frozen one-shot validation on a scientifically fresh panel. CAMSv3 2017/2018 is currently reserved for that role because repository-history and structure-only audits have not opened its scientific event values; freshness must be reverified immediately before any R1 validation.

Only after an independent validation pass could R1 receive a separately preregistered matched literature comparison. No OrbitTrace target-containing scan or reveal is authorized by an R1 development pass.