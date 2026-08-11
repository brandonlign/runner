# Pre-status exact-v31 order-hash provenance correction

Workflow run `31506843778` passed the corrected immutable #950 source counts, loaded immutable v31 training truth, reproduced exact v31, and reproduced the already-frozen pre-status 229-family v31 rank vector. It then stopped while freezing the source-density vector, before authoritative #1046 surfaced/missed status was restored and before any diagnostic median or PASS/FAIL statistic was computed.

The stop was caused solely by a local provenance helper in the frozen source-density diagnostic. Its `order_sha()` serialized the exact v31 order as `"\n".join(order) + "\n"`, while authoritative v31 source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da` defines `order_sha()` as `sha256("\n".join(order).encode())` with **no terminal newline**. The family order itself was unchanged.

`prestatus_provenance_repair_v3.py` loads the original frozen diagnostic by exact sibling file path, applies the already-established immutable #950 source counts `{'hard':19,'p19':53,'p20':157}`, and replaces only this local order-hash serializer with the exact authoritative v31 definition.

The scientific statistic remains exactly `A(i) = global_v31_percentile(i) - within_source_v31_percentile(i)`. The #1046 representative rule and the preregistered PASS gate remain unchanged: in both 2013 and 2014, missed-recoverable median A must be strictly positive and strictly greater than surfaced-recoverable median A.

No family identity, source identity, source count, rank, percentile formula, status attachment order, outcome use, ranking, panel evaluation, successor, or protected-data rule changes.
