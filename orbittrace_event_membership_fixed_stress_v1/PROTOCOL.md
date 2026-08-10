# Fixed-policy repeat-fold stress for #846

This protocol is frozen before the scientific result of #846 is known.

If and only if #846 returns `PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY`, the exact one policy selected by #846's preregistered selector (model, probability threshold, and additions/core cap) is eligible for this stress. No alternative policy from the #846 grid may be substituted.

The exact #846 scientific source is commit `99fdc0d21e91b68496adeddc21b2837093473ed9`.

## Stress design

The selected policy is retrained/evaluated under five new deterministic whole-shower grouped partitions, identified by fixed salts:

- `URC-EVENT-STRESS-A`
- `URC-EVENT-STRESS-B`
- `URC-EVENT-STRESS-C`
- `URC-EVENT-STRESS-D`
- `URC-EVENT-STRESS-E`

For each salt, all P12 additions attached to cores with the same dominant known shower remain in one fold. Ambiguous/background groups retain their family grouping. The fold algorithm remains count-balanced; only the deterministic within-count hash ordering changes by salt.

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

This source branch contains no execution marker. A one-file `RUN.md` child may be created only after #846 has scientifically passed. If #846 fails, this stress remains dormant permanently.

No SonotaCo 2013/2014, MAARSY scientific values, target-region events, OrbitTrace coordinates/members/identity, or prior target recovery information are accessed by this protocol or stress.
