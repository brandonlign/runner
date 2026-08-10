# MAARSY 2022 schema-only external-compatibility preflight — v1

## Scope

This is a metadata/source-only preflight permitted by `FINAL_EXTERNAL_VALIDATION_POLICY_V1.md`. It is performed before any SonotaCo 2013/2014 scientific access, before any MAARSY event-level scientific value is opened, and before any target access.

It answers one narrow question: can the already-frozen #839 URC discovery architecture be transported **unchanged** to the currently frozen single-year MAARSY 2022 validation panel?

This file does not replace the validation dataset, inspect a MAARSY event, run the detector, compute a performance endpoint, or authorize external/target access.

## Public schema/time-span evidence only

The public MAARSY head-echo catalogue metadata is sufficient to establish that the survey itself is not missing the basic physical-observable class needed for meteor-stream work:

- Zenodo record `10.5281/zenodo.15553437` identifies the public **MAARSY 2016–2024 Meteor Head Echo RCS Dataset**.
- Vierinen et al., EGU General Assembly 2025, `10.5194/egusphere-egu25-18621`, describes a nearly continuous 2016–2024 MAARSY catalogue containing atmospheric trajectories, Doppler shifts and radar-cross-section estimates, with Keplerian orbital elements computed for each meteor.
- The 2026 Atmospheric Measurement Techniques MAARSY study (`Monitoring of lower thermospheric neutral density variations using meteor head echoes`, AMT 19, 4277–4294) describes the processed 2016–2023 survey as providing three-dimensional meteor trajectories and geocentric velocities.

Only these dataset-level descriptions were inspected. No archive payload or event-level row was opened.

## Frozen URC temporal contract

The already-frozen URC proposal architecture is intrinsically a **two-annual-scan recurrence method** rather than a single-catalogue clustering method.

The pair-portable #839 generator source makes that contract explicit:

- application input is `years: tuple[int, int]` with two distinct year values;
- the scan must contain exactly those two year keys;
- hard-v8 family construction is performed on components from both annual scans;
- P19 is a recurrence layer constructed after both annual scans exist;
- P20 forms reciprocal isolated-quartet families by matching quartets from the first supplied year to quartets from the second supplied year, with every retained family carrying both years and exact 4+4 membership.

The portable adapter generalizes literal year addressing only. It does **not** change annual-recurrence semantics, proposal thresholds, event density, or family-existence rules.

## Compatibility result for the frozen panel

The frozen validation panel is **MAARSY 2022**, i.e. one calendar year.

A single 2022 annual scan cannot satisfy the frozen method's requirement for two distinct annual scans. Creating two pseudo-years by splitting 2022 events would not be a transport operation: it would change the statistical sampling density and, more importantly, replace independent annual recurrence with within-year subsampling. That would alter the scientific family-existence mechanism and is forbidden by the no-retuning/no-proxy external policy.

Therefore the current combination

`#839 URC annual-recurrence architecture + MAARSY 2022 single-year validation panel`

is **structurally incompatible for full-method no-retuning external validation**.

This conclusion is independent of whether M0 or M2 membership ultimately wins, because M2 is allowed to alter membership only; the hard/P19/P20 two-year proposal architecture remains fixed.

## Preaccess verdict

`MAARSY_2022_SINGLE_YEAR_FULL_URC_PREFLIGHT = INCOMPATIBLE`

This is not a scientific performance FAIL and does not consume the external validation panel. It is an architecture/panel compatibility finding made without event values.

No external-generalization PASS can be claimed by running a scientifically altered one-year approximation of the URC method. The incompatibility must be resolved at the governance/validation-design level **before** SonotaCo 2013/2014 scientific access if the project is to retain a defensible no-retuning generalization requirement.

This preflight does not itself authorize a dataset substitution or year addition.

## Firewall

- SonotaCo 2013/2014 scientific access: false.
- MAARSY event-level scientific access: false.
- MAARSY performance access: false.
- solar longitude 20°–55° target-region access: false.
- OrbitTrace coordinates, members, identity, and prior recovery information: inaccessible.
