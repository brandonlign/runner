# Final v8 discovery execution handoff

This file defines the only allowed operational inputs after this freeze. It does not authorize Stage A or Stage B. The target-containing workflows are deliberately **not directly dispatchable**. They can run only from execution-only child pull requests against `agent/orbittrace-v8-final-blind-discovery-freeze`, and each workflow rejects any child diff other than its single request JSON.

## A. Freeze-manifest preflight

Open/maintain the freeze PR from `agent/orbittrace-v8-final-blind-discovery-freeze` against the exact v8 parent. The source-only workflow `.github/workflows/orbittrace_v8_final_blind_freeze_audit.yml` must pass on the exact final freeze commit and produce:

- `PASS_V8_FINAL_BLIND_SOURCE_AUDIT`;
- `FREEZE_MANIFEST.json`;
- `v8_final_blind_source_audit.json`;
- no catalogue access;
- no target-region access;
- no withheld-reference access;
- no Stage A or Stage B execution request present on the freeze branch;
- target workflows not directly dispatchable.

The exact `freeze_commit` and SHA-256 of `FREEZE_MANIFEST.json` are inputs to the external authorization object below. Any later freeze-branch source edit changes the manifest and invalidates the authorization.

## B. Withheld-reference bundle, prepared without Stage A access

A separate reference custodian/process prepares one ZIP artifact containing exactly one file named `withheld_reference.json`. Its machine-readable schema is frozen at `WITHHELD_REFERENCE.schema.json` (`orbittrace-withheld-reference-v1`). The logical shape is:

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
- every `month_key` belongs to the Stage A universe: all months in 2022-2025 plus January-July 2026;
- the bundle contains the complete canonical withheld-reference member set within that exact Stage A month universe, not a selected subset;
- no coordinate, radiant, speed, orbit, activity, family rank, or detector score is included or needed;
- the ZIP SHA-256 is computed before Stage A and sealed into the authorization object;
- the authorization object must not include the reference artifact ID/URL/locator, so Stage A cannot retrieve it.

## C. External-validation authorization artifact

Only the separate external-validation track may create the authorization artifact after it has independently decided that the frozen v8 method is authorized for final blind GMN application.

The authorization ZIP contains exactly one `external_validation_authorization.json`. Its machine-readable schema is `EXTERNAL_AUTHORIZATION.schema.json` (`orbittrace-v8-final-discovery-authorization-v1`). It contains exactly:

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

## D. Stage A execution-only child PR

After authorization exists, create a child branch **from the exact frozen commit** and add exactly one new file:

`orbittrace_v8_final_blind_discovery/STAGE_A_EXECUTION_REQUEST.json`

The file must satisfy `STAGE_A_EXECUTION_REQUEST.schema.json` and contain only:

```json
{
  "schema": "orbittrace-v8-stage-a-execution-request-v1",
  "freeze_commit": "<exact frozen commit>",
  "authorization_artifact_id": "<digits only>",
  "authorization_artifact_sha256": "<64-hex authorization ZIP SHA-256>"
}
```

Open that child PR with base `agent/orbittrace-v8-final-blind-discovery-freeze`. The Stage A workflow uses `pull_request_target`, verifies the child is same-repository, verifies the complete child diff is exactly that one request file, checks out the **base freeze SHA rather than child code**, regenerates the exact source manifest, verifies the authorization, and only then begins target-containing GMN access.

The Stage A request schema deliberately has no withheld-reference artifact ID or locator. The workflow writes every family/rank. Only after `blind_families.json` is hashed does `seal_stage_a.py` attach the opaque pre-sealed reference digest and external-validation provenance to `stage_a_freeze.json`; the ranked-family payload itself is unchanged.

Do not inspect or interpret Stage A families before preserving the uploaded Stage A artifact ID and ZIP digest.

## E. Stage B execution-only child PR

Only after Stage A is immutable, create a fresh child branch **from the same exact frozen commit** and add exactly one new file:

`orbittrace_v8_final_blind_discovery/STAGE_B_EXECUTION_REQUEST.json`

The file must satisfy `STAGE_B_EXECUTION_REQUEST.schema.json` and contain only:

```json
{
  "schema": "orbittrace-v8-stage-b-execution-request-v1",
  "freeze_commit": "<same exact frozen commit>",
  "stage_a_artifact_id": "<digits only>",
  "stage_a_artifact_sha256": "<64-hex Stage A ZIP SHA-256>",
  "withheld_reference_artifact_id": "<digits only>",
  "withheld_reference_artifact_sha256": "<64-hex pre-sealed reference ZIP SHA-256>"
}
```

Open that child PR with base `agent/orbittrace-v8-final-blind-discovery-freeze`. Before reference download, Stage B verifies:

- the child diff is exactly the one Stage B request file;
- scientific code comes from the frozen base SHA, not the child;
- Stage A ZIP digest;
- Stage A inner ranked-family hash;
- all Stage A integrity gates;
- current Git commit equals Stage A's frozen commit;
- current source-manifest digest equals Stage A's frozen manifest digest;
- requested reference ZIP digest equals the opaque digest sealed before Stage A.

Only after those checks pass does the workflow retrieve the reference and apply the exact-ID full/partial/no-recovery rules in `PROTOCOL.md`.

## F. Prohibited recovery actions

A failed authorization, source audit, execution-only diff guard, Stage A integrity gate, artifact digest, or Stage B preflight is a failed/invalid execution. It does not permit changing scientific settings. A later session may correct a purely operational artifact ID/digest transcription error by replacing only the relevant execution-request child branch and rerunning the same immutable base commit, but it may not change input months, cuts, detector code, family semantics, score/ranking, reference membership rule, rank depth, or reveal threshold.
