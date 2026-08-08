# Terminal synthesis authoritative artifact-metadata correction

Frozen after failed guard-fixed run `31229474180` and **before any further terminal-synthesis execution**.

That run completed all source guards and the repository branch-name inventory, then downloaded the SAAMER 2020/2021 artifact successfully but stopped because the copied ZIP digest was wrong. `synthesize.py` did not execute. No external catalogue/web service or new scientific value was accessed.

To eliminate serial bookkeeping repairs, every result artifact used by the terminal synthesis was rechecked directly against GitHub Actions artifact metadata. The following IDs/digests are authoritative:

- promoted v8 development — run `31217916558`, artifact `9009728299`, SHA-256 `88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- SAAMER 2020/2021 — run `31210007928`, artifact `9006709213`, SHA-256 `e96e736b4e1d541fb4334d57bf20692404920e616857b783c88d1acba17a77f0`;
- SAAMER 2022/2023 — run `31212256679`, artifact `9007437717`, SHA-256 `0e4482d750d8dea93ef56205180b4d456aaedc4adb6dc04d9239a35ab32cab50`;
- AMOR 1996/1998 direct v8 — run `31221745373`, artifact `9010704319`, SHA-256 `474cbd33dab03b7866da1e0b4c5640824347655e2d1ad336076a752291146763`;
- UKMON 2020/2021 freshness adjudication — run `31225516384`, artifact `9011943529`, SHA-256 `d44e0673683045683ca78fd79642b4afa1b9495e3586aa6a3e4bd29a1445424a`;
- Harvard recurrence eligibility — run `31227232530`, artifact `9012522244`, SHA-256 `7d9e68ec6f5f9790613869316839f9b6e5cb29c3a0c17f360dd244b0d6531c67`;
- FRIPON integrity stop — run `31228163688`, artifact `9012820047`, SHA-256 `e4251f178a8a47ac11a4d99b5470badb6f589bc3c897ac8fcebc70f381b85428`;
- Hissar v8 coverage eligibility — run `31228541893`, artifact `9012940108`, SHA-256 `b9dbc7374184c00cf39906c53a1ac13c17c30429c04f6184a2a7931c6208a0de`;
- UKMON first pre-scientific structure failure — run `31225678351`, artifact `9012001791`, SHA-256 `08dc0b6de876733c2de8ce6079487ee5b3bdb1245bb98bc63da84c41566e4dfa`;
- UKMON deterministic transport-fallback failure — run `31225913104`, artifact `9012076689`, SHA-256 `404f24e581d70d9141e1407622bf22300320492f77691a384bf11a8455e0e5d7`.

This note supersedes only stale artifact-ID/digest bookkeeping in earlier terminal-synthesis drafts/correction notes. It does **not** alter any serialized result, panel status, N/Q count, method parameter, external power floor, pass/fail rule, or target boundary.

The corrected scientific record remains:
- SAAMER 2020/2021: `N=69`, `Q=29`, power-inconclusive;
- SAAMER 2022/2023: `N=66`, `Q=33`, power-inconclusive;
- direct v8 AMOR 1996/1998: `N=19`, `Q=19`, power-inconclusive;
- UKMON historical pair: interface-incompatible before science;
- Harvard: recurrence-ineligible before event-table access;
- FRIPON: integrity-disqualified before reserved scientific protocol;
- Hissar: coverage-ineligible before catalogue form submission.

No method change, power-floor relaxation, successor detector, target reveal, or OrbitTrace target access is authorized by this correction.