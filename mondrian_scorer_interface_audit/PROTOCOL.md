# Coverage-normalized Mondrian scorer interface audit

This auxiliary runner-only workflow decodes the exact passed PR #38 source and records its source hash, compile status, top-level constants, function signatures, and complete source text for implementation review.

It must not download meteor data, read labels, form windows, compute scores, inspect endpoints, or access GhostStream or SonotaCo. The exact decoded source must match SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

This audit creates no scientific result and authorizes no method change. It exists only to preserve the passed scorer exactly while designing a separately frozen external-survey adapter.