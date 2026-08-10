# OrbitTrace v28 — missingness-aware frozen-B1 evidence OOF ranking

## Pre-result basis

The truth-free exact-B1 census (PR #960; run 31424328582; artifact 9076629789; digest `sha256:da1bfcb566ce4b20150e06fb2a0d58d4a4ce15dc78088830f072e724fa9e7d42`) established before any v28 literature evaluation that B1 evidence is valid in both years for 61.80% of Sugar-route families and 67.69% of HDBSCAN-route families, and in at least one year for 73.78% / 78.60%. Across all 992 family-years, every non-PASS case is exactly one of two frozen B1 applicability states: `<4 screened local-field events` or `<4 source seeds`. No other failure type occurred.

Exact all-family v27 remains a pretruth applicability no-go. v28 does not relax B1, drop an inapplicable family, or alter any membership. It makes B1's already-observed applicability state explicit.

## Immutable pretruth inputs

v28 consumes only two immutable, pretruth artifacts before labels:
1. first valid v22 artifact 9074344777, digest `sha256:d070ce8e17c56d6a17b0e74377ef19d15b9422ca67a704f0b05c54b0715b1ae1`, containing the exact 71 label-free features, candidate centroids, and fixed expanded memberships;
2. truth-free B1 applicability-census artifact 9076629789 above, containing exact B1 PASS continuous mean log-odds values and exact applicability failure states for every family/year.

Both artifacts explicitly record no target/protected-data use in their pretruth payloads. v28 does not regenerate or reinterpret B1.

## Sole feature transformation

For each family and each year, append exactly three values in this order:
1. `mean_log_odds_or_zero`: exact census mean B1 log posterior odds when status is PASS; otherwise `0.0`;
2. `low_local_field`: `1.0` iff census status is `LT4_SCREENED_LOCAL_FIELD`, else `0.0`;
3. `low_source_seeds`: `1.0` iff census status is `LT4_SOURCE_SEEDS`, else `0.0`.

`0.0` is the fixed neutral log-odds placeholder; the two explicit failure-state indicators make missing evidence distinguishable from observed neutral evidence. No imputation value, missingness code, transformation, clipping, aggregation, or feature subset is searched. Any census state other than PASS / the two preregistered failure states invalidates v28 before truth.

Two years × three values gives exactly six appended features. The original 71 features remain byte-identical and in the same order. Final dimension: **77**.

## Ranking objective

v28 reuses exactly v24's strongest fixed learning architecture:
- two independent exact #839 ExtraTrees regressors;
- one strict whole-shower OOF head predicts 2013 fixed-membership F1;
- one predicts 2014 fixed-membership F1;
- deterministic five-fold same-shower grouping across both Sugar/HDBSCAN routes;
- exact inverse-group weights;
- fixed score `min(pred_2013,pred_2014)`;
- exact #839 diversity lambda `0.8`, scale `1.0`.

No target, model, fold, weight, combiner, diversity, membership, candidate, or fusion-weight search is allowed.

Exactly two successor orders are evaluated: `missing_b1_two_head_quality` and parameter-free `missing_b1_two_head_v19_rank_sum`. Exact v19 is a mandatory fixed-membership identity control.

PASS requires a single successor to beat the corresponding literature comparator on all four comparator/year panels: strictly greater macro-F1 and recovered F1>0.5 count at least equal to literature in every panel. Only an OOF all-panel PASS may fit/fingerprint full-development models; full-fit in-sample performance is ineligible.

A failure permanently rejects this exact missingness-aware B1 representation and does not authorize relaxing B1, changing the neutral placeholder, adding background-count features, or searching missingness encodings.

## Firewall

SonotaCo 2013/2014 remains exposed development-only. v28 pretruth construction contains no raw archive, MAARSY, DMS, OrbitTrace target, or target-region access. Any protected validation remains separately preregistered and unauthorized here.
