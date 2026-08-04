# One-shot SonotaCo 2024 confirmation of the frozen fixed-4° quartet score

Status: frozen before `024a.zip` is downloaded or any SonotaCo 2024 row, label, support count, score, p-value, fold, AUROC, false-positive rate, or recall endpoint is observed.

## Final model

The candidate is the exact post-development model frozen in PR #128: the PR #38 anchored four-event complete-link score with only the relative-solar-longitude divisor changed from 2° to **4° per distance unit**. Radiant longitude, ecliptic latitude, and geocentric speed retain their exact 2° / 2° / 2 km s⁻¹ scales. The nearest-three anchored quartet search is unchanged.

The model was chosen after the complete SonotaCo 2025 development program. Fixed 4° passed every original scientific gate on 2025, with AUROC 0.813250, FPR 0.047852 / 0.006836, and k=4 recall 0.154412 / 0.058824. It was selected in four of five held-out scale-selection folds. No further 2025 optimization is permitted after this freeze.

## Exact sources and inputs

- confirmation source SHA-256: `94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7`;
- encoded payload SHA-256: `c558141ce984f3b9d5ee5eecf7e80d3df54ce7ac0e0ac1e46ca5d84a7b7017d2`;
- baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- Mondrian scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- phase-scale source SHA-256: `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`;
- parser-v2 source SHA-256: `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b` from commit `60bbe701981256b89aaa1c9361efef2bbb2dd57e`;
- archive `024a.zip` SHA-256: `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`;
- annual member `024a/_U2_20240101_S.csv` SHA-256: `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`;
- GMN/MDC mapping audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

## Blind parser and native labels

1. Verify the archive and member hashes, ZIP CRC, safe paths, 38,793 data rows, 46-column raw header, trailing blank header cell, and 45-column effective rows.
2. Normalize only header punctuation/case. Require native solar longitude, radiant, speed, reported uncertainty, camera-count, fit-error, shower, and `dr/dv/dd` fields.
3. For each structurally valid row, parse solar longitude first and remove every row from 20.0° through 55.0° inclusive **before reading its shower token or any other feature**.
4. Define background only as blank/no-letter tokens or tokens beginning `SPO`.
5. Map a positive label only under `^([A-Z0-9]{3})_JA$` and only through one unambiguous eligible GMN/MDC code mapping. Exclude every unmatched nonbackground token; never reassign it to background.
6. Preserve the exact 2025 implemented quality rule: valid solar longitude/radiant/speed and at least two cameras. Uncertainty columns are required structurally but are not newly introduced as row-level filters.
7. Remove the frozen ESV contaminant rule from the background reservoir exactly as in the inherited baseline.

Parser continuation requires native syntax and mapped fractions at least 0.90, at least 30 native codes with 20 or more rows, at least 10,000 post-ESV background events, and at least 30 distinct labeled showers.

## Frozen episode and calibration design

- year 2024; corpus identifier `sonotaco-2024-fixed4-confirmation`;
- 128-event windows from a ±10° solar-longitude neighborhood;
- globally anchored 10° Mondrian bins;
- 128 same-survey calibration negatives per supported bin;
- 64 independent test negatives per supported bin;
- four positive replicates for k in {4,6,8,12};
- conservative rank p-values at alpha 0.05 and 0.01;
- exact fixed split statistic, radius-2.5 density, epsilon-2.5 DBSCAN, and five complex/parent folds;
- fixed seed prefixes `fixed4-confirmation-support`, `fixed4-confirmation-calibration`, `fixed4-confirmation-negative`, and `fixed4-confirmation-positive`.

At least 20 bins and 30 eligible showers are required. No source, parser, token rule, seed, bin, window, calibration count, comparator, fold, threshold, or gate may change after the archive is opened.

## One-shot confirmation gates

Every gate must pass:

1. pooled FPR <=0.060 / 0.020 at alpha 0.05 / 0.01;
2. worst 60° reporting-sector FPR <=0.120 at alpha 0.05;
3. weak-window AUROC >=0.75;
4. candidate AUROC within 0.03 of the strongest fixed comparator;
5. candidate AUROC exceeds both density and DBSCAN;
6. at least four of five fold AUROCs >=0.70, none below 0.65, all finite, and every fold nonempty;
7. recall at alpha 0.05 >=0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at alpha 0.01 >=0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing through k=4,6,8,12 at both alpha levels;
10. every parser, source, support, and blindness gate passes.

A complete pass gives `PASS_SONOTACO_2024_FIXED4_CONFIRMATION`. Any scientific failure is final for this model and will not be repaired or retuned. This run does not authorize a catalogue scan or GhostStream application.
