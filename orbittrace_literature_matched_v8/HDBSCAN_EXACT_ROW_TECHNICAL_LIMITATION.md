# Frozen HDBSCAN exact-row technical limitation

Final exact-row workflow run `31227299751` passed every pre-data source, protocol, assignment-hash, archive-hash, and blindness guard, then executed the frozen v8 scanner on the exact blind-safe HDBSCAN row universe.

The HDBSCAN panel contained exactly 26,460 SonotaCo-2023 rows and 19,658 SonotaCo-2025 rows. Candidate generation completed label-free in both years:

- 2023: 2,410 retained quartets, 413 components;
- 2025: 1,859 retained quartets, 327 components.

Before any shower label was loaded, frozen v8 multiplicity scoring stopped with:

`RuntimeError: family G62b0b1b96a90 year 2025 has only 64 events in local window`

The promoted v8 scorer requires a local episode of exactly 128 events. Under the exact HDBSCAN quality-filtered input rows, that requirement cannot be satisfied for this valid recurrent family.

## Scientific classification

This is a genuine matched-input incompatibility, not a detector-performance result and not an implementation defect.

The following changes are prohibited because each would alter either v8 or the exact-row benchmark after exposure:

- reducing the frozen episode size below 128;
- dropping the unscoreable family;
- widening the local window or changing its construction;
- adding target-excluded survey rows that HDBSCAN did not receive;
- changing HDBSCAN quality cuts to increase density;
- changing any v8 family/ranking/scoring parameter.

Therefore a **strict full-v8 exact-event-row comparison against catalogue HDBSCAN is technically infeasible on this SonotaCo 2023/2025 pair under the frozen methods**. The earlier same-survey/year comparison remains valid at its explicitly weaker scope (same survey years and blind-label universe, method-specific quality filters), but it must not be described as exact-row matched.

This limitation itself is negative evidence against a broad state-of-the-art claim: v8 cannot be shown to dominate HDBSCAN under the preregistered strict matched-row protocol.

No OrbitTrace target coordinate, identity, member, excluded-interval content, or final target result was accessed; the failure occurred before the common label parser was invoked.
