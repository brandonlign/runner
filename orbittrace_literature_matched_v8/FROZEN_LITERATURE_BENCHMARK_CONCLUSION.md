# Superseded literature benchmark conclusion

This file is retained only to preserve the history of the literature-comparison track. Its earlier revision contained a hand-assembled HDBSCAN matched-survey table that was not tied to a reproducible canonical workflow and therefore must **not** be used for scientific claims.

The authoritative frozen conclusion is:

- `orbittrace_literature_matched_v8/FROZEN_LITERATURE_CONCLUSION.md`
- `orbittrace_literature_matched_v8/FROZEN_LITERATURE_CONCLUSION.json`

Those files are artifact-audited against:

- exact-row v8 vs full Sugar workflow `31227437130`;
- frozen v8 same-survey workflow `31226030807` for v8-only annual metrics;
- canonical blind-safe HDBSCAN-2023 workflow `31226945294`, independently assignment-verified by workflow `31227148081`;
- blind-safe HDBSCAN-2025 workflow `31071589912`;
- strict HDBSCAN exact-row limitation workflow `31227299751`.

The final evidence-backed HDBSCAN conclusion is **not established superiority for v8 in sparse-stream discovery**. The strict identical-row full-v8 comparison is technically infeasible under the frozen methods because a valid recurrent family has only 64 available 2025 local-window rows while promoted v8 requires exactly 128. Same-survey/year results retain method-specific quality filters and do not satisfy the preregistered sparse superiority gate.

The exact-row Sugar conclusion remains a clear negative for v8: it fails both the 4–9 and broader 4–24 superiority gates and is substantially worse from 10 members upward and overall on the tested SonotaCo rows.

No v8 parameter was changed in response to comparator performance. The OrbitTrace target, coordinates, members, identity, excluded-interval contents, and final target result were not accessed.
