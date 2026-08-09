# OrbitTrace fixed train / test / validation split v1

## Purpose

Stop consuming a new benchmark every time a successor method fails. From this point forward, OrbitTrace methodology development uses one permanent development corpus, one permanent final matched literature test, and one permanent external validation panel.

This split is chosen for scientific utility and practical comparability, not merely by avoiding every historical metadata mention. Prior scientific-result exposure matters; transport-only or metadata-only handling does not by itself disqualify a dataset.

## 1. Permanent development / training corpus

**GMN 2022 + 2023, with solar longitude 20°–55° removed before any label, score, reservoir, fold, endpoint, or diagnostic construction.**

All future architecture selection, feature choice, model choice, threshold choice, ablation, debugging, and method rejection/promotion before the final test must occur here.

This corpus is intentionally exposed development data. It may be reused across successors without pretending that each successor receives a new holdout.

The development target is not just aggregate macro-F1. Development diagnostics must preserve the actual project priorities: sparse/weak-stream recovery, qualified-family non-regression, ranking quality, precision, and failure modes that previously caused P18 and B1 to fail.

## 2. Permanent final matched literature test

**SonotaCo 2013 + 2014.**

Rationale:

- same survey family and annual-archive style as the already-built SonotaCo Sugar/HDBSCAN matched benchmark machinery, making a fair matched comparison practical;
- two consecutive years, so the recurrent/cross-year discovery problem is tested without mixing survey generations;
- materially independent of GMN development data;
- repository search before this freeze found no SonotaCo 2013 scientific-result lineage and no SonotaCo 2014 scientific-result lineage; the recent 2014/2016 work accessed metadata/history only and did not open 2014 scientific archive values;
- unlike SonotaCo 2015–2025, these years have not already been used to select or diagnose the current method family.

The 2013/2014 scientific archives, labels, comparator cluster values, and method performance must remain unopened until a successor method is frozen from GMN development alone and is explicitly declared the final candidate for literature testing.

The test is executed once for the frozen method. Sugar and catalogue HDBSCAN must be evaluated on pairwise matched event-row universes with the same information-parity disclosures and sparse/broad superiority gates frozen before truth.

**No replacement year is allowed after any 2013/2014 scientific performance value is opened.** A replacement before scientific access is allowed only for an objective structural impossibility such as a missing/corrupt official archive or an unusable required field schema, and must be frozen before any candidate replacement archive is scientifically inspected.

## 3. Permanent external validation panel

**MAARSY 2020 + 2021.**

This remains the cross-survey no-retuning generalization test. Repository history records repeated preregistrations but no MAARSY 2020/2021 scientific-value execution for the P-series/B1 line, so the panel remains reserved.

The final method is transported without parameter, threshold, feature, membership, rank, or gate retuning. If the frozen architecture requires an observable that MAARSY cannot supply faithfully, the result is architecture incompatibility rather than permission to invent a proxy after seeing the problem.

Power-inconclusive remains distinct from scientific failure, but no alternative external panel is selected because of an unfavorable observed result.

## 4. Status of previously exposed datasets

SonotaCo 2023/2025, 2015/2017, 2018, 2019, 2020, 2016, and any other scientifically exposed historical panels are **diagnostic-only**. They may be used to understand historical failures, reproduce old results, or test infrastructure, but they cannot promote a future method or replace the fixed 2013/2014 final test.

In particular, the P18 SonotaCo 2023/2025 failure is retained as a scientific no-go and may motivate broad architectural reasoning, but future numerical choices must not be optimized against that exposed benchmark.

## 5. Fixed progression

1. Develop and iterate only on target-excluded GMN 2022/2023.
2. Freeze one final candidate method and all literature-comparison gates.
3. Execute the one-time SonotaCo 2013/2014 matched Sugar/HDBSCAN test.
4. If and only if the fixed literature criterion passes, execute MAARSY 2020/2021 once with no retuning.
5. If and only if the external requirement is satisfied, proceed to the separately frozen blind OrbitTrace search.

No new benchmark year is consumed for each failed development architecture. A development failure returns to step 1 using the same GMN development corpus.

## 6. OrbitTrace firewall

The OrbitTrace target region remains solar longitude **20°–55°**. Target coordinates, target members, identity, prior recovery information, and target-containing result inspection remain prohibited until the fixed literature test and no-retuning external validation requirements are satisfied.

## Governance consequence

This protocol supersedes the previous pattern of successor-specific fresh-year reservations. Future work should optimize the method, not rotate datasets.
