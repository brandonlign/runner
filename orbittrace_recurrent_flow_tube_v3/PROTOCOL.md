# OrbitTrace recurrent flow tube v3 — owned soft-evidence flow

## Scientific role and provenance

RFT v3 is the exact **pre-specified `owned_soft_evidence` variant** from the RFT v2 protocol, promoted as a distinct successor after its target-excluded GMN 2022 development result. This promotion does **not** change or rescue the binding RFT v2 verdict: RFT v2 remains `FAIL_RFT_V2_GMN2022_DEVELOPMENT_VIABILITY`.

The exact variant was frozen before its first outcome in RFT v2 protocol blob `fa6ec175e1ec32608e12b0571d7bcab686408443`, under the preregistered explanatory ablation:

> `owned_soft_evidence`: identical soft-evidence procedure using the frozen owned tube lists instead of unowned lists.

Therefore v3 introduces no post-outcome scientific parameter, threshold, weight, or ranking change. It simply promotes those already-frozen bytes/semantics as the sole method for a future one-shot held-out evaluation.

The authoritative RFT v2 development workflow run is `31561653503`, artifact ID `9127986475`, artifact digest `sha256:adfe47ed0909ea7edcef6bedcfdc72fadb022829291ceeb1f1aff5a5658b7a1b`.

Pinned development files:

- `RFT_V2_GMN2022_DEVELOPMENT.json` SHA-256 `d5ddbdf5f14a76588924f66a3cb138b888e83071fc3c29fd6522a374b44a37b6`;
- `RFT_V2_GMN2022_PRELABEL.json` SHA-256 `856c874b49be03a019c7f96780832ada8094b4771527478a4cac6afd3e150c35`.

The preregistered owned-soft-evidence GMN 2022 development metrics were:

- eligible known labels: 359;
- qualified matches: **133**;
- recovered@25: **18**;
- recovered@50: **33**;
- recovered@100: **60**;
- recovered@500: **120**;
- top-100 dominant precision: **0.6602954645802933**;
- MRR: **0.03157184203024598**;
- fragmentation median top500: **1.0**.

Those values satisfy all four core RFT v2 development qualification thresholds attached to coverage, top-100 recovery, purity, and fragmentation: qualified >=120, recovered@100 >=55, precision >=0.60, fragmentation <=3. They are **development-selection evidence**, not a new held-out result.

## Exact v3 method

The scientific geometry and all numerical constants remain the frozen RFT v1 values from implementation blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`:

- state: solar-centered radiant longitude, ecliptic latitude, geocentric speed;
- 2° solar-longitude strata;
- reciprocal KNN with K=4 and minimum atom size 4;
- minimum 3 strata, 6° span, and 10 retained events;
- 16 deterministic perturbation replicas;
- perturbation radiant sigma 0.35° and speed sigma 1%;
- perturbation Jaccard survival threshold 0.50;
- trajectory trim threshold 2.5;
- exact frozen pair, transition, fit, and residual functions.

The **sole v3 hypothesis generator is the frozen owned tube construction**: nominal paths are generated with RFT v1 path ownership enabled. No unowned tube may enter v3.

For every nominal owned tube:

1. Measure persistence against the owned tubes of perturbation replicas 1–16 using the exact v1 maximum-member-Jaccard survival rule at Jaccard >=0.50.
2. Persistence is a continuous measured feature. **No persistence cutoff is applied.**
3. Apply the unchanged RFT trajectory trim and require at least 10 retained members.
4. Compute coherence without multiplying by persistence:

   `coherence = log1p(n_members) * log1p(strata) / (1 + median_transition_cost + median_trajectory_residual)`.

5. Collapse exact post-trim member duplicates by retaining the representative with lowest `(median_transition_cost + median_trajectory_residual, tube_id)`.
6. Candidate ID is SHA-256 prefix of `RFT3|<sorted member IDs>`.

Create 1-based ranks:

- coherence rank: descending coherence, tie by family ID;
- persistence rank: descending persistence, tie by family ID.

The **only v3 order** is:

`(coherence_rank + persistence_rank, coherence_rank, family_id)`.

No fusion-weight search, persistence threshold, rank product, source quota, candidate budget optimization, diversity pass, reranking, parameter search, or alternate order is permitted.

## GMN 2023 one-shot held-out authorization

GMN 2023 has not been accessed by v3 before this protocol freeze. The exact v3 method above is frozen before any v3 GMN 2023 outcome.

GMN 2023 may be accessed **once** only after execution verifies all of the following before catalogue parsing:

1. the authoritative RFT v2 development result and prelabel files match the exact SHA-256 values above;
2. RFT v2's binding verdict remains FAIL (not rewritten or rescued);
3. the `owned_soft_evidence` ablation metrics exactly match the frozen values above and satisfy the four core development thresholds;
4. the v2 result/prelabel firewall flags show no GMN2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY, DMS, or protected-region access;
5. the v3 protocol and heldout implementation/workflow source pins match their frozen bytes.

Only after those checks may the runtime source list switch from GMN 2022 to the twelve fixed GMN 2023 months. No GMN 2022 data or labels may be reused to change v3 after the heldout begins.

## Frozen GMN 2023 held-out gates

To avoid choosing a friendlier post-development standard, v3 adopts the exact five numerical gates already frozen for the earlier RFT v1 GMN2023 heldout evaluator in memo blob `55794c9b9239598544cd15991392120bf8d85211`:

1. qualified known showers >= 120;
2. recovered@100 >= 58;
3. recovered@50 >= 35;
4. top-100 dominant precision >= 0.65;
5. fragmentation median top500 <= 3.0.

`PASS_RFT_V3_GMN2023_HELDOUT` requires all five gates plus every provenance/firewall assertion.

`USEFUL_BUT_INSUFFICIENT_RFT_V3_GMN2023_HELDOUT` requires at least four of five gates, recovered@100 >=52, and every provenance/firewall assertion.

Otherwise the verdict is `FAIL_RFT_V3_GMN2023_HELDOUT`.

The only post-result failure classes are descriptive:

- coverage failure: qualified <120;
- ranking failure: qualified >=120 and recovered@100 <58;
- fragmentation failure: median fragmentation >3;
- purity failure: top100 precision <0.65.

No 2023 ablations, reranking, threshold search, ownership alternative, score change, candidate modification, parameter search, or retry with a changed method is authorized.

## Firewall and claims

- Protected solar longitude 20°–55° remains inaccessible.
- OrbitTrace target information and target-region events remain inaccessible.
- SonotaCo 2013/2014 remains inaccessible during v3 heldout work.
- MAARSY and DMS remain scientifically inaccessible.
- GMN 2023 is a one-shot heldout test for the exact frozen v3 method; it is not used for development.
- A heldout PASS may be described as heldout GMN generalization of v3, not as validation of OrbitTrace itself and not as SonotaCo external validation.
