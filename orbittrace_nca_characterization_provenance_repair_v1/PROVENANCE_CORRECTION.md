# NCA OrbitTrace characterization v1 — provenance correction

Run `32308654983` is a technical no-result. Stage 1 stopped before its seal and Stage 2 reveal was skipped, so canonical target IDs did not enter the failed construction.

The failure was caused by one mislabeled provenance expectation in the characterization harness, not by the NCA scientific construction.

The prior exact M2D scorer emitted for the frozen rank-82 parent:

`ci=49 n=1708 m=28994 score=3.61022e-10 b=69 repl=530`

Inspection of the byte-frozen C++ source (`orbittrace_internal_mass_sonotaco_development_v1/internal_mass_exact.cpp`, commit `a5dd599ac94ce3c2597755be6c40c945f95929f8`) shows:

- `n` = candidate vertices;
- `m` = internal radius-graph edges;
- binary/output field `x` = positive annual-degree parent/outside boundary records;
- stderr field `b` = `blevels.size()`, the number of distinct outer annual-density levels;
- `repl` = dynamic maximum-spanning-forest edge replacements.

Therefore the original protocol/harness sentence interpreting `b=69` as 69 positive boundary edges was wrong. The exact full-universe reconstruction in run `32308654983`, performed before any canonical-ID access, returned:

- parent vertices: `1708`;
- internal edges: `28994` — exact match to frozen `m`;
- positive boundary records (`x` semantics): `4021`;
- outer annual-density levels (`b` semantics): `69`.

The repaired execution keeps `orbittrace_nca_orbittrace_characterization_v1/build_pretruth.py` byte-frozen at Git blob `6214be3da3afdf2e629fd34be980c0405c1abeae`. A wrapper changes only its mistaken provenance constant from `69` to `4021` at runtime. The repaired Stage-1 seal separately requires both `positive_boundary_edges == 4021` and `relevant_rho23_level_count == 69`.

No parent membership, graph edge, annual degree, bifiltration rule, persistence area, BWM rule, CMR rule, NCA branch rule, score, threshold, target overlap, or target-derived parameter is changed. Canonical IDs remain unavailable until the repaired Stage-1 artifact is sealed.
