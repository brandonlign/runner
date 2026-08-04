# SonotaCo 2025 label-token audit: authoritative no-go

Runner workflow `30876271770` completed the prospectively frozen aggregate-only audit. Artifact `8879636252` was preserved with digest `sha256:3bef946b023858ecb10a2bde846a43a870a27a658d4ab5b58c79c1021a899ba6`.

## Result

Structural and geometry readiness were excellent:

- all 36,826 published rows parsed;
- 35,453 rows were geometry-ready outside the blind interval;
- geometry completeness was **0.999972**;
- uncertainty completeness was **1.000000**;
- 24,052 deterministic background-reservoir rows were available.

But the exact predeclared label-token mapping found:

- matched reservoir rows: **0**;
- supported matched shower codes: **0**;
- supported matched complex/parent units: **0**;
- unmatched labeled rows: **11,401**.

The survey tokens use survey-native forms such as `GEM_JA`, `PER_JA`, and `SDA_JA`, while the frozen exact MDC mapping contains canonical codes without that suffix. Because the protocol explicitly forbade aliases or post-audit token normalization, both continuation gates failed.

Verdict: **`KILL_SONOTACO_2025_LABEL_AUDIT`**.

No suffix stripping, alias table, background reassignment, support relaxation, or year substitution is authorized for this formulation. The archive remains potentially useful for a separately prospectively designed survey-native study, but it is no longer an untouched confirmation source for a mapping rule chosen after observing these aggregate tokens.
