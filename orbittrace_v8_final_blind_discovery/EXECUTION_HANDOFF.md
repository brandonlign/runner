# Final v8 discovery execution handoff

This file defines the only allowed operational inputs after this freeze. It does not authorize Stage A or Stage B.

## A. Freeze-manifest preflight

Run the source-only workflow `.github/workflows/orbittrace_v8_final_blind_freeze_audit.yml` on the exact final branch commit. It must produce:

- `PASS_V8_FINAL_BLIND_SOURCE_AUDIT`;
- `FREEZE_MANIFEST.json`;
- `v8_final_blind_source_audit.json`;
- no catalogue access;
- no target-region access;
- no withheld-reference access.

The exact `freeze_commit` and SHA-256 of `FREEZE_MANIFEST.json` are inputs to the external authorization object below. A later source edit necessarily changes the manifest and invalidates the authorization.

## B. Withheld-reference bundle, prepared without Stage A access

A separate reference custodian/process prepares one ZIP artifact containing exactly one file named `withheld_reference.json` with this schema:

```json
{
  "schema": "orbittrace-withheld-reference-v1",
  "events": [
    {"event_id": "<stable GMN trajectory identifier>", "month_key": "YYYY-MM"}
  ]
}
```

Rules are frozen:

- every event object has exactly `event_id` and `month_key`;
- IDs are nonempty and unique;
- every `month_key` must belong to the Stage A universe: all months in 2022-2025 plus January-July 2026;
- the bundle contains the complete canonical withheld-reference member set within that exact Stage A month universe, not a hand-picked subset;
- no coordinate, radiant, speed, orbit, activity, family rank, or detector score is included or needed;
- the ZIP SHA-256 is computed before Stage A and sealed into the authorization object;
- the authorization object must **not** include the reference artifact ID/URL/locator, so Stage A cannot retrieve it.

## C. External-validation authorization artifact

Only the separate external-validation track may create the authorization artifact after it has independently decided that the frozen v8 method is authorized for final blind GMN application.

The authorization ZIP contains exactly one `external_validation_authorization.json` with:

```json
{
  "schema": "orbittrace-v8-final-discovery-authorization-v1",
  "decision": "AUTHORIZE_FINAL_GMN_BLIND_DISCOVERY",
  "method_commit": "c9d6c44704013ba0c9430100e98a29a56b453304",
  "v8_development_artifact_sha256": "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e",
  "freeze_commit": "<exact 40-hex final freeze commit>",
  "freeze_manifest_sha256": "<exact 64-hex FREEZE_MANIFEST.json SHA-256>",
  "external_validation": {
    "artifact_id": "<external-validation result artifact ID>",
    "artifact_sha256": "<64-hex result artifact SHA-256>",
    "verdict": "<external-validation track's immutable verdict>"
  },
  "sealed_withheld_reference_artifact_sha256": "<64-hex reference ZIP SHA-256>",
  "withheld_reference_schema": "orbittrace-withheld-reference-v1"
}
```

The authorization checker accepts only the exact `decision` string above. It does not reinterpret or tune the detector based on the external result. The external-validation track is responsible for issuing this object only when its own preregistered rules permit final application.

## D. Stage A dispatch

Dispatch `.github/workflows/orbittrace_v8_final_blind_stage_a.yml` on the exact `freeze_commit` and supply only:

- `authorization_artifact_id`;
- `authorization_artifact_sha256`.

The workflow verifies the code/source manifest and authorization before the first target-containing GMN access. It has no withheld-reference artifact locator. It then runs the frozen scanner and writes every family/rank. After `blind_families.json` has already been hashed, `seal_stage_a.py` attaches the opaque pre-sealed reference digest and external-validation provenance to `stage_a_freeze.json` without changing the ranking payload.

Do not inspect or interpret Stage A families before preserving the uploaded Stage A artifact ID and ZIP digest.

## E. Stage B dispatch

Only after Stage A is immutable, dispatch `.github/workflows/orbittrace_v8_final_blind_stage_b.yml` on the same exact freeze commit and supply:

- `stage_a_artifact_id`;
- `stage_a_artifact_sha256`;
- `withheld_reference_artifact_id`;
- `withheld_reference_artifact_sha256`.

Before reference download, Stage B verifies:

- Stage A ZIP digest;
- Stage A inner ranked-family hash;
- all Stage A integrity gates;
- current Git commit equals Stage A's frozen commit;
- current source-manifest digest equals Stage A's frozen manifest digest;
- requested reference ZIP digest equals the opaque digest sealed before Stage A.

Only after those checks pass does the workflow download the reference and apply the exact-ID full/partial/no-recovery rules in `PROTOCOL.md`.

## F. Prohibited recovery actions

A failed authorization, source audit, Stage A integrity gate, artifact digest, or Stage B preflight is a failed/invalid execution. It does not permit changing scientific settings. The later session may correct a purely operational identifier/digest transcription error and rerun the same immutable commit, but it may not change input months, cuts, detector code, family semantics, score/ranking, reference membership rule, rank depth, or reveal threshold.
