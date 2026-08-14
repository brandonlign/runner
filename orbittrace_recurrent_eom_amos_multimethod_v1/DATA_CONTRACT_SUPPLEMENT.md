# AMOS 2023/2024 comparator-only supplemental data contract

## Purpose

This file supplements, but does not modify, the frozen recurrent-EOM AMOS 2023/2024 data contract. The base three-stage transfer remains authoritative for the primary external-validation experiment. These extra fields exist only to make the already-frozen Sugar and catalogue-HDBSCAN literature implementations technically evaluable on AMOS under same-row pairwise comparisons.

No AMOS data have been received or inspected by this contract.

## Preconditions

Before this supplement may be opened:

1. the exact Stage-1 blind receipt from the primary AMOS protocol must have produced a retained-ID allowlist for calendar years 2023 and 2024;
2. every ID in the protected inclusive solar-longitude interval `[20.0,55.0]` must already have been removed;
3. the supplement must be keyed only by retained `event_id`.

Any unknown, protected, duplicate, or blank ID causes fail-closed termination before any supplemental value is used.

## Exact allowed header

The supplemental file header is exactly:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

No extra column is allowed.

### Meanings

- `event_id`: exact stable ID matching the retained base AMOS solution.
- `ra_sd_deg`: reported one-sigma uncertainty of the geocentric J2000 right ascension, degrees.
- `dec_sd_deg`: reported one-sigma uncertainty of the geocentric J2000 declination, degrees.
- `vg_sd_km_s`: reported one-sigma uncertainty of geocentric speed, km/s.
- `convergence_angle_deg`: documented multi-station trajectory convergence angle, degrees.
- `q_au`: perihelion distance of the same solved trajectory, AU.
- `e`: eccentricity of the same solved trajectory.

If AMOS uses a materially different uncertainty definition, velocity frame, convergence-angle definition, or orbit convention that prevents direct use of the frozen comparator predicate, that field is incompatible; no empirical conversion is allowed.

## Missingness

Blank/null comparator-only values are permitted. They do not remove an event from the primary recurrent-EOM AMOS sample. They only determine structural eligibility for the literature comparator that requires the missing field.

No imputation, fitting, proxy substitution, derivation from rounded values, or post-receipt quality-rule change is allowed.

## Isolation from recurrent-EOM

The recurrent-EOM implementation receives only the already-frozen canonical geometry fields:

`id,year,sol,sun_lon,ecl_lat,vg`

The supplemental uncertainty, convergence-angle, and orbit fields are forbidden as recurrent-EOM features, scores, tie breakers, filters except when constructing the predeclared **pairwise comparator row universe** for a same-information comparison.

Pairwise filtering is applied symmetrically: if a row is ineligible for a comparator, it is excluded from both that comparator and recurrent-EOM in that comparator-specific supplementary analysis.

## Truth isolation

This supplement may not contain or be joined to a shower code, shower name, IAU identifier, sporadic flag, background designation, target marker, cluster label, or any other truth-bearing field until all candidate/comparator outputs for that pairwise universe have been frozen and hashed.

## Provider request wording

If the base AMOS request is sent, the following comparator-only request may be appended without changing the primary experiment:

> For the retained non-protected event IDs only, and only if these quantities are directly available from the same solved multi-station trajectory, please also provide a separate table with: one-sigma geocentric J2000 RA uncertainty (deg), one-sigma geocentric J2000 Dec uncertainty (deg), one-sigma geocentric-speed uncertainty (km/s), trajectory convergence angle (deg), perihelion distance q (AU), and eccentricity e. Missing quantities may be left blank. Please do not include shower associations or any additional orbit elements in this supplemental table.

This wording is fixed before any AMOS transfer.