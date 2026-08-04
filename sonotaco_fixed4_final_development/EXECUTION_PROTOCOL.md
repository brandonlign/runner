# SonotaCo 2025 standalone fixed-4° final development execution

Status: frozen after PR #135 source equivalence passed and before any final-development score is computed.

## Exact inputs

- SonotaCo 2025 archive: `025a.zip`, SHA-256 `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`.
- GMN–MDC mapping audit: workflow `30855193522`, `audit.json` SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.
- standalone fixed4 source SHA-256 `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`.
- inherited baseline/scorer/adapter hashes remain exact.

## Fixed model

The final candidate is the PR #113 anchored nearest-three complete-link quartet score with solar-longitude separation scaled at exactly 4° per distance unit. The exact 2° formulation remains the only control. No 6°/8° view, scale family, selection, consensus, selector, fusion, or drift model is computed.

The solar-longitude blind interval 20°–55° inclusive is removed by the exact inherited adapter before labels, reservoirs, windows, scores, folds, or endpoints.

## Complete development gates

The run fails closed unless:

- every parser gate passes;
- supported bins / eligible showers are exactly 32 / 34;
- the exact original 2° FPR and k=4 recall reproduce;
- candidate pooled FPR is at most 0.060 / 0.020;
- worst 60° sector FPR at alpha 0.05 is at most 0.120;
- candidate weak AUROC is at least 0.75, within 0.03 of the strongest fixed comparator, and no more than 0.01 below the original;
- at least four fold AUROCs are at least 0.70 and none is below 0.65;
- k=4 recall is at least 0.15 / 0.05 at alpha 0.05 / 0.01;
- k=6 recall is at least 0.30 / 0.15;
- k=8 recall is at least 0.45 / 0.25;
- k=6 and k=8 recall at both alpha levels are no more than 0.02 below the original;
- recall is monotonic through k=12 at both alpha levels.

Any failed gate kills the fixed 4° final model. No repair or alternative model is authorized.

## Confirmation status

SonotaCo 2024 was prematurely exposed by PR #134 and is no longer untouched. Its observed endpoints are prohibited from changing this source, model, or gates. This run remains necessary to determine whether the final model actually passes the required standalone 2025 standard, but it cannot restore the lost untouched 2024 confirmation panel.

No GhostStream application or catalogue scan is authorized by this run.
