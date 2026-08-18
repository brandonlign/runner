# OrbitTrace DAG corroboration-mass rank v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE SHOWER TRUTH FOR THIS SUCCESSOR.**

This is the single detector-extraction follow-up authorized by the binding zero-label result `SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1`.

The predecessor support-resolved TopoModal cut established that candidate existence, recovery, purity, and fragmentation remain strong under sparse thinning, while its native modal-contrast order failed only the MRR gates. The new rule therefore changes **ranking only**. Candidate memberships remain the exact raw support-resolved TopoModal memberships.

The cross-hierarchy DAG result established that the exact nonempty TopoModal↔recurrent-EOM common-refinement atoms are more stable under thinning than either parent representation and that dense correspondence can be many-to-many. This successor uses every DAG edge simultaneously; it never chooses a unique recurrent parent.

The construction is consistent with the broader cluster-ensemble idea of extracting consensus evidence from multiple partitions and with correspondence-based stability analysis of hierarchical clusterings, but the exact score below is an OrbitTrace-specific, parameter-free event-mass ranking rule.

## 1. Firewall

Use only the already-frozen target-excluded GMN 2022+2023 sparse development panels.

Inclusive solar longitude `[20.0,55.0]` remains excluded.

Forbidden throughout this experiment:

- OrbitTrace target identity, target coordinates, target members, target orbital information, or protected target-region events;
- SonotaCo scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- shower-truth-informed score terms, thresholds, weights, tie rules, candidate deletion, panel-specific rules, or post-result rescue.

## 2. Immutable zero-label source

Use only the binding cross-hierarchy refinement DAG v1 artifact:

- workflow run `32185851992`;
- artifact ID `9342489614`;
- artifact digest `sha256:f933ebad11e507a7a5a669b00b9eed944fa0a61216ed728d37232d5354f57558`;
- prelabel file `CROSSHIERARCHY_REFINEMENT_DAG_V1_PRELABEL.json`;
- prelabel SHA-256 `65ead5f26026dbed74a098cc1df17d000c28705cd8fcd3af5134fd98151a0573`;
- result file `CROSSHIERARCHY_REFINEMENT_DAG_V1_RESULT.json`;
- result SHA-256 `b7b4a4355a488108f4107e86e98bfc872f67c176d63eac1e56772a78f0708721`;
- binding verdict `SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1`.

Use only its d=128 and d=1024 panels for this truth-scored sparse ranking experiment. d=64 is structural evidence only and is not truth-scored here.

For each panel the immutable source contains:

- every raw support-resolved TopoModal candidate `T_i`, its exact membership, original rank, modal contrast, and family hash;
- every recurrent-EOM candidate `R_j`, its exact membership, original recurrent rank, recurrent stability, and family hash;
- every nonempty exact atom `A_ij = T_i ∩ R_j`;
- exact event-universe hashes and structural audits.

The binding DAG truth-free result is an input only as authorization/provenance. No shower truth from any predecessor result is an input to candidate construction or ordering.

## 3. Candidate catalogue

For every d=128/d=1024 panel, the successor candidate identity set is **exactly** the complete raw support-resolved TopoModal candidate set from the DAG prelabel.

No candidate membership may change by even one event.

No candidate is deleted, merged, intersected into an atom, unioned with another candidate, clipped to recurrent coverage, split, or duplicated.

Let `N_R` be the number of recurrent-EOM candidates in the panel. Every recurrent candidate has a frozen one-indexed rank `r_j in {1,...,N_R}`.

Define its scale-free recurrence priority

`q_j = (N_R - r_j + 1) / N_R`.

Thus recurrent rank 1 has `q=1`, the final recurrent rank has `q=1/N_R`, and no score magnitude from a different method is mixed into this ordinal signal.

## 4. Sole successor score — DAG corroboration mass

For a TopoModal candidate `T_i`, use every incident DAG atom. Define

`S_i = sum_j ( |A_ij| / |T_i| ) * q_j`,

where the sum is over all recurrent candidates and nonexistent edges contribute zero.

Equivalent event-level interpretation: choose one event uniformly from `T_i`; if it is covered by recurrent-EOM, assign the normalized priority of its recurrent parent, otherwise assign zero. `S_i` is the mean of that truth-free corroboration value over all events in `T_i`.

Properties frozen by construction:

- `0 <= S_i <= 1`;
- recurrent coverage is automatically included because atom weights sum to at most 1;
- all many-to-many edges contribute; there is no unique-parent resolver;
- a candidate with no recurrent overlap has `S_i=0`;
- there is no overlap threshold, atom-size threshold, degree penalty, coefficient, exponent, normalization fit, learned model, or scale-specific parameter.

For audit only, also record

`C_i = sum_j |A_ij| / |T_i|`,

the unweighted recurrent coverage fraction. `C_i` is not an independent ranking objective or fitted weight; its effect is already contained in `S_i`.

## 5. Final deterministic order

Order every raw TopoModal candidate lexicographically by:

1. descending `S_i`;
2. ascending original raw TopoModal rank;
3. ascending `family_hash`.

Assign new ranks `1..N_T` in that order.

All candidates are retained exactly once. The original TopoModal order is retained as a complete control and used only as a tie-break after exact equality of `S_i`.

This is scientifically distinct from the closed overlap-consensus/Pareto lanes:

- it uses the complete raw support-resolved TopoModal catalogue, not only uniquely corroborated children;
- it allows and integrates multiple recurrent parents instead of requiring unique correspondence;
- it changes only rank, never memberships;
- it does not combine native modal-prominence rank with recurrent rank by Pareto sorting, Borda/rank sum, product, weighted blend, or learned score.

