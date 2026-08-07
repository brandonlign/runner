#!/usr/bin/env python3
"""Attach predata authorization provenance after the blind ranking is already frozen."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage-a-freeze", required=True, type=Path)
    p.add_argument("--authorization-json", required=True, type=Path)
    p.add_argument("--freeze-manifest", required=True, type=Path)
    args = p.parse_args()
    freeze = json.loads(args.stage_a_freeze.read_text())
    auth = json.loads(args.authorization_json.read_text())
    manifest = json.loads(args.freeze_manifest.read_text())
    manifest_sha = hashlib.sha256(args.freeze_manifest.read_bytes()).hexdigest()
    require(freeze.get("verdict") == "PASS_STAGE_A_BLIND_DISCOVERY_FREEZE", "blind ranking was not successfully frozen")
    require(freeze.get("withheld_reference_loaded") is False and freeze.get("target_identity_available") is False, "Stage A blindness was violated")
    require(auth.get("verdict") == "PASS_EXTERNAL_VALIDATION_AUTHORIZATION", "authorization check failed")
    require(auth.get("freeze_manifest_sha256") == manifest_sha, "authorization/freeze manifest mismatch")
    require(auth.get("freeze_commit") == manifest.get("freeze_commit"), "authorization/freeze commit mismatch")
    require(freeze.get("freeze_manifest_sha256") == manifest_sha, "Stage A used a different freeze manifest")
    freeze["authorization_verdict"] = auth["verdict"]
    freeze["external_validation"] = auth["external_validation"]
    freeze["freeze_commit"] = auth["freeze_commit"]
    freeze["sealed_withheld_reference_artifact_sha256"] = auth["sealed_withheld_reference_artifact_sha256"]
    freeze["withheld_reference_schema"] = auth["withheld_reference_schema"]
    freeze["authorization_attached_after_blind_ranking_freeze"] = True
    args.stage_a_freeze.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": freeze["verdict"],
        "blind_families_sha256": freeze["blind_families_sha256"],
        "authorization_attached_after_blind_ranking_freeze": True,
        "withheld_reference_loaded": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
