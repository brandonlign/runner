# OrbitTrace recurrent-EOM exposure-likelihood v1 — frozen protocol

## Status

Frozen before implementation and before the first scientific outcome.

Parent: exact recurrent-EOM HDBSCAN v1 on target-excluded GMN 2022+2023. This successor leaves GEO6, HDBSCAN, the pooled condensed hierarchy, annual EOM normalization, recurrent stability `E_rec=min(E_2022,E_2023)`, and the final ranking convention unchanged. Its sole scientific change is the scalar stability used inside HDBSCAN EOM branch selection.

Firewall remains binding: protected `[20°,55°]`, OrbitTrace target information/events, SonotaCo scientific values, AMOS, MAARSY and DMS are inaccessible. Complete parent/successor catalogues must freeze before shower truth. First technically valid GMN result is binding. No post-result alternative exposure model, local exposure estimate, likelihood transform, prior, threshold, blend, ranker, HDBSCAN parameter or rescue is allowed.

## Exact parent

- recurrent kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- recurrent runner blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding run `31827903547`, artifact `9229646556`;
- binding prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`;
- binding result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`;
- candidate count `2,097`.

A fresh normal HDBSCAN fit with exact parent settings must reproduce the binding recurrent selected-node set and exact candidate membership/order before the successor is interpreted. Otherwise the run is an engineering no-result.

## Motivation

Recurrent-EOM normalizes annual density-persistence mass by each year's total accessible catalogue size. However, it does not explicitly test whether the **membership composition of a hierarchy node** is statistically compatible with the survey's overall annual exposure split. A branch can therefore obtain nonzero persistence in both years while being far more concentrated in one year than the survey-wide observation ratio would predict.

For a physical stream observed by the same survey in two years, recurrence should mean not only persistence in both years but annual membership compatible with the exposure opportunity supplied by those years. This successor inserts a parameter-free binomial likelihood-ratio coherence term into EOM selection.

This is distinct from closed lanes: it does not change the hierarchy/core geometry, does not fit separate annual clusters, does not compare physical drift models, does not use local kNN/MST mixing, and does not alter the annual EOM combiner itself.

## Exposure likelihood ratio

Let total accessible event counts be the exact target-excluded parent counts:

- `N_2022 = 315024`;
- `N_2023 = 423658`;
- `N = 738682`.

Define the fixed survey exposure probability

`p = N_2022 / N`.

For every condensed-tree cluster node C, let descendant point counts be `n_1(C)` for 2022 and `n_2(C)` for 2023, with `n=n_1+n_2`.

Under the fixed-exposure recurrence model H0, annual identity follows Binomial(n,p). Under the saturated composition model H1, the maximum-likelihood annual probability is `p_hat=n_1/n`.

Ignoring the common binomial coefficient, define

`log LR(C) = n_1 log(p) + n_2 log(1-p) - [ n_1 log(p_hat) + n_2 log(1-p_hat) ]`,

with the standard convention `0 log 0 = 0`.

The parameter-free exposure-coherence weight is

`W_exp(C) = exp(log LR(C))`.

Mathematically `0 <= W_exp <= 1`; it equals 1 only when the node's annual fraction equals the global exposure ratio exactly (up to integer counts), and decreases as the node becomes exposure-incompatible. Floating-point underflow to exact zero for overwhelming incompatibility is accepted as the mathematical limit; no floor or clipping is permitted.

The sole successor stability is

`E_exp(C) = E_rec(C) * W_exp(C)`.

No p-value conversion, chi-square approximation, beta-binomial prior, pseudocount, local/seasonal exposure estimate, exponent, additive term, or fitted coefficient is permitted.

## EOM extraction and ranking

Run the exact parent HDBSCAN EOM tree optimization with `E_exp` substituted for recurrent stability. Root exclusion and label assignment remain exact parent behavior.

To isolate branch selection, successor ranking remains the original recurrent-EOM convention using the selected node's **original E_rec**, not the new exposure weight:

1. descending original recurrent stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic membership ID, prefix `REOMEXP1` only for provenance.

No post-filter or reranker is permitted.

## Pretruth invariants

Before shower truth opens, the runner must prove:

1. exact event counts `315024 / 423658 / 738682` and inclusive protected exclusion;
2. exact recurrent source identity;
3. fresh normal HDBSCAN reproduces binding recurrent selected nodes and complete 2,097 candidate membership/order;
4. bottom-up annual descendant counts sum exactly to each node's descendants;
5. every `W_exp` and `E_exp` is finite and in its mathematical range;
6. successor selected nodes, memberships, original recurrent scores and exposure weights are persisted and SHA-frozen before truth.

Any failure is an engineering no-result.

## Binding development gate

Use exact recurrent-EOM annual evaluation semantics. PASS requires all:

1. successor selected-node set differs (`mechanism_active=true`);
2. recovered@100 strictly improves in at least one year and is not lower in the other;
3. recovered@50 is not lower in either year;
4. top-100 dominant precision is not lower in either year;
5. MRR is not lower in either year;
6. median top-500 fragmentation is not higher in either year.

@25, @500, qualified matches, candidate count and exposure-weight distribution are reporting-only.

PASS: `PASS_RECURRENT_EOM_EXPOSURE_LR_V1_GMN_DEVELOPMENT`.
FAIL: `FAIL_RECURRENT_EOM_EXPOSURE_LR_V1_GMN_DEVELOPMENT`.

A FAIL permanently closes this exact global-exposure likelihood-ratio stability. No local-exposure, alternate null, prior, transform, blend or reranking rescue is authorized from the outcome. A PASS authorizes one separately frozen direct exposed SonotaCo benchmark; it does not authorize protected target access.