#!/usr/bin/env python3
"""Validate external authorization without accessing GMN or the withheld reference."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

V8_PARENT_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
V8_DEVELOPMENT_ARTIFACT_SHA256 = "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--freeze-manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.freeze_manifest.read_text())
    manifest_sha = hashlib.sha256(args.freeze_manifest.read_bytes()).hexdigest()
    require(manifest.get("schema") == "orbittrace-v8-final-blind-freeze-v1", "wrong freeze manifest schema")
    require(manifest.get("v8_parent_commit") == V8_PARENT_COMMIT, "freeze manifest v8 parent mismatch")
    require(manifest.get("v8_development_artifact_sha256") == V8_DEVELOPMENT_ARTIFACT_SHA256, "freeze manifest v8 artifact mismatch")
    freeze_commit = str(manifest.get("freeze_commit", ""))
    require(bool(HEX40.fullmatch(freeze_commit)), "freeze manifest commit invalid")

    with zipfile.ZipFile(args.artifact) as zf:
        names = [name for name in zf.namelist() if name.endswith("external_validation_authorization.json")]
        require(len(names) == 1, f"authorization artifact must contain exactly one authorization JSON: {names}")
        auth = json.loads(zf.read(names[0]).decode("utf-8"))
    require(auth.get("schema") == "orbittrace-v8-final-discovery-authorization-v1", "wrong authorization schema")
    require(auth.get("decision") == "AUTHORIZE_FINAL_GMN_BLIND_DISCOVERY", "external validation did not authorize final blind discovery")
    require(auth.get("method_commit") == V8_PARENT_COMMIT, "authorization method commit mismatch")
    require(auth.get("v8_development_artifact_sha256") == V8_DEVELOPMENT_ARTIFACT_SHA256, "authorization v8 artifact mismatch")
    require(auth.get("freeze_commit") == freeze_commit, "authorization does not bind exact execution commit")
    require(auth.get("freeze_manifest_sha256") == manifest_sha, "authorization does not bind exact source manifest")
    external = auth.get("external_validation")
    require(isinstance(external, dict), "external-validation provenance missing")
    require(str(external.get("artifact_id", "")).strip() != "", "external-validation artifact ID missing")
    require(bool(HEX64.fullmatch(str(external.get("artifact_sha256", "")))), "external-validation artifact SHA-256 missing/invalid")
    require(str(external.get("verdict", "")).strip() != "", "external-validation verdict missing")
    sealed_reference = str(auth.get("sealed_withheld_reference_artifact_sha256", ""))
    require(bool(HEX64.fullmatch(sealed_reference)), "sealed withheld-reference artifact SHA-256 missing/invalid")
    require(auth.get("withheld_reference_schema") == "orbittrace-withheld-reference-v1", "withheld-reference schema mismatch")
    require("withheld_reference_artifact_id" not in auth, "authorization must not expose a reference artifact locator to Stage A")
    result = {
        "schema": "orbittrace-v8-stage-a-authorization-check-v1",
        "verdict": "PASS_EXTERNAL_VALIDATION_AUTHORIZATION",
        "decision": auth["decision"],
        "method_commit": auth["method_commit"],
        "v8_development_artifact_sha256": auth["v8_development_artifact_sha256"],
        "freeze_commit": freeze_commit,
        "freeze_manifest_sha256": manifest_sha,
        "external_validation": external,
        "sealed_withheld_reference_artifact_sha256": sealed_reference,
        "withheld_reference_schema": auth["withheld_reference_schema"],
        "withheld_reference_access": False,
        "target_region_data_access": False,
    }
    path = args.output / "stage_a_authorization.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
