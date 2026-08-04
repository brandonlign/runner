# CAMSv3 structural feasibility parser-v1 result

**Verdict:** `KILL_CAMSV3_STRUCTURAL_FEASIBILITY`

Runner workflow `30879982868` completed the frozen six-year structural audit and preserved artifact `8880907906`, digest `sha256:a33007470c6f215091ecc19d56d45a883362514005f8d08a5dd42d2946d219cb`.

All six official 2011–2016 archives matched their predeclared SHA-256 hashes. Every ZIP passed CRC and safe-path checks. All six files parsed as UTF-8-SIG semicolon CSV with the pinned row counts, zero malformed rows, the exact required geometry fields, and one identical 63-field header.

The sole failed gate was exact member-path equality in every year. The archives contain the pinned CSV basenames under a directory prefix, while parser v1 required the full ZIP member path to equal the basename exactly.

No data-column value, shower-label token, score, calibration window, scientific endpoint, SonotaCo 2024 value, or GhostStream value was read.

Parser v1 remains killed. A separately frozen parser-v2 gate may change only member selection from exact full-path equality to exact `PurePosixPath(member).name` equality, while requiring exactly one matching CSV and preserving every archive hash, member basename, row count, delimiter, field, and no-value boundary.
