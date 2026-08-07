#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

EXPECTED = {
    "ref": "refs/remotes/origin/agent/orbittrace-fripon-2018-2019-freshness-audit",
    "path": "orbittrace_harvard_1968_1969_freshness_audit/PROTOCOL.md",
    "line": 26,
    "text": "- **DMS, Hissar, FRIPON, and current photographic collections:** public individual-orbit products exist but are materially smaller than the strongest remaining coherent two-year historical radar panel. They are not opened or cycled through here.",
}


def show(ref: str, path: str) -> str:
    p = subprocess.run(["git", "show", f"{ref}:{path}"], text=True, capture_output=True, errors="replace")
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-json", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    raw = json.loads(a.raw_json.read_text())
    assert raw["verdict"] == "FAIL_HISSAR_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    assert raw["potential_exposure_hit_count"] == 1
    assert all(raw["positive_controls"].values())
    for key in ("iau_mdc_contacted", "catalogue_form_submitted", "scientific_record_access", "source_label_access", "orbittrace_target_information_access"):
        assert raw[key] is False
    hit = raw["potential_exposure_hits"][0]
    for key in ("ref", "path", "line", "text"):
        assert hit[key] == EXPECTED[key], (key, hit[key], EXPECTED[key])

    src = show(EXPECTED["ref"], EXPECTED["path"]).splitlines()
    assert src[22].strip() == "### Screened catalogue classes"
    assert src[25] == EXPECTED["text"]
    assert "They are not opened or cycled through here." in src[25]
    assert src[28].strip() == "## Single next candidate"
    assert "Harvard Radar Meteor Project" in src[29]
    assert "Selection is metadata-only" in src[31]

    result = {
        "verdict": "PASS_HISSAR_1968_1969_ZERO_DATA_FRESHNESS_ADJUDICATION",
        "raw_audit_verdict_preserved": raw["verdict"],
        "raw_audit_run_id": 31227497479,
        "raw_audit_artifact_id": 9012608649,
        "raw_audit_artifact_zip_sha256": "93eca9bc5513f8d569b7643d0f8c36ed3bc42b1ef6d9f6755e1ce09a05090b75",
        "raw_hit_count": 1,
        "additional_hits_forgiven": 0,
        "adjudicated_hit": hit,
        "adjudication": "metadata_only_explicit_nonuse_in_prior_catalogue_screen",
        "iau_mdc_contacted": False,
        "catalogue_form_submitted": False,
        "scientific_record_access": False,
        "source_label_access": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": "The conservative raw FAIL remains preserved. Exact repository context proves its sole hit is a metadata-only screened-catalogue statement explicitly saying Hissar was not opened or cycled through. No additional hit is admissible; Hissar may proceed only to a separately frozen pre-scientific interface audit.",
    }
    (a.output / "hissar_1968_1969_freshness_adjudication.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
