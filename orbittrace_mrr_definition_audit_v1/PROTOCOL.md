# OrbitTrace MRR definition audit v1 — frozen protocol

## Status

**FROZEN AS AN EVALUATION-DESIGN AUDIT. THIS AUDIT CANNOT RETROACTIVELY PROMOTE, REOPEN, OR RESCUE ANY CLOSED SCIENTIFIC SUCCESSOR.**

This audit was motivated by inspection of the already-frozen Recurrent-EOM `metrics(...)` implementation after multiple candidate-rich successors independently passed every frozen recovery/precision/fragmentation gate and failed only MRR.

The purpose is not to change an outcome. It is to determine whether the current MRR implementation is an appropriate mandatory non-regression gate for future OrbitTrace method protocols.

## 1. No new truth access

This audit may use only:

1. frozen evaluator source already present in the repository; and
2. already-sealed result artifacts from completed target-excluded GMN development endpoints.

It may not open shower labels, regenerate candidates, rerun a scientific successor, access the protected OrbitTrace target region, or access SonotaCo/ASFN/EFN/AMOS/MAARSY/DMS event data.

## 2. Metric definitions

For one annual panel let `E` be the set of eligible shower labels, and for each `q in E` let `r_q` be the first rank of a positive candidate match, or undefined when the shower is not recovered.

### Current OrbitTrace conditional reciprocal-rank mean

The frozen Recurrent-EOM evaluator currently computes

`MRR_cond = mean(1 / r_q for q with defined r_q)`.

Eligible-but-unrecovered showers do not contribute to the denominator.

### Zero-filled eligible-query MRR

Define

`MRR_zero = (1 / |E|) * sum_q score(q)`

where

- `score(q) = 1/r_q` when recovered;
- `score(q) = 0` when unrecovered.

For any panel with at least one recovered shower,

`MRR_zero = MRR_cond * qualified_matches / eligible_labels`.

This audit uses only this identity and the frozen aggregate fields already emitted by the evaluator. It does not reinterpret candidate truth matches.

## 3. Formal monotonicity test

Prove directly from the current formula:

If a catalogue preserves all existing first ranks and newly recovers one previously missed eligible shower at rank `r_new`, then current conditional MRR decreases whenever

`1/r_new < MRR_cond_before`.

By contrast, zero-filled MRR strictly increases for every newly recovered shower at any finite rank if all existing first ranks are unchanged.

This is a mathematical property of the metric definitions, not an empirical method result.

## 4. Fixed empirical audit endpoint

Use the already-closed binding Recurrent-TopoModal support-mask v1 truth result only as a concrete fixed example because it preserves **exact Recurrent-EOM candidate ranks by construction** and changes only candidate membership.

Authoritative endpoint:

- workflow run `32070872999`;
- artifact `9301740793`;
- artifact digest `sha256:e2c92111294257022884f09c94a72e8c053b3bb7f5489c13ddd8517bda694dbe`;
- result file `RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_TRUTH.json`.

The endpoint remains scientifically closed regardless of this audit.

For each of its sixteen annual panels compute, separately for parent and successor:

- `eligible_labels`;
- `qualified_matches`;
- frozen `MRR_cond`;
- derived `MRR_zero = MRR_cond * qualified_matches / eligible_labels`.

Aggregate each scale (`d=1024`, `d=128`) using the same unweighted mean over its eight annual panels used by the existing aggregate MRR calculation.

Also compute pooled reciprocal mass per eligible query for each scale:

`pooled_MRR_zero = sum(MRR_cond_i * qualified_i) / sum(eligible_i)`.

No other successor is required for the primary verdict; additional closed endpoints may be reported later only as secondary diagnostics under a separately explicit complete-set rule.

## 5. Frozen audit questions

Return `AUDIT_MRR_DEFINITION_PROBLEM_CONFIRMED` iff all of the following hold:

1. source inspection confirms the frozen evaluator excludes eligible unrecovered showers from the MRR denominator;
2. the formal monotonicity derivation shows that adding a newly recovered shower can lower current conditional MRR while leaving all existing first ranks unchanged;
3. on the fixed support-mask endpoint, successor qualified recovery is strictly higher than parent at both sparse scales;
4. on that endpoint, current conditional MRR is lower than parent at both sparse scales;
5. on that endpoint, zero-filled MRR is higher than parent at both sparse scales, using both:
   - mean of panelwise zero-filled MRR; and
   - pooled reciprocal mass per eligible query.

Otherwise return `AUDIT_MRR_DEFINITION_PROBLEM_NOT_CONFIRMED`.

## 6. Interpretation constraints

A confirmed audit means only:

- the current conditional-MRR non-regression gate confounds coverage with ranking in a non-monotone way when the number of recovered eligible showers changes;
- future OrbitTrace protocols should not automatically reuse conditional MRR as a mandatory non-regression gate when comparing catalogues with different recovery counts;
- a future protocol may pre-freeze a zero-filled eligible-query MRR or another independently justified joint retrieval/ranking metric before testing a new scientific successor.

A confirmed audit does **not**:

- turn any previous FAIL into PASS;
- authorize tuning a closed successor;
- authorize protected target-region access;
- prove that TopoModal is globally superior;
- establish a new champion.

Every prior binding verdict remains binding under the metric contract under which it was run.

## 7. Provenance

Persist the audit script, exact source/result hashes, all sixteen derived panel values, scale aggregates, the formal inequality, and the final audit verdict. No scientific method parameter or candidate membership may be changed by this branch.
