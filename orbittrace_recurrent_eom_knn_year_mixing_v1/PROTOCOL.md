# OrbitTrace recurrent-EOM local-kNN year-mixing v1 — frozen protocol

## Status

Frozen before implementation and before the first scientific outcome.

The exact parent is recurrent-EOM HDBSCAN v1, selected on PR #1243. This successor is **rank-only** and consumes the exact binding recurrent-EOM prelabel catalogue from run `31827903547`; it does not refit HDBSCAN and therefore cannot change the 2,097 parent candidate memberships.

Scientific firewall:

- protected solar longitude `[20 deg,55 deg]` remains inaccessible;
- no OrbitTrace target information/events;
- no MAARSY or DMS scientific access;
- no SonotaCo values enter this GMN development test;
- no AMOS access or outreach;
- only target-excluded GMN 2022+2023 geometry and year identity may enter the successor score;
- the complete successor order is persisted before shower truth is opened;
- the first technically valid GMN outcome is binding;
- no post-result k change, graph symmetrization, edge weighting, cap, transform, pseudocount, exponent, blend, rank fusion, threshold, or HDBSCAN change is allowed.

## 1. Exact parent and binding candidate universe

Pinned recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Pinned recurrent-EOM development runner Git blob:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

Binding parent GMN run `31827903547`, artifact `9229646556`:

- prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`;
- result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`;
- candidate count `2,097`.

The successor must use the exact ordered `successor_candidates` from that binding prelabel as its parent catalogue. It may not rerun HDBSCAN to reconstruct them.

Exact binding recurrent-EOM metrics:

### 2022

- recovered@25 `22`
- recovered@50 `45`
- recovered@100 `89`
- recovered@500 `193`
- top-100 dominant precision `0.7856486012780942`
- MRR `0.022498269587309373`
- qualified matches `236`
- median top-500 fragmentation `1.0`

### 2023

- recovered@25 `23`
- recovered@50 `46`
- recovered@100 `89`
- recovered@500 `192`
- top-100 dominant precision `0.7867680236864514`
- MRR `0.0220239288966045`
- qualified matches `244`
- median top-500 fragmentation `1.0`

## 2. Motivation

Recurrent-EOM rewards HDBSCAN branches that have density persistence in both observing years. It does not distinguish whether the two annual samples actually occupy the **same local geometry** within the selected branch.

A recurring physical meteor stream should tend to have 2022 and 2023 events locally intermixed in GEO6. A branch can instead receive substantial annual EOM from both years while its local neighborhoods remain year-segregated.

This successor measures that local intermixing without changing the hierarchy or removing candidates.

It is distinct from closed mechanisms:

- cross-year-core changed HDBSCAN mutual-reachability geometry upstream and reduced recovery; this method never changes HDBSCAN or candidate membership;
- reciprocal-transfer fit separate annual HDBSCAN models and retained only reciprocal matches; this method uses one fixed parent catalogue and deletes nothing;
- directional morphology compared annual second moments; this method is graph-local rather than a global covariance summary;
- the prior MST-bottleneck experiment measured within-year tree shape in another representation; this method measures **cross-year label mixing** on pooled local neighborhoods.

## 3. Frozen local graph

For each exact recurrent-EOM candidate `C`, use only its exact member events and the parent's exact six-dimensional GEO representation:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`.

Order candidate rows deterministically by event ID before neighbor construction.

Let `n=|C|` and define

`k_C = min(10, n-1)`.

The value 10 is inherited exactly from the parent's fixed `min_samples=10`; it is not selected from this experiment.

Construct the exact Euclidean directed `k_C`-nearest-neighbor graph within `C` using `scipy.spatial.cKDTree` under pinned SciPy `1.14.1`, one worker, with self-neighbors removed. Every point contributes exactly `k_C` outgoing edges, so

`m(C)=n*k_C`.

No mutual-neighbor requirement, graph symmetrization, distance cutoff, distance weight, adaptive k, year-specific neighbor search, or external-background point is permitted.

