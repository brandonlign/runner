# Obninsk 1967–1968 recurrent-EOM preaccess adjudication

**Classification: NEUTRAL — pristine panel preserved, recurrent-EOM input compatibility not established.**

This adjudication occurs after recurrent-EOM HDBSCAN v1 passed target-excluded GMN development and the exposed SonotaCo 2013/2014 v31 benchmark, but **before any Obninsk meteor-event row is opened**.

## Frozen untouched status

Existing metadata-only Obninsk records remain authoritative:

- Stage-0 run `31231190121`, artifact `9013852268`, digest `sha256:6e26d9cda44d0a3d7787eb16fbfbd468fc895c3d5a3830170968abd34bd99303`;
- schema-only run `31231326927`, artifact `9013895837`, digest `sha256:d47f876429060b5824933f7a76c6ea60dd7678ffaf5e6f5381cb93a0b4090fbb`;
- PDS archive SHA-256 `7b4e1c138a6f44966adb28ea437921ca45b840365327f13dc5093397e0b19985`;
- `obninsk.xml` SHA-256 `ad36061a25d9c36b818f3ecf63a0bcfa9610adc98f0d937b15af140f041aba5b`;
- 9,358 records, 1967-09-15 through 1968-08-15;
- `event_row_access=false` and `obninsk.tab` unopened in both prior stages.

No event row is opened by this adjudication.

## Recurrent-EOM input requirement

The promoted method is frozen with the exact GMN/SonotaCo GEO6 representation:

`(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`

where the radiant is a geocentric/sun-centered direction and `vg` is geocentric speed. Changing or omitting the speed channel after seeing external-survey metadata would create a different method and is not authorized.

## Metadata-only mapping audit

The PDS schema provides:

- `OBSERVATION_TIME`: UT time of observation;
- `RADIANT_RA`, `RADIANT_DEC`: observed radiant in B1950.0 coordinates;
- `VINF`: described by PDS as **"Velocity at the top of the atmosphere, known as V(inf) in the field of meteor observations."**

Observation time is sufficient for a deterministic solar-position calculation, and B1950 radiant coordinates are in principle deterministically transformable to ecliptic coordinates with conventions frozen before data access.

The speed channel fails the old Obninsk Stage-0 compatibility rule. PDS does **not** document `VINF` as the exact modern geocentric asymptotic speed used by recurrent-EOM, nor does the metadata specify an observation/top-of-atmosphere altitude or an exact gravitational correction convention that would make `VINF -> vg` unique from documentation alone.

Independent NASA meteoroid-dynamics documentation also distinguishes velocity relative to Earth before gravitational acceleration from the corresponding velocity at the top of the atmosphere after Earth's gravity is included. Therefore equating the archived top-of-atmosphere `VINF` field with recurrent-EOM's `vg` is not justified as an exact metadata-only identity.

Deriving a replacement speed from the archived orbital elements is also not authorized: it would introduce a new external-survey transform from rounded derived orbital fields rather than preserve the frozen observed-geometry/speed representation.

## Binding consequence

Verdict:

`DEFER_OBNINSK_RECURRENT_EOM_EXTERNAL_VALIDATION_INPUT_INCOMPATIBLE_PREACCESS`

- Do **not** open `obninsk.tab` for recurrent-EOM.
- Do **not** fit or calibrate a `VINF -> vg` transform from Obninsk values.
- Do **not** drop the speed dimension, change its scale, derive it from orbit elements, or substitute another field.
- Preserve Obninsk as event-value untouched for any future method whose inputs are genuinely documented by this archive.

This is not evidence that recurrent-EOM fails on Obninsk. It is a preaccess interface incompatibility and therefore scientifically neutral.

## Firewall

- `target_information_access=false`
- `target_region_events_accessed=false`
- `obninsk_event_row_access=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected solar longitude `[20°,55°]` remains inaccessible.
