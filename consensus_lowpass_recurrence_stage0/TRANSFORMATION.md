# Exact source transformation manifest

The frozen candidate source was created before any score by applying only the following changes to exact majority-conditioned source SHA-256 `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`:

1. Add constants:
   - `PERSISTENT_ACTIVE_YEARS = 12`;
   - `CONSENSUS_SMOOTH_SIGMA = (1.6, 1.6, 1.0, 0.9)`.
2. In each unchanged template-width loop:
   - retain every existing score;
   - compute `consensus_evidence = median(per_year_evidence, axis=0)`;
   - Gaussian-smooth only that consensus with the fixed inherited sigma and existing boundary modes;
   - subtract it from every annual evidence map, truncate below zero, and take the unchanged third-strongest year;
   - maximize the resulting map over the unchanged widths.
3. Add `consensus_lowpass` to the unchanged complete-search threshold calibration and evaluation bundle.
4. Retain the existing five-year recurrent and one-year transient injections.
5. Add a twelve-year recurrent injection on the unchanged shared-structure background for every existing strength and location rule.
6. Compare the candidate with pooled, pooled-confirmed, hard recurrence, soft recurrence, and complete-median majority conditioning.
7. Add the seven frozen reduced-screen gates stated in `SOURCE_AUDIT_PROTOCOL.md`.
8. Replace only the stale Markdown reporter with candidate-specific metric names; JSON construction and simulation evidence are otherwise preserved.

No histogram grid, evidence formula, annual null, shared-structure generator, template width, recurrence order, location rule, jitter, strength, comparator implementation, threshold estimator, or input parser was changed.

The resulting exact candidate source is stored in `source_parts/` and must decode to SHA-256 `9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa`.