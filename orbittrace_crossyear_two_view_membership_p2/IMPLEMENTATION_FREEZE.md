# P2 implementation freeze

This implementation record is frozen before any P1 scientific result and before any P2 scientific execution.

Scientific source identity:

- reconstructed source SHA-256: `1b1b748cbb1c57adf4c22558efd44eef02d49ad143dfc31ab50c7e3c530d2c3f`;
- source is stored only as `source_parts/part00.b64` + `part01.b64`, concatenated, base64-decoded, then gzip-decompressed;
- exact promoted-v8 source/result identities and exact R1 D_SH comparator content SHA are hard-pinned in the source.

Implementation resolution for an otherwise undefined missing-feature case:

- every immutable v8 seed used by P2 must have a valid target-excluded orbit;
- every non-seed event in a frozen ±5° family-direction training/candidate window must also have a valid orbit;
- if either condition fails, P2 is input-ineligible and stops before fitting/evaluation;
- no event may be silently dropped, imputed, assigned an artificial D_SH value, or rescued by an observation-only path.

This resolution is required because P2's frozen feature vector contains exactly two mandatory views `[d_obs, d_orb]`. It closes an implementation degree of freedom; it does not change a threshold or choose a favorable subset.

The source otherwise implements the already-frozen protocol literally: cross-year source templates only, OAS covariance, exact two features, family-direction balanced weights, one `StandardScaler` + L2 `LogisticRegression(C=1, lbfgs)`, unit background responsibility, strict `>0.5` assignment, immutable v8 seeds/rank, and classifier/membership SHA freeze before truth evaluation.

P2 remains dormant until the succession rule in `PROTOCOL.md` authorizes it. No P2 development data are executed by this freeze.
