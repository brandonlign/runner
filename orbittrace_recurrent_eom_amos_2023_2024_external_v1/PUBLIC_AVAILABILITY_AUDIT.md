# AMOS 2023/2024 public-availability audit — zero scientific data

**Classification: NEUTRAL infrastructure finding.**

This audit was performed on 2026-08-14 after the recurrent-EOM AMOS scientific protocol and executable split-stage pipeline were frozen. It uses only public project/documentation pages and publication metadata. It does not open, request, download, inspect, or summarize an AMOS 2023/2024 meteor-event row.

## Purpose

Determine whether a public bulk interface already exposes the exact reduced multi-station fields required by the frozen recurrent-EOM AMOS 2023/2024 validation, before resorting to a direct data request.

This is a transport/availability audit only. It cannot change:

- recurrent-EOM v1;
- AMOS years 2023/2024;
- GEO6 representation;
- 20°–55° protected exclusion;
- coordinate adapter;
- label boundary;
- external-validation evaluator or gate.

## Public sources inspected

### Comenius University AMOS project page

Current page:

`https://fmph.uniba.sk/microsites/daa/daa/veda-a-vyskum-dev/amos/`

Observed metadata only:

- AMOS is an active Comenius University project;
- project lead is Prof. Juraj Tóth;
- listed contact email is `Juraj.Toth@fmph.uniba.sk`;
- the page describes current network/project activity but does not present a bulk historical reduced-trajectory download/API for the requested 2023/2024 event sample.

### Comenius University AMOS technical/project page

Current page:

`https://fmph.uniba.sk/microsites/daa/daa/veda-a-vyskum/amos/`

Observed aggregate metadata only:

- an AMOS all-sky camera records roughly 10,000–20,000 meteors per year depending on site/conditions;
- paired stations at overseas sites permit identification of roughly 5,000–8,000 common meteors per year and determination of their orbital characteristics;
- the page describes real-time operations/data archiving but does not expose a public bulk reduced-event download/API for the exact requested 2023/2024 multi-station sample.

These aggregate counts are not used as a scientific power result and do not replace the frozen AMOS gate. They only show that the intended survey is plausibly large enough to justify requesting the exact panel.

### Harvard/CfA AMOS live page

Current page:

`https://lweb.cfa.harvard.edu/~pveres/amos.html`

Observed metadata only:

- the same meteor detected by two stations is used to derive a geocentric velocity and atmospheric trajectory;
- those products feed heliocentric-orbit and shower/sporadic analysis;
- the visible page is a live-project/latest-images interface, not a historical bulk reduced-trajectory export.

This directly supports input compatibility with frozen recurrent-EOM's geocentric-speed requirement without exposing a requested-year event value.

### 2026 AMOS methods paper

Current publication metadata:

Tóth et al., `AMOS global meteor network: Instrumentation, procedures, accuracy validation and results`, Icarus 454 (2026), 117086.

Observed publication-level metadata only:

- AMOS is a global automated all-sky video network;
- its processing includes meteor trajectory and heliocentric-orbit determination;
- the paper describes/validates the trajectory/orbit pipeline.

No 2023/2024 event table from the paper was accessed or used.

## Binding availability conclusion

`NO_PUBLIC_BULK_AMOS_2023_2024_REDUCED_TRAJECTORY_EXPORT_FOUND_IN_INSPECTED_INTERFACES`

This wording is deliberately narrow. It means only that the specific public pages/search results inspected in this audit did not expose a bulk historical trajectory download or documented API satisfying the frozen data contract. It is **not** a claim that no such interface exists privately or elsewhere.

Therefore the scientifically clean next route remains the already-prepared direct data request to the AMOS team. If the team instead identifies an official public bulk interface, that interface may be used only after a separately frozen structure/transport audit and without opening event scientific values first.

## Request boundary

The request must ask for the complete solved multi-station sample, including sporadics, and preserve the already-frozen three-stage split:

1. minimal blinding index: `event_id,utc_time,solar_longitude_deg`;
2. only retained IDs after inclusive `[20.0,55.0]` exclusion: `event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`;
3. only after the pretruth candidate/ranking SHA-256 is frozen: `event_id,shower_code`, with unassociated events explicitly marked `SPORADIC`.

No quality filter, shower-only subset, orbit-element requirement, AMOS-specific calibration, or alternate year pair is authorized.

## Firewall

- `amos_2023_2024_event_rows_accessed=false`
- `amos_2023_2024_labels_accessed=false`
- `amos_2023_2024_orbit_elements_accessed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
