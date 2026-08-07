#!/usr/bin/env python3
"""Zero-data semantic adjudication of the sole corrected UKMON 2020/2021 audit hit.

This script does not rerun or relax the raw audit. It consumes the immutable artifact
from run 31225365557 and accepts only the exact single hit already reported there,
then verifies from repository source context that the hit is the explicit spent-SAAMER
positive control of the older UKMON 2024/2025 freshness audit.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)
RAW = Path("input_audit/ukmon_2020_2021_repo_freshness_audit.json")

EXPECTED = {
    "run_id": 31225365557,
    "job_id": 93018463154,
    "artifact_id": 9011892667,
    "artifact_zip_sha256": "e1bc2687a08c0812b123f5741beb429134940baff76cbb7f172c9a9836aef0b9",
    "ref": "refs/remotes/origin/agent/orbittrace-label-free-v6-ukmon-2024-2025-external",
    "path": "orbittrace_ukmon_2024_2025_freshness_audit/audit_history.py",
    "line": 50,
    "reason": "literal_target_year_in_ukmon_related_file",
    "text": "    saamer=collect(rs,[r'iaumdcSAAMER2020|SAAMER 2020-2021 external validation'])",
}


def git_show(ref: str, path: str) -> str:
    p = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        text=True,
        capture_output=True,
        errors="replace",
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return p.stdout


def main() -> int:
    if not RAW.exists():
        raise RuntimeError(f"missing frozen audit result: {RAW}")
    raw = json.loads(RAW.read_text())

    # Preserve the raw audit as a FAIL; this adjudication may not rewrite it.
    assert raw["verdict"] == "FAIL_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    assert raw["candidate_years"] == [2020, 2021]
    assert raw["potential_exposure_hit_count"] == 1
    assert raw["positive_controls"] == {
        "ukmon_2022_interface_detected": True,
        "ukmon_2024_2025_external_detected": True,
    }
    for k in (
        "catalogue_access_this_audit",
        "meteor_api_contacted",
        "scientific_value_access_this_audit",
        "label_access_this_audit",
        "target_information_access",
    ):
        assert raw[k] is False

    hit = raw["potential_exposure_hits"][0]
    for k in ("ref", "path", "line", "reason", "text"):
        assert hit[k] == EXPECTED[k], (k, hit[k], EXPECTED[k])

    source = git_show(EXPECTED["ref"], EXPECTED["path"])
    lines = source.splitlines()
    assert len(lines) >= 54
    assert lines[48].strip() == "# Positive controls must prove history search reaches spent survey work."
    assert lines[49] == EXPECTED["text"]
    assert lines[50].strip().startswith("sonotaco=collect(")
    assert lines[51].strip().startswith("pc_saamer=any(")
    assert lines[52].strip().startswith("pc_sonotaco=any(")

    # The target-year literal is semantically scoped to the SAAMER positive control,
    # not to a UKMON target-year URL, date iterator, parser, payload, or scientific result.
    line = lines[49]
    assert "SAAMER 2020-2021 external validation" in line
    assert "saamer=collect" in line
    assert "ukmeteors" not in line.lower()
    assert "ukmon" not in line.lower()
    assert "reqval" not in line.lower()
    assert "matches" not in line.lower()
    assert "summary" not in line.lower()

    result = {
        "verdict": "PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION",
        "raw_audit_verdict_preserved": raw["verdict"],
        "raw_audit_run_id": EXPECTED["run_id"],
        "raw_audit_job_id": EXPECTED["job_id"],
        "raw_audit_artifact_id": EXPECTED["artifact_id"],
        "raw_audit_artifact_zip_sha256": EXPECTED["artifact_zip_sha256"],
        "raw_hit_count": 1,
        "adjudicated_hit": hit,
        "adjudication": "non_UKMON_spent_SAAMER_positive_control",
        "additional_hits_forgiven": 0,
        "catalogue_access_this_adjudication": False,
        "meteor_api_contacted": False,
        "scientific_value_access_this_adjudication": False,
        "label_access_this_adjudication": False,
        "target_information_access": False,
        "claim_boundary": (
            "The corrected raw audit remains a recorded FAIL because it conservatively flagged one literal 2020/2021 mention. "
            "This separate immutable-artifact/source adjudication establishes that the sole hit is explicitly the spent-SAAMER positive control "
            "inside the older UKMON 2024/2025 freshness-audit source, not evidence that UKMON 2020/2021 meteor data were queried, parsed, or scientifically used. "
            "No additional raw-audit hit is admissible. On repository-history evidence, UKMON 2020/2021 may proceed to a separately frozen pre-scientific structure/interface audit."
        ),
    }
    (OUT / "ukmon_2020_2021_freshness_adjudication.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
