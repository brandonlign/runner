# AMOS 2023/2024 data request with optional literature-comparator supplement — ready draft, not sent

**Status: communication draft only. No email has been sent by this repository/session.**

This draft preserves the already-frozen primary recurrent-EOM external-validation transfer and appends only the separately frozen comparator-only fields needed to run the established Sugar and catalogue-HDBSCAN literature implementations on the same retained AMOS events. The comparator supplement is optional: inability to provide it does not invalidate the primary recurrent-EOM-vs-vanilla-HDBSCAN external validation.

## Subject

Research request: blinded AMOS 2023–2024 multi-station meteor solutions

## Send-ready draft

Dear Prof. Tóth,

I am conducting a meteor-stream methodology study and would like to ask whether the AMOS team could provide the complete reduced multi-station meteor solutions for calendar years 2023 and 2024 for an independently frozen external-validation test.

The method and evaluation protocol have already been fixed before access to any AMOS 2023/2024 event-level scientific data. To preserve a protected solar-longitude interval, I would like to separate the transfer into stages if feasible.

**Stage 1 — blinding index.** For each year, could you provide the complete solved multi-station sample as a CSV containing exactly:

`event_id,utc_time,solar_longitude_deg`

I would use only those fields to remove the inclusive solar-longitude interval 20°–55° and produce the retained event IDs. No radiant, velocity, orbit, uncertainty, quality, or shower information from the excluded IDs would be opened.

**Stage 2 — retained geometry only.** For only the retained IDs, could you then provide a CSV containing exactly:

`event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`

Here `ra_j2000_deg` and `dec_j2000_deg` should be the geocentric J2000 radiant and `vg_km_s` the geocentric speed. The sample should be the complete solved multi-station sample rather than a shower-only or quality-selected subset; sporadic meteors are required because the detector is evaluated against the full survey background.

**Optional Stage 2B — retained comparator-only quantities.** I have also frozen a supplementary benchmark against previously published meteor-stream clustering methods. If these quantities are directly available from the same solved trajectories, for only the retained IDs could you provide a separate CSV containing exactly:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

The requested meanings are:

- one-sigma uncertainty of the geocentric J2000 right ascension, in degrees;
- one-sigma uncertainty of the geocentric J2000 declination, in degrees;
- one-sigma uncertainty of geocentric speed, in km/s;
- the trajectory convergence angle, in degrees;
- perihelion distance `q`, in AU;
- eccentricity `e`.

Missing comparator-only quantities may be left blank. Please do not derive or approximate quantities that are not directly available from the AMOS solution, and please do not include shower associations or additional orbit elements in this supplemental table. These fields would be used only to reproduce the frozen literature-comparator eligibility rules; they are explicitly excluded from the recurrent-EOM method itself. If AMOS uses materially different uncertainty, velocity-frame, convergence-angle, or orbit conventions, a short description of the convention would be more useful than a conversion.

**Stage 3 — associations only after rankings are frozen.** After all geometry-only candidate memberships, comparator outputs, and complete rankings have been persisted and hash-frozen, could shower associations for the retained IDs be supplied separately as:

`event_id,shower_code`

with events lacking an assigned shower marked explicitly as `SPORADIC`? These associations would remain inaccessible to candidate generation and ranking and would be opened only for the post-freeze evaluation.

If AMOS already has an official public or institutional bulk interface that can provide these reduced fields for the complete 2023/2024 solved sample, a pointer to that interface would also be sufficient and appreciated.

I am happy to follow the AMOS team’s preferred citation, acknowledgement, data-use, or collaboration/coauthorship requirements. I can also provide the frozen protocol and exact field contracts if useful.

Thank you for considering the request.

Best regards,
Brandon Li

## Frozen communication constraints

- exact requested years are 2023 and 2024;
- the Stage-1 transfer contains only IDs, timestamps, and solar longitude;
- protected `[20.0,55.0]` IDs are removed before any Stage-2/2B/3 values are opened;
- the primary transfer remains the complete solved multi-station population, not a shower-only or quality-selected subset;
- Stage 2B is optional and comparator-only; missingness does not remove events from the primary external-validation sample;
- no comparator-only uncertainty, convergence-angle, `q`, or `e` value may enter recurrent-EOM features, scores, ranking, or primary-sample eligibility;
- no imputation, empirical conversion, proxy fitting, or post-receipt comparator-rule relaxation is allowed;
- shower labels remain separate and inaccessible until all method/comparator outputs are frozen and hashed;
- receipt of data authorizes no change to recurrent-EOM v1, its AMOS gate, or the predeclared multi-method benchmark.
