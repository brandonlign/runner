# OrbitTrace v27 — fixed-membership background-odds evidence OOF ranking

## Motivation

v22–v26 preserve a broad candidate universe with enough oracle headroom to beat catalogue HDBSCAN, but strict whole-shower OOF ranking still underestimates several excellent held-out showers. v26 showed that raw expanded-membership compactness/balance is not the missing information channel.

The next physically grounded hypothesis is **local-background normalization**. A compact family can still lie inside a dense generic meteor background; catalogue HDBSCAN explicitly benefits from density contrast. OrbitTrace already contains one frozen target-free stream-vs-local-field model, B1 (#502/#801). B1 scientifically failed as a hard membership assignment rule, so v27 does **not** revive, retune, or use its `log posterior odds > 0` event-acceptance rule. It reuses only B1's already-frozen continuous posterior model as a label-free ranking feature on memberships that are already fixed.

## Frozen SonotaCo information surface

The already-frozen SonotaCo final-r4 label-free preparation contains, for each event, detector geometry plus `q, e, inc, peri, node`. The 20°–55° target interval is already absent from the frozen rows before v27 begins. v27 must use only those frozen row files; it may not reopen raw SonotaCo archives, truth, MAARSY, DMS, or OrbitTrace target information during feature construction.

## Exact B1 model reused

v27 reuses the exact B1 scientific source and its exact dependencies:
- B1 source SHA-256 `8b848cad728ad2370d1bf538b3ccc7f71d1b65c1f8d483838374aa6e12bbbb0d`;
- source-year activity padding `6°`;
- density second-neighbor ceiling `1.5` for constructing the source-year local-field competitor;
- trajectory residual ceiling `1.5` for constructing that competitor;
- B1 three-dimensional feature vector: `log1p(density_d2)`, `log1p(trajectory_residual)`, `log1p(median_D_SH)`;
- exact Southworth-Hawkins `D_SH` implementation;
- Ledoit-Wolf Gaussian stream model fitted to original other-year seed leave-one-out features;
- Ledoit-Wolf Gaussian local-field model fitted to screened same-source-year non-family events;
- observed-seed prior odds `n_source_seeds / n_screened_source_background`.

No B1 feature, covariance model, prior, activity padding, density ceiling, trajectory ceiling, orbit statistic, or weight is changed or searched.

## Sole v27 feature construction

The candidate universe, ranking inputs, and final membership remain exactly the valid v22–v26 broad hard/P19/P20 universe with exact frozen v19 membership expansion. No event is added, removed, reassigned, or used recursively.

For each family and each target year:
1. The **opposite-year pre-expansion family members** are the source seeds. At least four orbit-valid source seeds are required.
2. Fit the exact B1 stream and source-year local-field models described above, using only label-free frozen rows.
3. Take every event already present in the family's **fixed expanded membership** for the target year. Do not apply B1's target-event acceptance cutoff and do not drop a member merely because it lies outside B1's density/trajectory screens; those screens remain only part of the frozen source-background model construction.
4. Evaluate the exact B1 continuous transferred log posterior odds for every fixed target-year member.
5. Record the simple arithmetic **mean log posterior odds** across those fixed members.

The arithmetic mean is fixed because log posterior odds are additive evidence and the mean gives per-member evidence without rewarding larger families merely for having more members. No median, sum, trimmed mean, positive fraction, quantile, clipping, threshold, or alternative aggregation is evaluated.

Exactly two new label-free features are appended:
- mean B1 log posterior odds for the fixed 2013 membership;
- mean B1 log posterior odds for the fixed 2014 membership.

The original 71 v22-v25 features remain unchanged and in the same order. v27 feature dimension is exactly **73**. The failed v26 7-dimensional expanded-cohesion augmentation is not carried forward.

## Pretruth firewall

Before B1 evidence construction, v27 must reproduce the valid v22-v25 scientific payload:
- fixed membership JSON bytes exactly match the first valid v22 payload;
- derived centroid and 71-feature arrays preserve exact shapes/order and match canonical **round-to-10-decimal** fingerprints computed from the first valid v22 artifact;
- exact v19 expanded-family identities are preserved;
- zero rows occur in solar longitude 20°–55°.

The 10-decimal numeric identity is a transport-only reproducibility tolerance. The first v27 attempt, run `31422892882`, stopped before B1 evidence and before truth because recomputation differed from the valid v22 arrays only at machine precision (maximum absolute differences below `6e-14`; memberships exact). Round-to-12 remained brittle at decimal-boundary values, while round-to-10 is identical across the valid v22 artifact and the fresh runner. No scientific setting, event, family, order, or feature definition changes through this repair.

Both 73-dimensional feature matrices and their two-column B1 evidence matrices must be hash-frozen before exposed SonotaCo truth is loaded. Feature construction accepts no label/truth field.

## Ranking objective

v27 does not select a new loss or target. It reuses exactly v24's strongest balanced architecture:
- two independent exact #839 ExtraTrees regressors;
- one strict-group OOF head predicts 2013 family membership F1;
- one predicts 2014 membership F1;
- deterministic five-fold whole-shower grouping across both Sugar and HDBSCAN routes;
- exact inverse-group training weights;
- final OOF score `min(predicted_F1_2013, predicted_F1_2014)`;
- exact #839 diversity lambda `0.8`, scale `1.0`.

No model, target, fold, weighting, prediction-combiner, diversity, or fusion-weight search is allowed.

## Frozen variants and gate

Exactly two successor orders are evaluated:
1. `background_odds_two_head_quality`: diversity order from the fixed two-head minimum score on 73 features.
2. `background_odds_two_head_v19_rank_sum`: parameter-free equal-weight rank-sum between that order and exact v19 rank-sum.

Exact v19 fixed-membership order is retained as an identity control and must reproduce all four fixed v19 metrics.

PASS requires one frozen successor to beat the corresponding literature comparator in **all four** comparator/year panels: candidate macro-F1 strictly greater than literature and recovered F1>0.5 count at least equal to literature in every panel. The same robust four-panel selector used by v22–v26 chooses between the two frozen successors.

Only an OOF all-panel PASS may fit and fingerprint two full-development 73-feature annual heads. Full-fit in-sample performance is ineligible as promotion evidence. A v27 failure permanently rejects this exact B1-evidence transfer and does not authorize B1 threshold/aggregation/model tuning.

## Firewall

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region event, or protected 20°–55° content is authorized. Any protected cross-survey validation requires a separate candidate-specific pretruth protocol after an OOF PASS.
