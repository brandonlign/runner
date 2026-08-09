# P14 no-retuning external validation — MAARSY 2020/2021

## Status / eligibility

Protocol-only reservation frozen before any P14 matched Sugar/HDBSCAN truth or superiority result exists. It may execute only after exact verdict `PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS`, with mandatory sparse superiority separately against HDBSCAN and Sugar in both SonotaCo 2023 and 2025. Broad-only superiority is insufficient.

No MAARSY scientific value is opened by this reservation. Solar longitude 20°–55° and all OrbitTrace target information remain inaccessible.

## Fixed external panel and transport

External panel is exactly **MAARSY 2020 and 2021**. Years may not be replaced, subsetted, augmented, or selected after performance is known.

Survey transport is the already-source-audited adaptation of immutable pre-existing MAARSY transport logic:
- exact Zenodo record/file identity and archive size/MD5 remain fixed;
- exact native geometry fields `sun_lon`, `slat`, `slon`, `vels` and native six-column `kepler` orbit representation are used;
- solar longitude 20°–55° is excluded before radiant/speed values are retained;
- deterministic fixed 10°-bin identity cap remains 10,000 events per bin;
- years are exactly 2020/2021, stopping before the first 2022 member;
- no schema/value-dependent feature substitution or threshold adjustment is allowed.

If an exact frozen scientific observable cannot be represented from the MAARSY schema, verdict is `ARCHITECTURE_INCOMPATIBLE` rather than substituting another quantity or retuning the method.

## Frozen P14 method

P14 remains dual-output:

1. **Primary discovery core:** exact promoted recurrent-core construction plus support-safe multiplicity total-order semantics.
   - `EPISODE_SIZE=128` is immutable.
   - Every multiplicity-scorable core uses exact frozen v8 scoring/ranking.
   - If a recurrent core lacks the required 128-event local support, it keeps its exact core identity, receives no fabricated multiplicity score, and ranks after all scorable cores in stable lexical `family_id` order.
   - Any other scoring exception is fatal.
2. **Secondary characterization halo:** exact P12 halo transported without retuning. Halo membership cannot create, delete, reorder, rescue, or qualify a core discovery.

P14 development artifact `9041190744` proved the support-safe fallback is vacuous on target-excluded development: 226/226 families scorable and 452/452 episodes exactly 128, while P13 core and exact P12 halo hashes/endpoints remain unchanged.

All inherited P12 scientific machinery remains exact wherever required: drift-conditioned observation representation, exact orbital view, deterministic cross-year construction, P3 `0.5` seed-floor minimum and `0.10` negative-tail budget, P8 finite-sample rank from that `0.10`, P9 reciprocal reliability, P4/P10 geometry, P11 density contrast, responsibility rule, no recursive growth, no halo reranking, no parameter search.

## Pretruth firewall

Before any MAARSY known-shower label value is indexed, freeze/hash:
- exact 2020/2021 target-excluded event universes;
- archive/source/schema/unit identities and transformations;
- recurrent core families/event IDs;
- P14 complete core order plus exact scored/unscorable support audit;
- exact P12 halo memberships;
- all model/cross-fit/density/drift/decision payloads used by the transported method;
- proof no 20°–55° event entered candidates, backgrounds, families, episodes, folds, scores, endpoints, checkpoints, or truth universe.

No external truth may feed back into family generation, membership, support eligibility, ranking, or thresholds.

## Power classification

Panel is power-eligible only if, after frozen target exclusion and before performance interpretation:
- at least **5 known-shower labels have >=4 usable events in each of 2020 and 2021**; and
- P14 produces at least **5 recurrent core families**.

Otherwise verdict is `POWER_INCONCLUSIVE_MAARSY_2020_2021`, not pass/fail, with no target authorization and no MAARSY-specific retuning.

## No-retuning generalization gates

For a power-eligible panel:

### Core discovery integrity
- exact P14 core construction/rank completes without integrity/firewall violation;
- immutable core seeds are preserved;
- at least one externally truth-qualified recurrent shower is recovered by the core;
- no halo event affects core qualification/recovery/rank;
- P14 support-safe ranking obeys exact 128-event semantics, with no fabricated score and every unscorable core after every scored core.

### Halo characterization generalization
On the same eligible external truth set for core and halo:
- halo macro-F1 >= core macro-F1 + **0.08**;
- for externally large showers (same frozen development definition, total usable truth members >=100 when nonempty), halo mean recall >= **1.5×** core mean recall;
- when that large subset is nonempty, halo mean precision >= **0.85**;
- if large subset is empty, those two large-shower gates are N/A rather than manufactured PASS; core-discovery and macro-F1 gates remain mandatory.

Final power-eligible PASS is `PASS_P14_MAARSY_2020_2021_NO_RETUNING_EXTERNAL`; otherwise `FAIL_P14_MAARSY_2020_2021_NO_RETUNING_EXTERNAL`.

## Downstream authorization

Only exact P14 matched PASS **and** exact MAARSY external PASS authorize activation of the separately frozen final blind OrbitTrace search. Matched FAIL, external FAIL, power-inconclusive, architecture-incompatible, or any integrity/firewall failure leaves target access forbidden.
