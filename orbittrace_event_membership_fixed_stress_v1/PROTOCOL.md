# Fixed-policy repeat-fold stress for #846

This protocol is frozen before the scientific result of the **final admissible** #846 execution is known.

The two earlier #846 runs `31343806656` and `31344761936` were invalidated pre-result by source-level same-shower fold-grouping issues and are permanently inadmissible regardless of outcome. The only admissible #846 scientific source is final corrected commit `e5733a57488b7b8dff26c15ff76f679810efac9c`, executed as run `31344902186`.

If and only if that final corrected #846 run returns `PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY`, the exact one policy selected by #846's preregistered selector (model, probability threshold, and additions/core cap) is eligible for this stress. No alternative policy from the #846 grid may be substituted.

The final corrected grouping changes **only fold-group identity** while preserving #846's original event-correctness target:

- every qualified hard core is grouped by its unchanged #846 target shower identity;
- every nonqualified near-miss is grouped by its best eligible known-shower association solely for fold separation;
- fragments with no eligible association remain family-specific background groups;
- the wrapper fails closed if a qualified target does not equal its fold-group identity or if fragments sharing one shower association do not share one group.

No event target, feature, model, weight, threshold, cap, membership rule, feasibility gate, P12 assignment, hard core, data row, or target-firewall rule is changed by this correction.

## Stress design

The selected policy is retrained/evaluated under five new deterministic whole-shower grouped partitions, identified by fixed salts:

- `URC-EVENT-STRESS-A`
- `URC-EVENT-STRESS-B`
- `URC-EVENT-STRESS-C`
- `URC-EVENT-STRESS-D`
- `URC-EVENT-STRESS-E`

For each salt, all P12 additions attached to cores with the same final corrected shower group remain in one fold. The fold algorithm remains count-balanced; only the deterministic within-count hash ordering changes by salt.

The exact selected model class/hyperparameters, probability threshold, cap, feature set, group-balanced weighting, P12 assignments, v8 core, target exclusion, and evaluation metrics are unchanged. There is no model, threshold, cap, salt, or gate search.

## PASS gate

Every one of the five fixed panels must independently satisfy the original #846 feasibility bars:

- corrected qualified known streams >=95;
- corrected recovery@100 >=59;
- corrected top-100 dominant precision >=0.668;
- historical membership macro F1 >=0.30;
- annual all-shower mean-F1 gain over the v8 core >=+0.015 in 2022;
- annual all-shower mean-F1 gain over the v8 core >=+0.015 in 2023.

The aggregate verdict is `PASS_EVENT_LEVEL_P12_FIXED_GROUP_STRESS` only if all five panels pass. Otherwise the selected #846 policy fails robustness and cannot challenge the original #839 membership under final selection freeze #848. No failed salt may be dropped or replaced.

## Activation

This source contains no execution marker. A one-file `RUN.md` child may be created only after final corrected run `31344902186` has scientifically passed. If that run fails, this stress remains dormant permanently.

The authoritative workflow is independently pinned to corrected source commit `e5733a57488b7b8dff26c15ff76f679810efac9c` and run `31344902186`; this protocol correction changes provenance text only and does not alter the already-frozen executable stress semantics.

No SonotaCo 2013/2014, MAARSY scientific values, target-region events, OrbitTrace coordinates/members/identity, or prior target recovery information are accessed by this protocol or stress.
