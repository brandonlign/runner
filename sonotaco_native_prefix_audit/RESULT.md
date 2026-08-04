# SonotaCo 2025 survey-native prefix audit: authoritative pass

Runner workflow `30877123487` completed the prospectively frozen aggregate-only audit. Artifact `8879922111` was preserved with digest `sha256:0d9cec37d71ad753326f5945309ca4c95d79209d02c1b9948a29047b2e10e859`.

The single universal rule `^([A-Z0-9]{3})_JA$` mapped the captured three-character prefix to the canonical shower code. `SPO` remained background. No alias table, fuzzy match, suffix list, or per-shower exception was used.

## Result

- all **36,826** rows parsed;
- **1,372** GhostStream-interval rows removed before every aggregate;
- geometry completeness **0.999972**;
- uncertainty completeness **1.000000**;
- **24,052** reservoir-ready background rows;
- native syntax fraction **1.000000**;
- matched native reservoir fraction **0.943426**;
- **10,756** matched reservoir rows;
- **645** unmatched-prefix reservoir rows;
- **34** supported matched shower codes;
- **31** supported complex/parent units.

All eleven frozen gates passed.

Verdict: **`PASS_SONOTACO_2025_NATIVE_PREFIX_AUDIT`**.

This authorizes only a separately frozen SonotaCo-2025 scientific development benchmark of the exact coverage-normalized Mondrian quartet. SonotaCo 2024 remains untouched and value-blinded under PR #63. No result here authorizes a GhostStream application or catalogue scan.