# OrbitTrace v6 — frozen SonotaCo 2018 prospective result

Authoritative scientific workflow: `31155550264`

Scientific job: `92794141790`

Artifact: `8985017321`

Scientific source commit: `d8258581af143308495bd97bedcc142abbbd951a`

The body below is copied verbatim from the completed scientific artifact; no metric, gate, threshold, or verdict is edited by this freeze step.

# OrbitTrace v6 SonotaCo 2018 prospective validation

Verdict: **`FAIL_V6_SONOTACO_2018_PROSPECTIVE_VALIDATION`**

## Continuous ranking

- v3 weak AUROC: **0.779039**
- Brown-family weak AUROC: **0.770711**
- fixed4 weak AUROC: **0.787687**
- v3 - Brown: **+0.008328**

## Frozen v6 decision

- pooled FPR: **0.048295**
- worst-sector FPR: **0.065104**
- recall k=4/6/8/12: **0.128788 / 0.469697 / 0.712121 / 0.893939**

## Predecessor references (first 128 nulls, denominator 129, nominal alpha .05)

- fixed4 recall k=4/6/8/12: **0.181818 / 0.409091 / 0.583333 / 0.803030**
- Brown recall k=4/6/8/12: **0.060606 / 0.348485 / 0.689394 / 0.886364**
- fixed4 FPR: **0.045928**
- Brown FPR: **0.041667**

## Gates

- PASS — `parser_all_pass`
- PASS — `eligibility_universe_exact`
- PASS — `frozen_scoring_sources_self_test`
- PASS — `calibration_panels_exact_512_and_prefix128`
- PASS — `v6_pvalues_exact_denominator_513_grid`
- PASS — `predecessor_pvalues_exact_denominator_129_grid`
- PASS — `v3_weak_auc_at_least_brown`
- PASS — `v6_pooled_fpr_at_most_0055`
- PASS — `v6_worst_sector_fpr_at_most_008`
- FAIL — `v6_k4_recall_at_least_predecessor_fixed4`
- PASS — `v6_k6_within_003_of_predecessor_brown`
- PASS — `v6_k8_within_003_of_predecessor_brown`
- PASS — `v6_k12_within_003_of_predecessor_brown`
- PASS — `v6_decision_rule_exact_17_15_122_over_513`

This is the one preregistered SonotaCo 2018 prospective execution. No same-corpus retuning is authorized.

A passing result validates the sparse-episode detector; it does not by itself establish blind catalogue rediscovery or OrbitTrace target recovery.
