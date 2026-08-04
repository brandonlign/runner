# Seven-year real-shower feasibility manifest v1: infrastructure no-go

Runner workflow `30881045533` stopped before retrieving the prior audit artifact or downloading any GMN monthly source.

The exact PR #14 commit and file path were fetched successfully, but the workflow incorrectly supplied GitHub's 40-character Git blob identifier `4a029051230f7c6e99b09e911f8a9e5228a58783` to `sha256sum`, which requires a 64-character SHA-256 digest. The checksum line was therefore syntactically invalid.

No monthly source, meteor row, solar longitude, shower label, quality field, support count, detector score, or GhostStream-region value was read.

Verdict: **`KILL_REAL_SHOWER_FEASIBILITY_MANIFEST_V1`**.

This does not adjudicate data availability or scientific feasibility. A separately recorded manifest-v2 repair may verify the exact immutable source by commit plus Git blob SHA and record the file SHA-256 as provenance output, while preserving every scientific source, year, month, blind interval, support definition, gate, and no-score boundary.