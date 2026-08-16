# OrbitTrace recurrent local-BIC HDBSCAN v1 — frozen GMN protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SCIENTIFIC OUTCOME.**

This is a genuinely new hierarchy-construction/extraction successor to promoted recurrent-EOM HDBSCAN v1. It is motivated by the already-known structural limitation that an extraction-only recurrence objective cannot recover a stream branch that the upstream HDBSCAN hierarchy never represents, and by the independent statistical principle that a density cluster should be judged relative to its local background rather than by an absolute event count.

The design is not a rescue of failed exposure-LR, shared-drift BIC, wavelet-recurrence, B1, P11, or local-background trajectory-contrast. It uses none of their fitted weights, response models, trajectory tubes, global year fractions, wavelet scores, posterior cutoffs, or result-informed settings.

Relevant independent methodological motivation predating this outcome includes HDBSCAN/FOSC hierarchical density extraction (Campello, Moulavi & Sander 2013, DOI 10.1007/978-3-642-37456-2_14; Campello et al. 2013 FOSC, DOI 10.1007/s10618-013-0311-4), meteor-shower significance relative to local sporadic background (Moorhead 2016, arXiv:1511.02487), and statistically significant density clustering (Significant DBSCAN+, DOI 10.1145/3474842). These motivate the mechanism class only; no published method is copied as the scientific implementation below.

## 1. Scientific parent and development corpus

Parent comparator is the exact binding recurrent-EOM HDBSCAN v1:

- implementation blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GMN binding run `31827903547`;
- parent prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`;
- parent result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`.

Development data remain exact target-excluded GMN 2022+2023 only. The protected solar-longitude interval `[20.0,55.0]` is excluded inclusively before radiant/speed scientific use. OrbitTrace target information/events, SonotaCo 2013/2014, AMOS, MAARSY and DMS are inaccessible to this GMN selection.

## 2. Representation

Use the exact promoted GEO6 embedding unchanged:

`[cos(sol), sin(sol), sin(lon_sc) cos(beta), cos(lon_sc) cos(beta), sin(beta), vg/72]`.

For density-volume reasoning the **intrinsic physical dimension is fixed at D=4**: one solar-longitude coordinate, two radiant-sphere degrees of freedom, and one speed coordinate. The six columns are an embedding of this four-dimensional physical manifold; D is not fitted or searched.

## 3. Low-support HDBSCAN hierarchy

The promoted parent fixes `min_cluster_size=10` and `min_samples=10`. The successor instead constructs exactly one pooled 2022+2023 HDBSCAN hierarchy with:

- `min_cluster_size=8`;
- `min_samples=4`;
- Euclidean metric;
- `cluster_selection_method='eom'` only as the library extraction path;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=false`;
- no z-scoring, feature weighting, quality trimming, orbit features, or labels.

These counts are fixed from the pre-existing scientific recovery definition rather than from an outcome: an annual recovered shower requires at least four overlapping meteors, so a structure independently supportable at that minimum in both observing years has pooled support `4+4=8`; the local core support is the same single-year minimum of four. No alternate `min_cluster_size` or `min_samples` is allowed after outcome.

## 4. Scale-invariant local log-persistence evidence

Let `lambda_birth(C)>0` be a non-root condensed-tree node's birth density and let a departing point/child branch leave `C` at density `lambda_exit`. For year `y`, define

`L_y(C) = sum_b n_y(b) * ln(lambda_exit(b) / lambda_birth(C))`,

where `n_y(b)` is the exact number of descendant events from year `y` carried by departing branch `b`.

Rows with `lambda_exit < lambda_birth` or nonfinite required values fail closed. Equal birth/exit density contributes zero. The root is never a selectable cluster and receives no scientific quality.

This statistic uses a **ratio of density scales**. Therefore multiplying every geometric distance by a positive constant multiplies both inverse-distance lambdas by the same reciprocal constant and leaves every `ln(lambda_exit/lambda_birth)` exactly unchanged.

## 5. Smooth recurrent common evidence

No global annual event fraction is used. No annual count is normalized by the full-survey event count.

For a node with annual local log-persistence evidence `L_1,L_2`, define

`L_common(C) = 4 L_1 L_2 / (L_1 + L_2)` when both are strictly positive, otherwise `0`.

This is the twice-harmonic common evidence. It has three fixed properties that motivate its use:

1. it is zero if one observing year supplies no local persistence evidence;
2. when the two years carry equal evidence `L`, it equals the pooled evidence `2L`;
3. when evidence is unequal it shrinks smoothly rather than using the noise-sensitive hard minimum of recurrent-EOM.

There is no exponent, weight, epsilon, year coefficient, clipping threshold, or alternate combiner.

## 6. Local BIC-style FOSC quality

Because local D-dimensional density scales as `lambda^D`, the recurrent local log-likelihood evidence is fixed as

`logLR(C) = D * L_common(C)` with `D=4`.

For node support `n_C`, define the sole extraction quality

`Q(C) = 2 * logLR(C) - ln(n_C)`.

The `ln(n_C)` term is the standard one-extra-parameter BIC penalty. **Do not clip negative Q to zero.** Negative-quality leaf nodes must be allowed to lose to selecting no cluster from that branch. This is important for preventing the lower support floor from automatically emitting every small dense fluctuation.

Pass the complete node-quality dictionary through the same HDBSCAN `get_clusters(..., cluster_selection_method='eom', epsilon=0, allow_single_cluster=false)` / FOSC dynamic-programming path used by the promoted implementation. No node-specific threshold is introduced.

## 7. Candidate ranking

Rank selected successor candidates by exactly:

1. descending `Q(C)`;
2. descending `L_common(C)`;
3. descending ordinary HDBSCAN stability on the successor hierarchy;
4. descending member count;
5. deterministic family ID.

No rank fusion with recurrent-EOM, v31, v19, wavelet, drift, background contrast, or any other score is allowed.

## 8. Pretruth freeze

Before opening hidden known-shower labels, persist and SHA-256 freeze:

- exact event counts and firewall declarations;
- successor HDBSCAN settings;
- condensed-tree hash;
- every node's birth density, annual descendant counts, `L_2022`, `L_2023`, `L_common`, `logLR`, and `Q`;
- selected node IDs;
- exact candidate memberships and complete order;
- mechanism-activity status relative to the binding recurrent-EOM parent.

The implementation must first reproduce the exact binding recurrent-EOM parent memberships/order from a fresh parent fit before hidden truth can be used.

## 9. Binding GMN promotion gate

After pretruth freeze only, evaluate exact parent and successor using the already-promoted annual evaluator.

For **each** year, successor must satisfy:

- recovered@50 not lower;
- recovered@100 not lower;
- top-100 dominant precision not lower;
- MRR not lower;
- median top-500 fragmentation not higher.

Additionally:

- recovered@100 must be **strictly higher in at least one** of 2022 or 2023;
- selected membership/node solution must differ from the promoted parent (`mechanism_active=true`).

Pass token:

`PASS_RECURRENT_LOCAL_BIC_HDBSCAN_V1_GMN_DEVELOPMENT`

Otherwise:

`FAIL_RECURRENT_LOCAL_BIC_HDBSCAN_V1_GMN_DEVELOPMENT`.

The first technically valid outcome is binding.

## 10. Post-outcome rule

A FAIL permanently closes this exact architecture. It does **not** authorize changing D, 8/4 support, the logarithmic persistence statistic, BIC penalty, common-evidence formula, score clipping, rank order, HDBSCAN metric, feature scale, or gate. No SonotaCo execution follows a GMN FAIL.

A PASS authorizes only a separately frozen prospective exposed-SonotaCo comparison and a separately frozen robustness/generalization diagnostic. Those must be committed before their first outcomes.

## 11. Absolute firewall

- `blind_exclusion=[20.0,55.0]`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `sonotaco_2013_2014_access=false` during this GMN selection
- `amos_scientific_access=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `post_result_parameter_search=false`