## 6. Equal-budget controls

For every panel define

`K = min(N_T, N_R)`.

Freeze and evaluate three exact catalogues at the same `K`:

1. **successor** — all raw TopoModal candidates ordered by `S_i`, first K;
2. **native TopoModal control** — same exact TopoModal memberships in original frozen rank order, first K;
3. **recurrent-EOM control** — original frozen recurrent candidates/rank order, first K.

No candidate budget may depend on truth, year, shower count, or result.

## 7. Zero-label authorization gate

Before shower truth opens, persist `DAG_CORROBORATION_MASS_RANK_V1_PRELABEL.json` and require all of the following:

1. DAG prelabel/result SHA-256 and binding SUPPORT verdict reproduce exactly;
2. exactly eight panels exist: d=128/d=1024 × buckets 0..3;
3. all panel event-universe hashes and firewall flags reproduce;
4. every successor candidate family identity and membership is byte-for-byte identical to the corresponding raw TopoModal candidate;
5. every recurrent rank is a permutation `1..N_R` and every `q_j` equals the frozen formula exactly;
6. every atom is nonempty, is a subset of both referenced parents, and all atoms incident to a TopoModal candidate are event-disjoint;
7. every `S_i` recomputes exactly from atom counts and recurrent ranks and lies in `[0,1]`;
8. every recorded `C_i` recomputes exactly and lies in `[0,1]`;
9. final successor order is a deterministic permutation of every raw TopoModal candidate with continuous ranks `1..N_T`;
10. all eight panels have positive equal budget `K` and successor capacity `N_T >= K`;
11. the mechanism is active: at least one panel's full ordering differs from native TopoModal;
12. the mechanism is evaluation-active: at least one panel's first-K family set/order differs from native TopoModal;
13. mean `S_i` among successor first-K is no lower than mean `S_i` among native-TopoModal first-K in every panel, with a strict increase in at least one panel.

Only `PASS_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH` authorizes shower truth.

A pretruth failure closes this exact extraction rule unless the failure is purely technical and demonstrably occurs before any valid scientific pretruth result. No score/rule may change after a valid pretruth outcome.

## 8. Truth semantics

If and only if pretruth passes, use the established target-excluded GMN sparse truth runtime and matching semantics:

- evaluate each d=128/d=1024 bucket separately for 2022 and 2023, giving 8 annual panels per scale;
- eligible annual shower requires at least 4 truth events in that panel-year;
- positive candidate match requires precision `>=0.5` and overlap `>=4`;
- evaluate successor, native TopoModal control, and recurrent-EOM control at identical panel budget K;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, median top-500 fragmentation, historical conditional MRR, and zero-filled eligible-query MRR.

### Binding MRR definition

For each eligible shower `q`:

- `RR(q)=1/r_q` if the shower is first positively matched at successor rank `r_q`;
- `RR(q)=0` if it is unrecovered within the evaluated catalogue.

`MRR_zero = mean_q RR(q)` across **all eligible showers**, including unrecovered showers as zero.

Historical conditional MRR is diagnostic only.

## 9. Binding twelve-gate promotion contract

The new score is intended to fix prioritization without sacrificing the raw TopoModal catalogue's demonstrated recovery/purity. Therefore it must beat the native order on MRR while preserving its stronger recovery behavior.

### Fine sparse scale — d=1024

1. successor qualified-total is at least native TopoModal;
2. successor qualified matches are nonlower than native TopoModal in at least `6/8` annual panels;
3. successor mean `MRR_zero` is **strictly greater** than native TopoModal;
4. successor mean `MRR_zero` is at least recurrent-EOM;
5. successor mean top-100 dominant precision is at least native TopoModal;
6. successor mean median top-500 fragmentation is no higher than native TopoModal.

### Coarse sparse scale — d=128

7. successor qualified-total is at least native TopoModal;
8. successor qualified matches are nonlower than native TopoModal in at least `6/8` annual panels;
9. successor mean `MRR_zero` is **strictly greater** than native TopoModal;
10. successor mean `MRR_zero` is at least recurrent-EOM;
11. successor recovered@25 total is at least native TopoModal;
12. successor mean top-100 dominant precision is at least native TopoModal and successor mean median top-500 fragmentation is no higher than native TopoModal.

All twelve gates are mandatory.

Return exactly one binding truth verdict:

- `PASS_DAG_CORROBORATION_MASS_RANK_V1`, or
- `FAIL_DAG_CORROBORATION_MASS_RANK_V1`.

The first technically valid truth execution after a valid frozen pretruth PASS is binding.

## 10. Closure and next authorization

A PASS authorizes only one separately frozen scale/full-GMN translation of this exact membership-preserving ranking rule. It still does not authorize protected OrbitTrace target access or external-survey claims.

A valid FAIL permanently closes this exact DAG corroboration-mass rank. Do not rescue it by:

- adding modal contrast or native rank as a weighted score term;
- changing normalized recurrent priority;
- replacing the linear event-mass expectation with max/min/product/geometric mean;
- using atom Jaccard, overlap coefficient, component size, degree, entropy, or persistence as a new score term;
- adding thresholds, quotas, one-parent selection, orphan deletion, component contraction, or candidate membership edits;
- changing K, gates, tie rules, scale rules, or panel subsets;
- learning a reranker or searching score variants after truth.

Any later successor must be scientifically distinct and separately frozen before truth.