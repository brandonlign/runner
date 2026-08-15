# OrbitTrace permanent train / validation / final-test split v1

## Status

**FROZEN GOVERNANCE.** This document is created after the binding GMN development PASS of density-synchronous recurrent-EOM (#1263) but **before any AMOS 2023/2024 event-level scientific data have been accessed**. It does not change any historical result or reclassify an exposed dataset as pristine.

The purpose is to stop sequential dataset shopping and version-by-version movement of the evaluation goalposts. From this point forward, methodology work has exactly three roles: development, exposed validation, and one sealed final external test.

## Scientific firewall

The protected OrbitTrace solar-longitude interval **[20 deg, 55 deg] inclusive remains inaccessible** before all method labels, candidate generation, ranking, evaluation, or split assignment that uses scientific variables. OrbitTrace target information/events, MAARSY scientific data, and DMS scientific data remain inaccessible.

No rule in this document authorizes target access.

## 1. TRAIN / DEVELOPMENT — GMN 2022 + 2023

The permanent method-development panel is the existing target-excluded **GMN 2022 + 2023** population.

This panel is already exposed and is the only place where method architecture may be iterated.

Allowed:
- scientifically motivated new successors;
- implementation/debugging and synthetic audits;
- candidate-generation/ranking diagnostics;
- known-shower evaluation under the existing target-excluded GMN evaluator;
- rejection of failed methods and prospective design of later distinct methods.

Required:
- every successor is frozen before its first technically valid GMN outcome;
- every failure remains preserved;
- no result-informed parameter/threshold/weight/feature rescue of a failed frozen version;
- density-synchronous recurrent-EOM (#1263) is the current GMN development champion until prospectively beaten.

A method that fails its frozen GMN gate **does not reach validation**.

## 2. VALIDATION — SonotaCo 2013 + 2014

The permanent validation panel for future successors is **SonotaCo 2013 + 2014**.

SonotaCo 2013/2014 is explicitly **EXPOSED DEVELOPMENT / VALIDATION ONLY**. It is not external validation and must never be described as pristine or independent generalization.

Purpose:
- reject GMN-specific overfitting before consuming the sealed final external test;
- compare a GMN-passing frozen method against the appropriate fixed parent and frozen literature comparators on a second survey;
- provide one consistent validation role instead of searching for a new survey after each result.

Rules:
- a successor must first pass its frozen GMN development gate before SonotaCo execution;
- the exact SonotaCo validation protocol/comparators for that successor must be frozen before opening that successor's SonotaCo outcome;
- a SonotaCo failure is accepted; no threshold, HDBSCAN parameter, weight, transform, subset, ranking, or fusion rescue of that exact version is allowed;
- a later scientifically distinct successor may return to GMN development, but it starts a new frozen version;
- SonotaCo results are always labeled development/validation evidence, never external validation.

### Grandfathered #1263 exception

Density-synchronous recurrent-EOM #1263 was frozen under an earlier protocol that explicitly stated that it would **not receive a post-hoc SonotaCo benchmark**. That promise remains binding. This governance does not retroactively run #1263 on SonotaCo or rewrite its history.

For future successors, SonotaCo is the permanent validation panel. If no later successor legitimately clears both GMN development and SonotaCo validation, #1263 may remain the final candidate because it was independently frozen before any AMOS access.

## 3. FINAL TEST / EXTERNAL VALIDATION — AMOS 2023 + 2024

The only sealed final external test is **AMOS 2023 + 2024**, using the already-requested complete solved multi-station population and the existing target-exclusion / staged-access principles.

AMOS remains scientifically untouched at the time of this freeze.

Rules:
- AMOS is not used for method ideation, threshold choice, feature choice, HDBSCAN settings, ranking choice, or successor selection;
- no AMOS event-level geometry or shower label is opened during ongoing methodology development;
- once methodology development is explicitly closed, exactly one final selected method is frozen for the AMOS test;
- its complete candidate/rank payload is frozen before AMOS shower labels are opened;
- the first technically valid AMOS outcome is binding;
- after AMOS is opened, **no method rescue or new version may be justified using AMOS outcomes**;
- if the final method fails AMOS, the scientific conclusion is that external generalization was not established. The response is not to search sequentially for another external survey.

The earlier recurrent-EOM v1 AMOS protocol in PR #1244 remains preserved unchanged as historical preregistration. It must not be independently executed in a way that consumes AMOS before the final-method test. If multiple already-frozen comparators are evaluated when AMOS eventually opens, all pretruth candidate/rank outputs must be frozen before any AMOS labels are revealed.

## Datasets that are NOT test sets

The following are permanently excluded from the role of a new pristine test for this lineage:

- **GMN 2024 + 2025:** repository history established prior target-excluded scientific and known-shower/F1 exposure in PR #453 / run `31235104333`; later PRs #552, #578, #584 and #587 explicitly invalidated this panel as a prospective holdout.
- **GMN 2019–2025 generally:** earlier OrbitTrace methodology work consumed substantial target-excluded event/label information across these years. They may be historical diagnostics only, not newly relabeled pristine test data.
- **GMN 2020 + 2021:** already used in the recurrent-EOM retrospective transfer experiment.
- **ASFN 2018 + 2019:** already consumed by the binding recurrent-EOM pristine validation and is now a historical negative diagnostic, not a fresh test for successors.
- **EFN 2017 + 2018:** geometry/hierarchy has already been observed; shower labels remain sealed, but the panel cannot be pristine for successors designed afterward.
- **SonotaCo 2013 + 2014:** validation/development only by definition.
- any newly discovered survey selected because GMN/SonotaCo/AMOS produced an unfavorable result: forbidden dataset shopping.

## Permanent workflow

For every future successor after #1263:

1. **Design + freeze on scientific grounds.**
2. **Run GMN 2022/2023 development.** If FAIL, preserve and stop that version.
3. If GMN PASS, **freeze its SonotaCo 2013/2014 validation protocol before outcome**.
4. Run SonotaCo validation. If FAIL, preserve and stop that version. If PASS, it may challenge the current final candidate.
5. Continue development only on GMN; never use AMOS while choosing among methods.
6. When methodology development is explicitly closed, select one final method.
7. **Freeze and run AMOS 2023/2024 once.**
8. Accept PASS or FAIL. No post-test rescue and no replacement-survey hunt.
9. Only after all required scientific gates and the separate protected-target firewall authorize it may any final OrbitTrace target procedure occur.

## Interpretation

This is a conventional train / validation / test structure adapted to a two-year recurrence detector:

- **Train/development:** GMN 2022/2023.
- **Validation:** SonotaCo 2013/2014 (exposed; selection aid only).
- **Final test:** AMOS 2023/2024 (sealed external validation).

It is intentionally simpler than the prior sequence of survey-specific contingencies. Historical experiments remain scientifically informative, but they no longer create additional chances for a method to pass.