## 4. Fixed-count year-mixing enrichment

Let:

- `n_1(C)`, `n_2(C)` be annual member counts;
- `x(C)` be the number of directed kNN edges whose endpoints come from different years.

Conditioning on the fixed directed graph and fixed annual counts, a random permutation of year labels gives any directed edge cross-year probability

`q(C)=2 n_1(C)n_2(C) / [n(C)(n(C)-1)]`.

Thus expected cross-year edges are

`mu(C)=m(C)q(C)`.

Define

`M_knn(C)=x(C)/mu(C)`

when both years are present and `mu>0`; otherwise `M_knn(C)=0`.

No clipping, logarithm, p-value transform, z-score, variance correction, pseudocount, or winsorization is permitted.

## 5. Successor score

For each binding recurrent candidate, take its already-frozen recurrent stability `E_rec(C)` from the binding prelabel and define

`S_knn(C)=E_rec(C) * M_knn(C)`.

The successor ordering is fixed as:

1. descending `S_knn`;
2. descending binding `E_rec`;
3. descending binding ordinary HDBSCAN stability;
4. descending member count;
5. ascending deterministic membership-derived ID with provenance prefix `REOMKNN1`.

The family-ID prefix cannot influence any preceding key.

No candidate is added, deleted, split, merged, or membership-trimmed.

## 6. Pretruth invariants

Before shower truth can be evaluated, the runner must prove:

1. binding parent prelabel and result hashes are exact;
2. target-excluded event counts are exactly `315024` for 2022 and `423658` for 2023;
3. every one of the 2,097 binding candidate event IDs maps to exactly one accessible event row;
4. every candidate membership is reproduced exactly from the binding prelabel;
5. the successor contains the same 2,097 membership sets exactly;
6. all neighbor endpoints remain inside their own candidate;
7. each candidate has exactly `n*k_C` directed edges after self removal;
8. all mixing expectations/enrichments/scores are finite;
9. the complete successor order is written and SHA-256 frozen before shower truth is used.

Failure of any invariant is an engineering no-result.

## 7. Binding GMN evaluation and gate

Use the exact recurrent-EOM annual evaluator and truth convention.

The first technically valid result passes only if all are true relative to the exact recurrent parent:

1. candidate membership universe is identical;
2. complete rank order changes (`mechanism_active=true`);
3. recovered@100 is strictly higher in at least one year and not lower in the other;
4. recovered@50 is not lower in either year;
5. top-100 dominant precision is not lower in either year;
6. MRR is not lower in either year;
7. median top-500 fragmentation is not higher in either year.

Recovered@25, @500, and full-catalogue qualified matches are reporting-only, preserving the recurrent-EOM gate convention.

PASS token:

`PASS_RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT`

A scientific FAIL permanently closes this exact raw local-kNN mixing product ranker. No alternate k, mutual graph, symmetrization, additive blend, transformed enrichment, or fitted combination may be rescued from the result.

A PASS authorizes one separately frozen direct exposed SonotaCo benchmark against recurrent-EOM, v31, and the existing matched literature comparators. It does not authorize target-region access.

## 8. Relation to the earlier MST-export technical no-result

A separately frozen attempt to use HDBSCAN's exposed global mutual-reachability MST stopped before any successor prelabel or scientific result because an HDBSCAN run with MST export produced 2,079 recurrent candidates instead of the binding 2,097. Run `31891304186`, artifact `9248667099` is therefore engineering provenance only.

This kNN method is a distinct scientific successor, not a rerun of that endpoint. Its graph definition and entire gate are frozen here before implementation/outcome, and it uses the binding recurrent catalogue directly rather than refitting HDBSCAN.

## 9. Potential contribution if supported

If successful, the contribution is **recurrent density clustering with graph-local temporal exchangeability ranking**: recurrent-EOM selects repeated-observation density branches, while a fixed local-neighborhood mixing enrichment prioritizes branches whose independent observing years occupy the same local phase-space neighborhoods.