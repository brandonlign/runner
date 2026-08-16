# Engineering correction v1 — no scientific result

Initial run `31934917047` is an engineering no-result only.

The run loaded the exact target-excluded GMN corpus and reached the first frozen subset (`d=128`, bucket `0`, `n=5567`), then stopped before MeanShift fitting because `physical_embedding()` requested pre-normalization radiant aliases `sun_lon` / `ecl_lat` from rows already passed through the exact selected recurrent-EOM `normalize_event()` function.

That normalizer intentionally returns the same physical quantities under canonical keys:

- `sol` -> `sol`
- Sun-centered ecliptic longitude -> `lon`
- ecliptic latitude -> `lat`
- geocentric speed -> `vg`

Exact exception:

`KeyError: 'sun_lon'`

The failure occurred before any modal basin, recurrent-EOM comparator output, cross-scale Jaccard metric, or result JSON was produced. No scientific outcome was observed.

Authorized engineering correction only:

- preserve frozen `PROTOCOL.md` and original `run_diagnostic.py` unchanged;
- invoke the exact same frozen diagnostic through a wrapper whose only replacement is `physical_embedding()`, reading the canonical normalized keys `lon` and `lat` instead of their pre-normalization aliases;
- retain exactly the same 5° solar half-width, 4° radiant scale, 10% speed scale, six-coordinate formula, MeanShift bandwidth/seeding/iterations, minimum basin support, recurrent-EOM comparator, subsets, cross-scale metric, non-collapse rule, and frozen gate.

This changes field names only, not any numeric value or scientific method. The corrected execution, if it reaches `MODAL_BASIN_SCALE_V1.json`, is the first technically valid outcome for this architecture.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed by the failed run.
