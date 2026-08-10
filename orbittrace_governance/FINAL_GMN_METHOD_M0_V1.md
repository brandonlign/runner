# OrbitTrace final GMN method — M0 / URC v1

## Final scientific selection

GMN 2022/2023 methodology development is complete. Under the pre-result final selector in PR #848, the final method is **M0**, the original-membership URC architecture from PR #839.

No further GMN candidate generator, ranking feature/model, membership architecture, threshold family, or score combination is admissible for the final literature claim. GMN may now be used only for source-equivalence, deterministic replay, and transport verification.

## Frozen method

### Candidate universe

The primary catalogue is the exact union of:

1. hard v8 pooled-year-centroid recurrent families;
2. P19 subthreshold reciprocal-recurrence soft families;
3. P20 recurrent isolated-quartet soft families.

On the reference target-excluded GMN development panel this is 226 + 1,075 + 3,203 = **4,504** candidate families. P21 and all later proposal expansions are excluded permanently.

### Membership

Each family uses exactly its original generator membership. No P12 halo, core/halo switch, fragment union, event-level P12 filter, or post-ranking membership expansion is part of M0.

### Ranking

The final ranker is the exact #839 strict same-shower grouped ExtraTrees quality architecture:

- 600 trees;
- max depth 4;
- min samples leaf 5;
- all features;
- random state 20260809;
- group-balanced development weighting;
- exact 34-field structural/cohesion/source/neighbor feature vector;
- diversity lambda **0.8**, scale **1.0**.

The deployment model was fit once on all allowed GMN development candidates after architecture selection.

Frozen identities:

- #839 decoded scientific source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- #839 selected development order SHA-256: `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`;
- full-GMN feature-matrix SHA-256: `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`;
- serialized full-GMN model SHA-256: `ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909`.

The merged #860 unseen-data ranker is the authoritative portable ranking implementation and uses deterministic single-thread inference plus the same diversity ordering.

## Development evidence

Reference M0 endpoints on target-excluded GMN 2022/2023:

- recovery@25 **22**;
- recovery@50 **40**;
- recovery@100 **75**;
- recovery@500 **159**;
- qualified known streams **256**;
- MRR **0.019037817654898162**;
- top-100 dominant precision **0.7645689180574315**;
- membership macro F1 **0.17953659309876194**.

#842 independently passed both preregistered robustness tracks: five new whole-shower grouped ranking partitions and deterministic 10%/20% event-thinning candidate regeneration.

## Membership adjudication

- **M1 / #845:** scientific FAIL. Best fragment merge changed macro F1 only 0.179537→0.183682 and required extreme membership inflation; no robust adjacent-radius rule passed.
- **M2 / #846 + #850:** corrected #846 feasibility PASS selected exactly `ET_d4_l10`, threshold 0.4, no cap. The independently frozen five-partition fixed-policy #850 stress then scientifically FAILED because panel `URC-EVENT-STRESS-E` retained **94** corrected qualified streams versus the preregistered minimum **95**. Four other panels passed, but #850 required all five. No #852 integration is authorized.

Therefore #848 resolves deterministically to M0. Neither M1 nor M2 may be rescued, retuned, or reselected from these outcomes.

## Final output contract

For each final pairwise SonotaCo common-row universe, M0 emits exactly one pre-truth primary catalogue containing for every family:

- stable family ID;
- source class (`hard`, `p19`, `p20`);
- exact original primary member-ID set;
- frozen model quality score;
- final rank after the frozen diversity rule.

No secondary member representation exists for the final claim.

## Fixed progression

1. Complete source-equivalent pair-portable generation/ranking and freeze one integrated M0 executable as `FINAL_FOR_LITERATURE_TEST`.
2. Run the one final matched **SonotaCo 2013 + 2014** test against frozen Sugar and catalogue HDBSCAN.
3. Only a literature PASS may activate frozen no-retuning **MAARSY 2020 + 2021** validation.
4. Only the required MAARSY PASS may authorize the final blind target-containing OrbitTrace search.

OrbitTrace information and solar longitude **20°–55°** remain sealed throughout steps 1–3.
