# AMOR numeric-token transport correction

The delimiter-corrected external attempt reached the first allowed scientific field `LS` but parsed zero events because the preserved AMOR data tokens carry a terminal comma. The staged parser diagnostics subsequently established, without detector/family/ranking/orbit access, that:

- every width-18 LS token in 1996 and 1998 matches a finite decimal core followed by exactly one terminal comma;
- the only LS range-invalid values are `360.0,`, which the already-frozen external parser discards before any other field;
- after discarding range-invalid LS and the 20°–55° blind interval, every inspected `Yr`, `Mn`, `RA`, `DECL`, and `Vg` token in both selected years has exactly the same decimal-core + one-terminal-comma grammar.

This correction is therefore transport-only and source-proven. The original scientific runner and protocol remain immutable. The corrected wrapper applies exactly two parser adaptations:

1. whitespace tokenization, already proven by the structure-only audit;
2. a strict numeric decoder that accepts only ASCII finite decimal/scientific numeric text followed by exactly one terminal comma, removes that comma, and converts the core to `float`.

No bare numeric token, multiple comma, missing marker, alternate decimal syntax, or inferred repair is accepted.

The same strict decoder is used at the post-ranking orbital reread. Orbital token syntax has deliberately not been inspected before ranking freeze; if it is incompatible with this strict rule, the run must stop/fail integrity rather than broaden the parser after seeing rankings.

The selected AMOR years, archive hashes, width-18-only policy, LS range rule, 20°–55° blind cut, event identities, 10,000/bin density normalization, fixed4 proposals, v6 connected-family topology, v8 pooled-year centroids, 128-event multiplicity ranking, Brown/v3/persistence comparators, D_SH validator, power floors, top-K rule, and scientific pass gates are unchanged.
