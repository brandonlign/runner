# P18 no-retuning external-validation addendum — MAARSY 2020/2021

## Status

Protocol-only external freeze before any P17/P18 matched truth or matched superiority result and without MAARSY event-value or target access.

P18 inherits the already-preregistered MAARSY design without changing panel, transport, power floor, effect-size gates, or firewall:

- exactly MAARSY 2020 and 2021;
- exact preaccess transport: original blob `f563ca63e169e6ddfe846219d8f00384f3451797`, adapter blob `bbf71f190ca128e3e24f71900fefbd1472cdacb6`, source-audit run `31325401462`, generated transport SHA256 `3e0bcc3db805f60310ec9b01d6d48f76b29544780119c05e71fc225c04e3fe48`;
- fixed 10°-bin identity cap 10,000 events/bin;
- solar longitude 20°–55° excluded before scientific values are retained;
- power eligibility: at least 5 truth labels with >=4 usable events in each year and at least 5 recurrent cores;
- underpowered remains `POWER_INCONCLUSIVE_MAARSY_2020_2021`, distinct from scientific failure;
- on a power-eligible panel, exact reported halo macro-F1 must exceed immutable core macro-F1 by >=0.08;
- when the externally large-shower subset is nonempty, exact reported-halo recall must be >=1.5x immutable core recall and exact reported-halo precision must be >=0.85;
- all inherited discovery/integrity/information-parity/firewall gates remain mandatory.

## P17/P18 semantics fixed externally

- Core family existence/qualification and rank remain exact P14/P17 primary semantics.
- P15 `MIN_DIRECTION_NEGATIVES=128` remains immutable; `<128` directions contribute zero proposals and are unavailable.
- P17 reciprocal-support closure remains fail-closed: if reciprocal P3 reliability is absent only because the reciprocal direction is pretruth support-unavailable, reciprocal reliability is false; P9 cannot pass and that supported direction contributes zero proposals. Missing reciprocal evidence without exact unavailable-ledger proof remains fatal.
- P18 reported membership is exactly the resulting frozen P17 halo for the same stable family ID.
- P18 cannot add a detector proposal, fill unavailable evidence, seed growth, alter rank, or change a family correspondence.
- P17 closure ledger/hash and P18 core↔halo correspondence/report-membership hashes must freeze before any MAARSY truth value is indexed.

No MAARSY result may change years, transport, thresholds, support rule, reciprocal rule, family generation, rank, membership source, power floor, or effect-size gate.

## Authorization

External execution requires immutable evidence that:
1. P17 development vacuity passed exclusively from the admissible artifact-only canonical P15/P12/P13 evidence, with no post-result tolerance;
2. P18 canonical development identity remains exact P16 identity (226 families, 17,238 pre-existing halo additions, core SHA `12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c`, halo SHA `f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3`);
3. both P17 matched checkpoints froze before truth and P18 was transformed from them before truth;
4. the fixed matched evaluator returns `PASS_P18_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS`.

A passing external verdict is exactly `PASS_P18_MAARSY_2020_2021_NO_RETUNING_EXTERNAL`; otherwise `FAIL_P18_MAARSY_2020_2021_NO_RETUNING_EXTERNAL`, `POWER_INCONCLUSIVE_MAARSY_2020_2021`, or `ARCHITECTURE_INCOMPATIBLE` as preregistered.

Only exact P18 matched PASS plus exact `PASS_P18_MAARSY_2020_2021_NO_RETUNING_EXTERNAL` can satisfy the methodology/generalization prerequisites for final Stage A. This addendum itself authorizes no target access.
