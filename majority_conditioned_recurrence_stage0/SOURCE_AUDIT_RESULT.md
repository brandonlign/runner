# Majority-conditioned recurrence source audit: pass

Runner workflow `30879930251` completed the frozen no-score audit. Artifact `8880883035` was preserved with digest `sha256:02868aad5e30d7602b9657768dd0244c1ef2372dbab282c2e4bbef4a7d678702`.

The exact worst-family source SHA-256 `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac` was reconstructed and the committed deterministic derivation produced:

- candidate SHA-256 `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- 29,871 source bytes;
- 629 source lines;
- successful Python compilation.

All frozen static checks passed. The source contains the pointwise annual median, common-mode subtraction, nonnegative truncation, majority-conditioned method key and verdict, while retaining the hard recurrence, soft recurrence, shared-structure null, recurrent injection, and transient injection.

No scientific dependency was installed, no data was downloaded, and no detector, null, injection, score, threshold, or endpoint was executed.

Verdict: **`PASS_MAJORITY_CONDITIONED_SOURCE_AUDIT`**.

This authorized only the separately frozen reduced screen in PR #86.