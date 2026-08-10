# OrbitTrace final external-validation policy — v1

## Permanent panel

The only final external-generalization panel is **MAARSY 2022**.

No unfavorable scientific result may trigger a switch to another external survey or year. The panel is validation data, never development data.

## Preflight allowed before final-candidate declaration

A source/schema/transport-only preflight may determine:

- which raw observables are natively present;
- exact field semantics and units;
- deterministic quality-cut implementability;
- year/archive availability and integrity;
- whether the frozen target exclusion can be applied before any target-sensitive processing;
- whether the final candidate's required observables can be reproduced exactly without proxy or imputation.

The preflight may not inspect event-level scientific values, shower labels, detector scores, candidate outputs, target-region contents, or any performance endpoint.

## Candidate-specific external gate must be frozen early

At `FINAL_FOR_LITERATURE_TEST` declaration, **before SonotaCo 2013/2014 scientific access and before MAARSY scientific access**, the project must freeze:

- the exact MAARSY transport/adapter;
- every quality cut and support rule;
- the exact no-retuning parameter mapping from the GMN candidate to MAARSY;
- the external evaluation unit and known-shower mapping, if labels are part of evaluation;
- an objective power floor;
- all external performance/effect-size gates;
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
- success gates.

If an exact required observable is unavailable, the verdict is `EXTERNAL_ARCHITECTURE_INCOMPATIBLE`, not permission to invent a substitute.

## Power

The frozen external protocol must include an objective power floor capable of testing the candidate's principal claimed improvement. A panel that does not meet that floor returns `EXTERNAL_POWER_INCONCLUSIVE`.

Neither `EXTERNAL_ARCHITECTURE_INCOMPATIBLE` nor `EXTERNAL_POWER_INCONCLUSIVE` satisfies the project requirement for demonstrated generalization and neither unlocks the target.

## Required final external verdict

Only an exact preregistered `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION` satisfies the external-generalization requirement.

A scientific FAIL is final for that frozen candidate. No MAARSY-based retuning and no replacement validation dataset are allowed.

## Target boundary

The OrbitTrace target and solar-longitude 20°–55° region remain unavailable throughout MAARSY validation. Only the exact external PASS may activate the separately frozen final blind-search protocol.
