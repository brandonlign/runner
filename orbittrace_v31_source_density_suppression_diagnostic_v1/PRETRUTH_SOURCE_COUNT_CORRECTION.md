# Pretruth source-count provenance correction

This is an engineering/provenance correction to the already-frozen source-density diagnostic. It does **not** change the diagnostic statistic, status source, representative rule, PASS gate, or any outcome-dependent choice.

The first execution attempt, workflow run `31505343915`, stopped in the immutable #950 payload-verification step before SonotaCo truth was loaded, before exact v31 was reproduced, before the pre-status rank vector or source-density vector was constructed, and before authoritative #1046 surfaced/missed status was restored. Therefore it produced no scientific diagnostic result.

The frozen protocol/source incorrectly transcribed the immutable #950 HDB proposal-source cardinalities as `hard=19`, `p19=54`, `p20=156`. Direct inspection of the already-immutable pretruth #950 `hdbscan/V22_PRETRUTH_FEATURE_MANIFEST.json` shows the exact counts are instead:

- `hard = 19`
- `p19 = 53`
- `p20 = 157`

The total remains exactly 229 and the source labels/family universe are unchanged.

The diagnostic formula remains exactly:

`A(i) = p_global(i) - p_source(i)`

where `p_source(i)` uses the actual immutable cardinality of family `i`'s proposal source. No source was selected, reweighted, merged, split, or treated specially after seeing any outcome.

The preregistered PASS gate remains unchanged: in both 2013 and 2014, the missed-recoverable median `A` must be strictly positive and strictly greater than the surfaced-recoverable median `A`.

All original non-search commitments and the protected-data firewall remain in force. SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`; protected 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
