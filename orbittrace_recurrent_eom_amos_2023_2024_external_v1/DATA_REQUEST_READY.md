# AMOS 2023/2024 data request — ready draft, not sent

**Status: communication draft only. No email has been sent by this repository/session.**

Current public AMOS project contact (verified 2026-08-14): Prof. Juraj Tóth, `Juraj.Toth@fmph.uniba.sk`.

## Subject

Research request: blinded AMOS 2023–2024 multi-station meteor solutions

## Draft

Dear Prof. Tóth,

I am conducting a meteor-stream methodology study and would like to ask whether the AMOS team could provide the complete reduced multi-station meteor solutions for calendar years 2023 and 2024 for an independently frozen external-validation test.

The method and evaluation protocol have already been fixed before access to any AMOS 2023/2024 event-level scientific data. To preserve a protected solar-longitude interval, I would like to separate the transfer into three stages if feasible.

**Stage 1 — blinding index.** For each year, could you provide the complete solved multi-station sample as a CSV containing exactly:

`event_id,utc_time,solar_longitude_deg`

I would use only those fields to remove the inclusive solar-longitude interval 20°–55° and return the retained event IDs. No radiant, velocity, orbit, quality, or shower information from the excluded IDs would be opened.

**Stage 2 — retained geometry only.** For only the retained IDs, could you then provide a CSV containing exactly:

`event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`

Here `ra_j2000_deg` and `dec_j2000_deg` should be the geocentric J2000 radiant and `vg_km_s` the geocentric speed. I do not need orbital elements for this validation.

The sample should be the complete solved multi-station sample rather than a shower-only or quality-selected subset; sporadic meteors are required because the detector is evaluated against the full survey background.

**Stage 3 — associations only after rankings are frozen.** After the geometry-only candidate memberships and complete rankings have been persisted and hash-frozen, could shower associations for the retained IDs be supplied separately as:

`event_id,shower_code`

with events lacking an assigned shower marked explicitly as `SPORADIC`? These associations would remain inaccessible to candidate generation and ranking and would be opened only for the post-freeze evaluation.

If AMOS already has an official public or institutional bulk interface that can provide these exact reduced fields for the complete 2023/2024 sample, a pointer to that interface would also be sufficient and appreciated.

I am happy to follow the AMOS team’s preferred citation, acknowledgement, data-use, or collaboration/coauthorship requirements. I can also provide the frozen protocol and exact field contract if useful.

Thank you for considering the request.

Best regards,
Brandon Li

## Non-negotiable scientific constraints attached to this draft

- exact years remain 2023 and 2024;
- no alternate year pair may be substituted after seeing availability/results without a separately justified protocol;
- complete solved multi-station population is required, not a shower-only subset;
- no quality-filtered subset is requested;
- protected `[20.0,55.0]` physical rows must remain unopened;
- no orbit elements are needed;
- no AMOS-specific calibration may be fitted;
- labels remain separate and inaccessible until pretruth SHA-256 freeze;
- receipt of data does not authorize any change to recurrent-EOM v1 or its gate.
