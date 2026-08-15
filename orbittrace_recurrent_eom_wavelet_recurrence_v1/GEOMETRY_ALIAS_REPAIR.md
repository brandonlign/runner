# Geometry alias repair after prelabel technical no-result

Workflow run `31896206565` is permanently classified as a technical no-result.

It successfully opened only the already-authorized target-excluded GMN 2022/2023 geometry, then stopped while constructing the first successor score with `KeyError: 'sun_lon'`. No successor order was completed or persisted, no prelabel JSON was written, no hidden shower truth was opened, and no scientific result JSON was written.

The cause is purely an adapter-name mismatch. The exact recurrent-EOM parent normalizer returns the same frozen physical coordinates under keys:

- `lon` = sun-centered radiant longitude;
- `lat` = ecliptic latitude;
- `vg` = geocentric speed.

The frozen wavelet score expects those same quantities under episode names `sun_lon`, `ecl_lat`, and `vg`.

The only authorized repair is therefore an identity alias in the development wrapper before scoring:

- `sun_lon := lon`;
- `ecl_lat := lat`;
- `vg := vg` unchanged.

No numerical transformation, unit conversion, normalization, parameter, ranking formula, candidate membership, gate, target boundary, dataset, or truth-handling rule changes. The frozen protocol, wavelet-recurrence kernel, multi-anchor v3 source, recurrent-EOM parent, and strong `+2` recovered@100 gate remain unchanged.

The next technically valid run remains the first binding scientific outcome.