# MAARSY 2022 schema-only external-compatibility preflight — v1

## Scope

This is a metadata/source-only preflight permitted by `FINAL_EXTERNAL_VALIDATION_POLICY_V1.md`. It is performed before any SonotaCo 2013/2014 scientific access, before any MAARSY event-level scientific value is opened, and before any target access.

It asks whether the frozen #839 URC architecture can be transported unchanged while keeping **MAARSY 2022 as the sole scored validation endpoint**.

No archive payload, event-level row, shower truth, detector output, or performance endpoint was inspected.

## Public schema/time-span evidence only

Public MAARSY metadata establishes:

- Zenodo record `10.5281/zenodo.15553437` identifies the public **MAARSY 2016–2024 Meteor Head Echo RCS Dataset**;
- Vierinen et al., EGU 2025, `10.5194/egusphere-egu25-18621`, describes a nearly continuous 2016–2024 catalogue with atmospheric trajectories, Doppler information, radar-cross-section estimates, and derived Keplerian orbital elements;
- Huyghebaert et al., AMT 2026, describes a 2016–2023 processed MAARSY meteor-head-echo catalogue with three-dimensional trajectories and geocentric velocities and explicitly analyzes interannual measurements.

Thus the survey provides both the required physical-observable class and adjacent annual scans including 2021 and 2022 at the dataset-description level.

## Frozen URC temporal contract

The #839 proposal architecture is intrinsically a **two-distinct-annual-scan recurrence method**:

- application input is an ordered two-year pair with distinct years;
- hard-v8 family construction uses components from both annual scans;
- P19 adds cross-year reciprocal recurrence;
- P20 matches reciprocal isolated quartets across the two annual scans and retains exact 4+4 recurrent membership.

The portable adapter may generalize literal year addressing but may not change annual-recurrence semantics, thresholds, density assumptions, family-existence rules, memberships, or ranking.

## Initial incompatibility finding

A literal single-scan interpretation of “MAARSY 2022” is incompatible with the frozen method. Splitting 2022 into pseudo-years would replace independent annual recurrence with within-year subsampling and would therefore be a scientific method change rather than transport.

That initial finding remains valid: **MAARSY 2022 alone cannot run full #839 unchanged.**

## Pre-result transport resolution

The incompatibility is resolved without changing the scored validation endpoint or the method:

- ordered detector input pair: **MAARSY 2021 + MAARSY 2022**;
- **2021 role:** permanently unlabeled recurrence-support scan only;
- **2022 role:** sole scored external-validation year;
- 2021 is the immediately preceding annual scan in the same public near-continuous survey and was selected mechanically before event-level access;
- no 2021 known-shower truth, mapping, recovery metric, performance value, selection statistic, or success criterion may ever be opened or computed;
- only 2022 candidate memberships are evaluated after all detector outputs are frozen;
- no pseudo-year, alternate support year, alternate scored year, or post-result substitution is permitted.

This preserves the exact scientific requirement that a family demonstrate annual recurrence while retaining MAARSY 2022 as the one validation endpoint requested by the project design.

## Preaccess verdict

`MAARSY_2022_WITH_FIXED_2021_UNLABELED_SUPPORT_PREFLIGHT = STRUCTURALLY_COMPATIBLE`

This verdict is transport/schema compatibility only. It is **not** a scientific external-validation PASS, does not consume the MAARSY scientific panel, and does not authorize event-level access.

A later source audit must still prove the final pair-portable #839 generator/ranker application can map the MAARSY observables exactly, and the complete 2022 truth/power/performance gate must be frozen before SonotaCo 2013/2014 scientific access.

## Firewall

- SonotaCo 2013/2014 scientific access: false.
- MAARSY 2021 event-level scientific access: false.
- MAARSY 2022 event-level scientific access: false.
- MAARSY truth/performance access: false.
- solar longitude 20°–55° target-region access: false.
- OrbitTrace coordinates, members, identity, and prior recovery information: inaccessible.
