# Conditional local-trunk AMOS 2023/2024 staged data request — ready draft, NOT SENT

## Status

**Communication draft only. Nothing is authorized or sent by this file.**

This draft may be used only if the frozen GMN experiment returns exactly `PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`. The scientific method, receipt firewall, and AMOS evaluator are already frozen before any AMOS event-level access. The requested data fields are unchanged from the previously audited density-synchronous AMOS request because local TopoModal trunk v1 uses only the same retained solar longitude, radiant, geocentric speed, event ID, year, and post-freeze shower-association information.

## Subject

Research request: blinded AMOS 2023–2024 multi-station meteor solutions for a frozen external test

## Ready draft

Dear Prof. Tóth,

I am conducting a meteor-stream methodology study and would like to ask whether the AMOS team could provide the complete reduced multi-station meteor solutions for calendar years 2023 and 2024 for a one-shot external validation test.

The final method, comparison methods, field contract, protected-region handling, and evaluation criteria have already been fixed before access to any AMOS 2023/2024 event-level scientific data. To preserve that blinding, I would like to separate the transfer into stages if feasible.

**Stage 1 — blinding index only.** For each year, could you provide the complete solved multi-station sample as a CSV containing exactly:

`event_id,utc_time,solar_longitude_deg`

I would use only those fields to remove the inclusive solar-longitude interval 20°–55° and create a retained-ID allowlist. No radiant, velocity, orbit, uncertainty, quality, or shower-association value from an excluded ID would be opened.

**Stage 2 — retained physical geometry only.** For only the retained IDs, could you then provide a CSV containing exactly:

`event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`

Here `ra_j2000_deg` and `dec_j2000_deg` should be the geocentric J2000 radiant and `vg_km_s` the geocentric speed. The requested population is the complete solved multi-station sample rather than a shower-only or quality-selected subset; sporadic meteors are needed because the method is evaluated against the full survey background.

**Optional Stage 2B — retained literature-comparator quantities.** A supplementary benchmark against already-frozen literature-method implementations is also prespecified. If these quantities are directly available from the same solved trajectories, for only the retained IDs could you provide a separate CSV containing exactly:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

The requested meanings are one-sigma uncertainties of geocentric J2000 right ascension and declination in degrees, one-sigma geocentric-speed uncertainty in km/s, trajectory convergence angle in degrees, perihelion distance `q` in AU, and eccentricity `e`. Missing optional quantities may be left blank. Please do not derive or approximate unavailable fields and please do not include shower associations or additional orbit elements in this table. These optional fields are isolated from the primary OrbitTrace method.

**Stage 3 — shower associations only after the pretruth freeze.** After the retained geometry has been processed and the complete ordinary-HDBSCAN, recurrent-EOM, density-synchronous recurrent-EOM, and final recurrent-local-TopoModal-trunk candidate memberships and rankings have been persisted and hash-frozen, could the shower association for every retained ID be supplied separately as a CSV containing exactly:

`event_id,shower_association`

Please use the explicit value `SPORADIC` for retained events without an assigned shower. The association table would remain inaccessible to candidate generation, hierarchy construction, local-topology membership construction, cluster selection, and ranking and would be opened only by the post-freeze evaluator.

If AMOS already has an official public or institutional bulk interface that can provide these reduced fields for the complete 2023/2024 solved sample under the same staged separation, a pointer to that interface would also be appreciated.

I am happy to follow the AMOS team’s preferred citation, acknowledgement, data-use, or collaboration requirements, and I can provide the frozen protocol and exact field contracts if helpful.

Thank you for considering the request.

Best regards,
Brandon Li

## Frozen communication constraints

- exact years: 2023 and 2024 only;
- Stage 1 exact header: `event_id,utc_time,solar_longitude_deg`;
- `[20.0,55.0]` excluded inclusively before Stage-2/2B/3 values may be opened;
- Stage 2 exact header: `event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`;
- Stage 3 exact header: `event_id,shower_association`, with exact `SPORADIC` for unassigned retained events;
- complete solved multi-station population required, including sporadics;
- Stage 2B optional/comparator-only and never alters the primary sample;
- no imputation, empirical conversion, survey calibration, alternate years/sample, or replacement survey;
- labels remain inaccessible until all four primary candidate catalogues are frozen and hashed;
- no method, threshold, physical scale, local-trunk rule, rank, gate, or final-method change after receipt;
- this document remains **NOT SENT** until a separate explicit owner-authorized send action occurs.
