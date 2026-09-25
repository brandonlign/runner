# OrbitTrace final SonotaCo 2013/2014 execution freeze — v1

## Purpose

This is the candidate-specific **pre-access execution contract** for the one-shot final matched literature test. It is frozen after GMN method selection closed on M0/#839 and before any SonotaCo 2013/2014 scientific value, known-shower truth value, comparator output, or final-candidate performance value is opened.

This contract does not itself download or inspect SonotaCo. Its sole purpose is to make final-test authorization mechanical and fail-closed.

## Selected candidate

The only candidate eligible for the final literature test is the final GMN-developed **M0 / PR #839 URC union ranking**:

- candidate universe semantics: hard-v8 + P19-soft + P20-soft;
- GMN development union count: 4,504 = 226 + 1,075 + 3,203;
- membership: original frozen M0 family memberships;
- ranking: frozen #839 strict-group ExtraTrees quality regression plus diversity;
- diversity lambda 0.8, diversity scale 1.0;
- development selected order SHA-256 `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`.

M1 and M2 are ineligible. M2's initial calibration improvement does not override its preregistered repeated-group stress failure.

## Required generator identity

The exact P19 source can reproduce all discrete family semantics while derived floating distances differ at machine-roundoff scale across otherwise identical executions. Because `soft_trigger_max_seed_distance` is an actual frozen #839 ranking feature, this is **not** waived as irrelevant metadata.

Before the current strengthened #862 equivalence result is known, the acceptance rule is frozen as follows. The pair-portable hard/P19/P20 generator must return exactly:

`PASS_URC_PAIR_PORTABLE_GENERATOR_GMN_OPERATIONAL_EQUIVALENCE`

with frozen GMN counts:

- hard = 226;
- P19-soft = 1,075;
- P20-soft = 3,203;
- union = 4,504.

The artifact must prove all of:

- exact hard order match = true;
- exact hard family match = true;
- exact P19 **discrete** match = true, including family order/IDs, component IDs, event/member IDs, trigger/support IDs, years, counts, booleans, and all other non-floating structure;
- P19 floating leaves satisfy **absolute tolerance 1e-12 and relative tolerance 1e-12**;
- the reported maximum absolute P19 floating difference is <=1e-12;
- exact P20 family match = true;
- exact P20 isolated-quartet match = true;
- regenerated-vs-frozen #839 34-column feature matrices are numerically equivalent under the same 1e-12 absolute/relative rule;
- serialized-model prediction maximum absolute difference is <=1e-12;
- the final #839 diversity order is **exactly identical**, with deployment application-order SHA-256 `9063270f131b81bb0032026b2742b985ab0f8d5655abb46a1d405d30501b6d7d`;
- performance metric computed = false;
- truth labels used by generator/ranker = false;
- SonotaCo 2013/2014 access = false;
- MAARSY scientific access = false;
- target information access = false.

Thus the only relaxed identity is machine-level representation of derived P19 floating descriptors. Candidate existence, membership, ordering, discrete structure, and the **actual frozen downstream ranking must remain exact**. A tolerance-only match without exact final-order invariance does not pass.

The final execution workflow must pin the **specific passing #862 source commit, workflow run ID, artifact ID, and artifact digest** before any SonotaCo archive is opened.

## Required ranker identity

The already-passed #860 pair-portable ranker transport is mandatory. Final execution must pin:

- serialized ExtraTrees model SHA-256 `ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909`;
- exact GMN feature-matrix SHA-256 `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`;
- exact fitted-prediction SHA-256 `493d39cd57f272ee088b1c1c80240c2af99595a5e8a3c91defe693cd460041ac`;
- exactly 34 application features;
- explicit ordered-year pair and event-to-year mapping rather than event-ID-prefix inference;
- diversity lambda 0.8 and scale 1.0;
- no truth-label input.

## Required comparator bundle

The final comparator source bundle is frozen by #820/#865 and may not be replaced after SonotaCo access.

Pin exactly:

- comparator source-export workflow run `31346168826`;
- artifact ID `9047392743`;
- artifact digest `sha256:8acb1986561d44194e2b7ebf5eb725a115eff5ba10b9b5d30a74f63a71a93fbc`;
- Sugar uncertainty-core SHA-256 `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`;
- catalogue-HDBSCAN runner SHA-256 `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

Scientific comparator semantics are exactly those frozen in `orbittrace_governance/FINAL_COMPARATOR_SAME_INFORMATION_FREEZE_V1.md`. In particular, no known-shower/native-background truth may filter comparator or candidate detector input.

## Required final matched evaluator

The truth-opening evaluator is exactly #854:

- evaluator source SHA-256 `cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c`;
- source-audit workflow run `31344796531`;
- audit artifact ID `9046953388`;
- audit artifact digest `sha256:315f01965b1fec3820f32ab56cb57d96f7401373e3d2d127c78d7da35808210f`.

It retains pairwise common-row universes, comparator-defined candidate budget B, one-to-one maximum-total-F1 matching, fixed size strata, the broad/sparse effect-size routes, and the frozen 10,000-replicate stratified bootstrap.

No alternative evaluator may be substituted after final-test values are visible.

## Required external-validation gate freeze

Before SonotaCo access, the downstream no-retuning external gate must already be immutable so a literature result cannot influence how generalization is judged.

Required governance merge commit:

`45428174b36b8a5207951bc2c046ced3aa2e9781`

The sole scored external endpoint remains **MAARSY 2022**, with MAARSY 2021 allowed only as permanently unlabeled recurrence support. The exact downstream pass token is `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION`.

## SonotaCo scientific-data boundary

Only after every prerequisite above passes may an execution child receive the exact SonotaCo 2013 and 2014 archive transport.

For each comparator × year pair, the child must:

1. remove solar longitude 20°–55° before target-sensitive processing or truth access;
2. apply only frozen label-free structural/quality cuts;
3. construct and hash the pairwise common-row manifest;
4. run and freeze #839 output on those exact common rows;
5. run and freeze the relevant comparator output on those exact common rows;
6. hash both outputs and all source/configuration identities;
7. **only then** reveal known-shower truth for those exact row IDs;
8. evaluate with the frozen #854 evaluator;
9. preserve the complete result and bootstrap records without changing any method or gate.

SonotaCo native shower/background designations may not affect row inclusion, detector calibration, family generation, rank, clustering, or postprocessing before the truth-open boundary.

## One-shot conservation rule

Once any SonotaCo 2013/2014 scientific archive value is opened for the final test:

- #839 cannot be retuned, replaced, or reranked;
- Sugar/HDBSCAN parameters or row rules cannot change;
- the evaluator cannot change;
- the SonotaCo years cannot change;
- the MAARSY validation gate cannot change;
- no alternate final candidate can be presented as a fresh one-shot test on the same panel.

A final literature failure is a scientific failure of the frozen candidate on the permanent test, not permission for another SonotaCo attempt.

## Target firewall

Final-test authorization is **not** target authorization.

Throughout the literature test:

- OrbitTrace target coordinates, radiant, velocity, orbit, identity, members, activity profile, prior recovery performance, and target-region candidate results remain inaccessible;
- the withheld solar-longitude 20°–55° interval remains excluded;
- no target-specific search, nearest-neighbor lookup, member expansion, family merge, or reranking is permitted.

Only a final literature PASS followed by exact `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION` can authorize the separately frozen blind OrbitTrace search.

## Mechanical authorization output

The accompanying adjudicator may return only:

- `AUTHORIZED_FINAL_SONOTACO_2013_2014_EXECUTION`, or
- a fail-closed `NOT_AUTHORIZED_*` state.

It can never authorize OrbitTrace target access.