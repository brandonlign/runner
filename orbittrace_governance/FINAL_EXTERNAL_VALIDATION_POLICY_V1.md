# OrbitTrace final external-validation policy — v1

## Permanent scored endpoint

The only final external-generalization **scored endpoint is MAARSY 2022**.

The frozen #839 URC architecture requires two distinct annual scans. Its candidate-specific external transport therefore uses the fixed ordered pair **MAARSY 2021 as unlabeled recurrence support + MAARSY 2022 as the sole scored validation year**.

MAARSY 2021 is not a second validation endpoint. It may contribute only raw label-free detector input required by the frozen annual-recurrence mechanism. No 2021 shower truth, catalogue mapping, performance metric, selection statistic, or success criterion may be opened or computed.

No unfavorable scientific result may trigger a switch to another support year, scored year, survey, or panel.

## Preflight allowed before final-candidate declaration

A source/schema/transport-only preflight may determine:

- which raw observables are natively present;
- exact field semantics and units;
- deterministic quality-cut implementability;
- 2021 and 2022 archive availability/integrity at metadata level;
- whether the frozen target exclusion can be applied before target-sensitive processing;
- whether the frozen candidate's required observables can be reproduced exactly without proxy or imputation.

The preflight may not inspect event-level scientific values, shower labels, detector scores, candidate outputs, target-region contents, or any performance endpoint.

The 2021 support choice is frozen pre-result as the immediately preceding annual scan in the same public near-continuous MAARSY survey. It is not selected from event values or performance.

## Candidate-specific external gate must be frozen early

At `FINAL_FOR_LITERATURE_TEST` declaration, **before SonotaCo 2013/2014 scientific access and before any MAARSY event-level scientific access**, the project must freeze:

- the exact MAARSY adapter;
- every quality cut and support rule;
- the exact no-retuning parameter mapping from the GMN candidate to MAARSY;
- the exact annual recurrence mapping `(2021 support, 2022 scored)`; no pseudo-years;
- the rule restricting scientific evaluation to 2022 members/truth only;
- the external evaluation unit and known-shower mapping;
- an objective 2022 power floor;
- all external 2022 performance/effect-size gates;
- deterministic random seeds/resampling rules, if any;
- the exact PASS/FAIL/INCOMPATIBLE/UNDERPOWERED vocabulary.

Those choices may use only the frozen candidate, target-excluded GMN 2022/2023 development evidence, and schema-only MAARSY preflight information. They may not use SonotaCo final-test outcomes or MAARSY scientific values.

This timing prevents a literature-test pass from being followed by an easier external-validation definition.

## No retuning

MAARSY execution permits **zero** post-freeze changes to:

- detector parameters;
- feature definitions or weights;
- thresholds;
- support/component rules;
- family construction;
- membership rules;
- ranking;
- calibration architecture;
- annual recurrence mapping;
- success gates.

If an exact required observable, 2021 support scan, or 2022 scored scan is unavailable, the verdict is `EXTERNAL_ARCHITECTURE_INCOMPATIBLE`, not permission to invent a substitute, pseudo-year, or replacement year.

## Truth boundary

Before detector outputs are frozen, neither 2021 nor 2022 known-shower truth may be opened.

After outputs are frozen, **only 2022 truth may be opened** for the external evaluation. The 2021 support scan remains unlabeled for the entire project. Any computation of 2021 shower-recovery/performance values invalidates the external-validation claim.

## Power

The frozen external protocol must include an objective 2022 power floor capable of testing the candidate's principal claimed improvement. A panel that does not meet that floor returns `EXTERNAL_POWER_INCONCLUSIVE`.

Neither `EXTERNAL_ARCHITECTURE_INCOMPATIBLE` nor `EXTERNAL_POWER_INCONCLUSIVE` satisfies the project requirement for demonstrated generalization and neither unlocks the target.

## Required final external verdict

Only an exact preregistered `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION` satisfies the external-generalization requirement.

A scientific FAIL is final for that frozen candidate. No MAARSY-based retuning and no replacement validation dataset are allowed.

## Target boundary

The OrbitTrace target and solar-longitude 20°–55° region remain unavailable throughout both the 2021 support scan and 2022 scored validation. Only the exact external PASS may activate the separately frozen final blind-search protocol.
