# SonotaCo 2025 survey-native prefix audit: authoritative pass

Runner workflow `30877123487` completed the frozen aggregate-only support audit. Artifact `8879922111` was preserved with digest `sha256:0d9cec37d71ad753326f5945309ca4c95d79209d02c1b9948a29047b2e10e859`.

Every frozen gate passed:

- all 36,826 rows structurally parsed;
- 1,372 blind-interval rows removed before all aggregates;
- geometry completeness **0.999972**;
- reservoir-ready background **24,052**;
- uncertainty completeness **1.000000**;
- all **11,401 / 11,401** nonbackground label rows matched the single exact `XXX_JA` syntax;
- **10,756 / 11,401 = 0.943426** reservoir-ready native labels mapped through their three-character prefix to an eligible frozen code;
- **34** supported matched codes with at least 20 rows;
- **31** supported complex/parent keys.

Pinned source and input hashes:

- prefix-audit source: `41e4ad94714f1825939bcfb153b7fcc81cce34aeef76f0dae48c493758061755`;
- SonotaCo archive: `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`;
- SonotaCo member: `30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7`;
- PR #14 GMN/MDC audit: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

Verdict: **`PASS_SONOTACO_2025_NATIVE_PREFIX_AUDIT`**.

The single generic rule is therefore sufficiently broad and precise for survey-native development. This pass authorizes only a separately frozen SonotaCo 2025 scientific screen of the coverage-normalized 10° Mondrian quartet. SonotaCo 2024 remains label- and value-blinded; no GhostStream or catalogue application is authorized. Keep this PR closed, draft, and unmerged as the support record.