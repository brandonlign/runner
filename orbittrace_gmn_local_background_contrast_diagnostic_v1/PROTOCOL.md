# OrbitTrace GMN local-background contrast diagnostic v1

## Scientific role

This is a **target-excluded GMN mechanism diagnostic only**. It does not modify v31 and it does not access SonotaCo. Its sole question is whether candidate-internal physical coherence becomes more useful for ranking when it is normalized against the contemporaneous local meteor background rather than interpreted in isolation.

The motivation is fixed before outcome: the active GMN quality representation already contains member count, year balance, centroid separation, and within-family median/q90/max cohesion, while prior stability and source-blind quality/diversity diagnostics did not improve the hard-family ranking. This diagnostic therefore tests a different quantity: **local-background contrast**.

A PASS may authorize one separately frozen transferable successor. A FAIL permanently closes this exact background definition, exact contrast order, and exact equal-rank fusion. No post-result window search, score weighting, feature subset, threshold, alternate background construction, or route-specific rescue is authorized.

## Data firewall

- GMN development years: 2022 and 2023 only.
- Protected solar longitude **20 deg to 55 deg inclusive remains excluded before feature construction**.
- OrbitTrace target information and target-region events remain inaccessible.
- SonotaCo 2013/2014 is inaccessible during this diagnostic.
- MAARSY and DMS are inaccessible.
- Candidate generation and memberships are immutable.

The candidate universe is the exact 226 hard families in frozen P19 prelabel payload SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`. The immutable v8 result SHA-256 is `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`.

## Frozen local-background contrast feature

For each candidate and each year separately:

1. Use the immutable annual candidate centroid and exact frozen `centroid_distance` physical metric already used by the candidate-cohesion code.
2. Resolve all immutable candidate member event IDs against the target-excluded GMN scan and compute their distances to that annual centroid.
3. Define the **local background** as every target-excluded scan event from the same year whose solar longitude lies within **2 degrees circular distance of the candidate annual centroid solar longitude**, excluding the candidate's own member IDs. This is one fixed 4-degree-wide local window, inherited from the fixed-4-degree candidate geometry; it is not searched.
4. Compute the annual member q90 distance.
5. Compute annual **separation AUC** as the exact empirical probability that a randomly selected candidate member is closer to the candidate centroid than a randomly selected local-background event, counting equal distances as one half. Higher is better.
6. Compute annual **background penetration** as the fraction of local-background events whose centroid distance is less than or equal to the member q90 radius. Lower is better.
7. Fail closed if an annual candidate has no members, no centroid, or no local-background events. No family is deleted or assigned a fallback score.

Summarize each family by:

- `worst_auc = min(auc_2022, auc_2023)`;
- `worst_penetration = max(penetration_2022, penetration_2023)`;
- `worst_member_q90 = max(member_q90_2022, member_q90_2023)`.

The complete feature vector is written to a prelabel artifact before development truth is used for any metric or rank assessment.

## Sole ranking and fusion rule

There is one contrast order only:

`(higher worst_auc, lower worst_penetration, lower worst_member_q90, family_id)`.

Equivalently sort by:

`(-worst_auc, worst_penetration, worst_member_q90, family_id)`.

There is one fusion only. Convert the immutable hard order and contrast order to 1-based ranks, sum them equally, and sort by:

`(hard_rank + contrast_rank, hard_rank, family_id)`.

No coefficient, threshold, calibration, background-window alternative, source quota, diversity parameter, candidate deletion, or budget-specific rule is permitted.

## Binding GMN signal gate

The first technically valid result is binding. PASS requires **all**:

- fused recovered@100 strictly greater than the immutable hard baseline;
- fused recovered@50 not lower than baseline;
- fused top-100 dominant precision not lower than baseline;
- fused MRR not lower than baseline.

Otherwise verdict is FAIL and this exact mechanism is closed.

## Claim boundary

Even a PASS is only target-excluded GMN development evidence for local-background contrast. It does not beat HDBSCAN or Sugar on SonotaCo and does not itself authorize any SonotaCo view. Any transfer must be separately frozen first and must respect the existing SonotaCo exposed-development closure.
