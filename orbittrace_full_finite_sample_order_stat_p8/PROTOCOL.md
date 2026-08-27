# OrbitTrace P8 full finite-sample 10% order-statistic membership protocol

## Status

Source/protocol-only successor after authoritative P7 scientific no-go. P8 is fully target-excluded and may not access comparator outcomes, external-panel event values, solar longitude 20°–55°, or OrbitTrace target information.

Authoritative predecessor P7 is permanently frozen as `FAIL_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_NO_GO` from workflow `31295871142`, artifact `9033122516` (`sha256:705b53bfca6a743af73d16852da3e880c28a650008c646982ff8af7560394f81`). P7 passed every substantive development gate except qualified-match non-regression: 92 versus the required v8 baseline 95.

P8 is the successor explicitly preregistered in PR #649 comment `5229911755` while P7 workflow `31295871142` was still running and before P7 truth was available. It is therefore not selected from the observed P7 endpoint.

## Pretruth structural motivation

Using only immutable P6 pretruth membership/cross-fit payloads, before P7 truth:

- 439 family-directions satisfy the inherited P3 reliability rule;
- direction negative-tail rate versus nonseed additions has Spearman rho approximately 0.8575, remaining approximately 0.8014 after rank-residualizing against held-out seed count and seed floor;
- the highest negative-tail decile accounts for approximately 70.41% of P6 additions;
- 50/439 reliable directions have enough held-out recurrent seeds for an order-statistic rank above one and account for approximately 68.51% of P6 additions;
- 27 reliable directions permit a finite-sample rank above two while remaining within the inherited 10% exclusion budget; those 27 account for approximately 61.11% of P6 additions;
- 98.23% of P6 proposal rows are single-family, so the later inter-family responsibility competition cannot regulate most of the high-burden regime.

No known-shower identities, per-shower truth endpoints, comparator results, external data, target-region events, or OrbitTrace target information enter this motivation.

## Sole P8 scientific change

P8 preserves the exact P7/P6 family-excluded held-fold model and the exact inherited P3 reliability decision. Reliability continues to be defined using the **minimum** held-out recurrent-seed probability:

- at least four held-out target-year recurrent seeds;
- minimum held-out seed probability strictly >0.5;
- fraction of local negatives scoring at or above that minimum <= `P3_NEGATIVE_TAIL_MAX = 0.10`;
- at least 128 local negatives in the frozen ±5° window.

P8 does not rescue any direction that P7/P6 considered unreliable.

For candidate membership only, let `n` be the number of held-out recurrent seeds in a reliable family-direction and let their same-held-fold model probabilities be sorted ascending. P8 fixes

`k = max(1, floor(P3_NEGATIVE_TAIL_MAX * (n + 1)))`

and sets

`membership_floor = k-th smallest held-out recurrent-seed probability`.

The candidate is scored by the exact same family-excluded held-fold scaler/logistic model and must satisfy `candidate_probability >= membership_floor` before the unchanged P4/P5 geometry and responsibility rules.

No other scientific rule changes.

## Why the rank formula is fixed

Under exchangeability of a future true member with the `n` held-out recurrent seeds and a continuous score, the probability that the future true member falls below the `k`-th smallest held-out seed score is `k/(n+1)`. P3 already froze `0.10` as its local-negative tail scale. P8 therefore takes the **largest integer order-statistic rank permitted by that already-frozen scale**, subject to retaining at least the minimum-seed floor:

`k = max(1, floor(0.10 * (n + 1)))`.

Consequences are deterministic:

- for `n < 19`, `k=1`, exactly preserving the P6/P7 minimum-seed floor in sparse directions;
- for `19 <= n <= 28`, `k=2`, exactly matching P7;
- for larger `n`, P8 uses the additional finite-sample resolution instead of fixing rank two regardless of support.

There is no alpha search, alternate quantile, multiplier, additive margin, per-family exception, or known-truth optimization. The `0.10` value is not a new P8 parameter: it is referenced directly from inherited `P3_NEGATIVE_TAIL_MAX`.

## Exact inherited architecture

P8 keeps unchanged:

- promoted-v8 226 recurrent families, every v8 seed, and exact multiplicity rank;
- years 2022/2023 and blind exclusion 20°–55°;
- P2 two-view features `[d_obs, D_SH]`, source-seed OAS construction, exact Southworth–Hawkins implementation, ±5° local nonseed windows, >=128 negatives/direction, equal direction/class weights, weighted StandardScaler, and L2 logistic C=1.0/lbfgs/max_iter=1000/tol=1e-10;
- P3 deterministic five-fold SHA-256 family exclusion and original minimum-seed reliability gate;
- P4 coordinate-wise held-out-seed envelope;
- P5 componentwise joint support by one actual Pareto-maximal held-out recurrent-seed vector;
- P6 same-held-fold candidate scoring and odds;
- unit background, strict winning responsibility >0.5, deterministic tie handling;
- immutable v8 seeds, no recursive growth, no refit from added members, no recentering, and no reranking.

The final all-family P2 model remains provenance-only and cannot determine P8 proposal inclusion or odds.

## Frozen development gates

The substantive gates are unchanged:

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

Additional P8 integrity gates require:

- every direction's recorded rank exactly equals `max(1, floor(P3_NEGATIVE_TAIL_MAX * (n+1)))`;
- every rank lies in `[1,n]`;
- whenever `k>1`, `k/(n+1) <= P3_NEGATIVE_TAIL_MAX`;
- every direction whose formula gives rank one has `membership_floor == seed_floor`;
- every proposal has probability >= its exact recorded P8 membership floor;
- no P7/P6-unreliable direction can propose;
- all P8 order-statistic floors, proposals, conflict decisions and complete memberships are SHA-frozen before any known-shower label value is indexed;
- `P3_NEGATIVE_TAIL_MAX` is the only exclusion-budget constant and P8 performs no parameter search.

## Governance

There is exactly one primary P8 configuration: the full finite-sample rank formula above. No alternate alpha, rank cap, support cutoff, quantile, multiplier, offset, family-specific exception, or threshold sweep is allowed.

A genuine P8 development failure rejects this exact configuration. Any later successor must be motivated by pretruth structure and frozen before another truth evaluation.

Matched Sugar/HDBSCAN comparison, MAARSY external validation and final target-containing search remain closed unless P8 first passes every development gate. Sparse-stream superiority against both Sugar and HDBSCAN in both SonotaCo 2023 and 2025 remains mandatory before external validation.
