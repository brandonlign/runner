# OrbitTrace final GMN method — M0 / URC v1

## Scientific decision

GMN 2022/2023 methodology development is complete. The final method selected under the pre-result stopping and membership-promotion rules is **M0**, the original-membership URC architecture from PR #839.

No further GMN candidate generator, ranking feature/model, membership rule, threshold, score combination, or postprocessing family may be introduced for the final literature claim.

## Final scientific architecture

### Candidate generation

The primary catalogue is the exact union of three already-frozen recurrent, target-free proposal classes:

1. hard v8 pooled-year-centroid recurrent families;
2. P19 subthreshold reciprocal-recurrence soft families;
3. P20 recurrent isolated-quartet soft families.

On the reference target-excluded GMN 2022/2023 development corpus this union contains **4,504** candidates: 226 hard + 1,075 P19 + 3,203 P20.

P21 and all later proposal expansions are excluded permanently. P21 failed scientifically and then failed the preregistered unique-coverage stopping rule.

### Primary membership

Every family uses its **original generator membership** exactly as emitted by hard-v8, P19, or P20. No P12 halo, M1 fragment union, M2 event-level P12 filter, core/halo switch, or later membership expansion is part of the final output.

### Ranking model

The final continuous quality ranker is the exact PR #839 strict same-shower grouped ExtraTrees quality-regression architecture:

- estimator: `ExtraTreesRegressor`;
- trees: 600;
- max depth: 4;
- min samples leaf: 5;
- max features: all;
- random state: 20260809;
- development weighting: group-balanced by known-shower group;
- feature vector: exact 34-field structural/cohesion/source/neighbor vector frozen by #839;
- final unseen-data model: fit once on all 4,504 allowed GMN development candidates after architecture selection;
- serialized full-GMN model SHA-256: `ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909`;
- full-GMN feature-matrix SHA-256: `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`;
- canonical deterministic single-thread prediction is used for deployment.

### Diversity ordering

Final catalogue order applies the exact frozen #839 diversity rule to model predictions:

- diversity lambda = **0.8**;
- diversity scale = **1.0**;
- stable frozen tie semantics from the #839 ranker source.

No final-test label, comparator output, candidate budget, external result, or target information may change model scores or ordering.

## Development evidence for M0

Reference target-excluded GMN 2022/2023 endpoints from #839:

- recovery@25 = **22**;
- recovery@50 = **40**;
- recovery@100 = **75**;
- recovery@500 = **159**;
- qualified known streams = **256**;
- MRR = **0.019037817654898162**;
- top-100 dominant precision = **0.7645689180574315**;
- best-membership macro F1 over all eligible known streams = **0.17953659309876194**.

The ranking passed both preregistered robustness tracks in #842:

- five new whole-shower grouped-CV partitions retained r100 73–77 and all 256 qualified streams;
- deterministic 10%/20% event-thinning regeneration passed every fixed proposal-coverage gate.

## Membership-challenger adjudication

### M1 / #845 — rejected

Fixed-rank fragment membership merging failed its scientific gate. The best diagnostic rule raised r100 75→76 but macro membership F1 only 0.179537→0.183682 and required 226,998 added memberships with extreme family inflation. No adjacent-radius robust rule passed.

### M2 / #846 + #850 — rejected

The corrected strict all-fragment #846 feasibility run selected one fixed event-level P12 policy (`ET_d4_l10`, threshold 0.4, no cap) and passed development feasibility. Its independently frozen five-partition fixed-policy stress then failed because panel `URC-EVENT-STRESS-E` produced **94** corrected qualified streams versus the preregistered minimum **95**. Four other panels passed. The #850 rule required all five, so M2 is a permanent scientific no-go. No #852 integration is authorized.

Therefore the pre-result #848 selector resolves deterministically to M0.

## Frozen source/provenance anchors

- #839 active ranker decoded scientific source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.
- #839 selected development order SHA-256: `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`.
- full-GMN ranker model SHA-256: `ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909`.
- portable unseen-data ranker application is the merged #860 implementation, required to reproduce the frozen GMN feature semantics and deterministic serialized-model ordering.
- pair-portable candidate generation must pass its separate exact GMN structural-equivalence audit before final-test authorization.

## Final-test output contract

For each frozen pairwise SonotaCo common-row universe, M0 must emit exactly one primary catalogue before truth is opened:

- stable family ID;
- source class (`hard`, `p19`, or `p20`);
- exact primary member-ID set;
- fixed model quality score;
- final primary rank after frozen diversity ordering.

No secondary halo or alternative member representation exists for M0.

## Development stop

From this freeze onward, GMN 2022/2023 may be used only for source-equivalence, deterministic replay, transport testing, and provenance checks that do not select or modify scientific behavior. Such work is not new scientific development.

## Fixed progression

1. Complete source-equivalent final transport and declare this exact M0 executable `FINAL_FOR_LITERATURE_TEST`.
2. Execute the one final SonotaCo **2013 + 2014** matched literature test against frozen Sugar and catalogue HDBSCAN.
3. Only a final literature PASS may authorize frozen no-retuning **MAARSY 2020 + 2021** validation.
4. Only the required MAARSY PASS may authorize the final blind target-containing search.

OrbitTrace information and solar longitude **20°–55°** remain sealed throughout steps 1–3.
