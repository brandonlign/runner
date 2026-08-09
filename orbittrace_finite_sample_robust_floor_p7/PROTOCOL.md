# OrbitTrace P7 finite-sample robust held-seed floor protocol

## Status

Source/protocol-only successor after authoritative P6 scientific no-go. P7 remains fully target-excluded and may not access comparator outcomes, external-panel event values, solar longitude 20°–55°, or OrbitTrace target information.

Authoritative predecessor P6 is permanently frozen as `FAIL_SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_NO_GO` from workflow `31294809555`, artifact `9032829183` (`sha256:619d69f2c08cda4520610b8248f0ecede4a3d3e92a65e5c1d97a00ed1d05bec8`). P6 passed every substantive development gate except qualified-match non-regression: 92 versus the required v8 baseline 95.

P7 is a minimal continuation of the P3/P4/P5/P6 membership lineage, not a detector restart.

## Pretruth structural diagnosis

The P6 pretruth payload was frozen before known-shower labels were opened. Using only `p3_crossfit_pretruth.json` and `p6_decisions_pretruth.json.gz` from the immutable P6 artifact:

- 439 family-directions satisfy the inherited P3 reliability rule;
- direction negative-tail rate versus final nonseed additions has Spearman rho approximately 0.8575;
- after rank-residualizing both quantities against held-out seed count and seed floor, the correlation remains approximately 0.8014;
- the 44 directions in the highest negative-tail decile account for approximately 70.41% of all P6 additions;
- only 50/439 reliable directions have at least 19 held-out recurrent seeds, yet those 50 directions account for approximately 68.51% of P6 additions;
- 98.23% of proposal rows occur on single-family events; for directions with negative-tail >=0.05, more than 99.9% of proposal rows are single-family, so the inherited inter-family responsibility competition cannot materially regulate this high-burden regime.

These diagnostics do not use known-shower identities, per-shower endpoints, target-region events, comparator results, or external data. They show that the weakest held-out seed controls a large membership expansion in well-supported directions while the later responsibility layer is usually uncontested.

## Sole P7 scientific change

P7 preserves the exact P6 family-excluded held-fold model and the exact inherited P3 reliability decision. The original P3 reliability floor remains:

`seed_floor = minimum held-out recurrent-seed probability`.

Reliability is still defined exactly as before: at least four held-out target-year recurrent seeds, `seed_floor > 0.5`, and local-negative tail at that original minimum floor <=0.10. P7 does **not** rescue any direction that P6 considered unreliable.

For candidate membership only, P7 defines a deterministic `membership_floor` from the same held-out recurrent-seed probability vector:

- if the direction has fewer than 19 held-out recurrent seeds, `membership_floor = minimum seed probability` exactly as P6;
- if the direction has at least 19 held-out recurrent seeds, `membership_floor = second-smallest held-out recurrent-seed probability`.

The candidate must be scored by the exact same family-excluded held-fold scaler/logistic model that produced those held-out seed probabilities, as already required by P6, and must satisfy `candidate_probability >= membership_floor`.

No other scientific rule changes.

## Why 19 is fixed before P7 truth

Under exchangeability of a future true member with `n` held-out recurrent seeds and a continuous score, the probability that the future member falls below the second-smallest of the `n` seed scores is `2/(n+1)`. P3 already fixed 0.10 as the maximum acceptable local-background tail scale. P7 permits the second-order-statistic tightening only when its finite-sample exclusion probability is no larger than that inherited 10% scale:

`2/(n+1) <= 0.10`, hence `n >= 19`.

This is an order-statistic adequacy calculation, not a threshold sweep. No 18/20/other cutoff, alternate seed quantile, multiplier, additive margin, or family-specific exception may be evaluated in the primary P7 lineage.

For `n < 19`, P7 deliberately preserves the P6 minimum-seed floor so the sparse-family regime is not tightened by an under-resolved order statistic.

## Exact inherited architecture

P7 keeps unchanged:

- promoted-v8 226 recurrent families, every v8 seed, and exact multiplicity rank;
- years 2022/2023 and blind exclusion 20°–55°;
- P2 two-view features `[d_obs, D_SH]`, source-seed OAS construction, exact Southworth–Hawkins implementation, ±5° local nonseed windows, >=128 negatives/direction, equal direction/class weights, weighted StandardScaler, and L2 logistic C=1.0/lbfgs/max_iter=1000/tol=1e-10;
- P3 deterministic five-fold SHA-256 family exclusion and original minimum-seed reliability gate;
- P4 coordinate-wise held-out-seed envelope;
- P5 componentwise joint support by one actual Pareto-maximal held-out recurrent-seed vector;
- P6 same-held-fold candidate scoring and odds;
- unit background, strict winning responsibility >0.5, deterministic tie handling;
- immutable v8 seeds, no recursive growth, no refit from added members, no recentering and no reranking.

The final all-family P2 model remains provenance-only exactly as in P6 and cannot determine candidate inclusion or proposal odds.

## Frozen development gates

The exact P6 substantive gates remain unchanged:

- exact v8 baseline reproduced;
- all 226 v8 families/order and every v8 seed preserved;
- qualified known-shower matches >=95;
- recovery@100 >=58;
- top-100 dominant precision >=0.65;
- macro F1 >=0.2536657194465356;
- large-shower mean recall >=1.5x v8;
- large-shower mean precision >=0.85;
- expansion nonvacuous;
- all source, pretruth, model, decision, membership and label-dataflow firewall gates pass.

Additional P7 integrity gates require:

- `P7_ROBUST_FLOOR_MIN_SEEDS == 19`;
- the inherited P3 reliability set is unchanged;
- every reliable direction with fewer than 19 held-out seeds has `membership_floor == seed_floor`;
- every reliable direction with at least 19 held-out seeds records order-statistic rank 2 and `membership_floor >= seed_floor`;
- every surviving proposal records its `membership_floor` and has probability >= that floor;
- no previously P6-unreliable direction can propose;
- all P7 floors, proposals, conflict decisions and complete memberships are SHA-frozen before any known-shower label value is indexed.

## Governance

There is exactly one primary P7 configuration: second-smallest held-out seed probability iff `n >= 19`, otherwise the exact P6 minimum floor. No parameter search is allowed.

A genuine P7 development failure rejects this exact configuration. Any successor must be motivated by pretruth structure and frozen before another truth evaluation; the P7 cutoff or order statistic may not be altered after seeing P7 truth.

Matched Sugar/HDBSCAN comparison, MAARSY external validation and the final target-containing search remain closed unless P7 first passes every development gate. Sparse-stream superiority against both Sugar and HDBSCAN in both SonotaCo 2023 and 2025 remains mandatory before external validation.
