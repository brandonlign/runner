#!/usr/bin/env python3
"""Synthetic-only tests for OrbitTrace post-development guards."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
AUTHORIZE = ROOT / "authorize_validation.py"
FREEZE = ROOT / "freeze_development_result.py"
RESCUE_QUEUE = "fixed4 p <= 1/129; never inserted into wavelet ranking"


def run(*args: str, expect_success: bool) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if (completed.returncode == 0) != expect_success:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def valid_result() -> dict:
    return {
        "verdict": "PASS_WAVELET_CATALOGUE_V3_DEVELOPMENT",
        "configuration": {
            "years": [2022, 2023],
            "blind_exclusion": [20.0, 55.0],
            "rescue_alpha": 1.0 / 129.0,
            "rescue_queue": RESCUE_QUEUE,
        },
        "gates": {
            "self_tests": True,
            "source_exclusion": True,
            "recovery": True,
            "precision": True,
        },
    }


def write_json(path: Path, value: dict) -> str:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        result_path = work / "development.json"
        authorization_path = work / "authorization.json"
        manifest_path = work / "manifest.json"

        digest = write_json(result_path, valid_result())
        run(
            str(AUTHORIZE),
            str(result_path),
            "--expected-sha256",
            digest,
            "--output",
            str(authorization_path),
            expect_success=True,
        )
        run(
            str(FREEZE),
            str(result_path),
            str(authorization_path),
            "--output",
            str(manifest_path),
            expect_success=True,
        )
        manifest_first = manifest_path.read_bytes()
        run(
            str(FREEZE),
            str(result_path),
            str(authorization_path),
            "--output",
            str(manifest_path),
            expect_success=True,
        )
        assert manifest_path.read_bytes() == manifest_first
        manifest = json.loads(manifest_first)
        assert manifest["held_out_catalogues_loaded_by_this_freeze"] is False
        assert manifest["orbittrace_reference_loaded_by_this_freeze"] is False
        assert manifest["scientific_tuning_authorized"] is False

        failed = valid_result()
        failed["verdict"] = "FAIL_WAVELET_CATALOGUE_V3_DEVELOPMENT"
        failed_path = work / "failed.json"
        write_json(failed_path, failed)
        run(
            str(AUTHORIZE),
            str(failed_path),
            "--output",
            str(work / "should_not_exist.json"),
            expect_success=False,
        )

        gate_failure = valid_result()
        gate_failure["gates"]["precision"] = False
        gate_failure_path = work / "gate_failure.json"
        write_json(gate_failure_path, gate_failure)
        run(
            str(AUTHORIZE),
            str(gate_failure_path),
            "--output",
            str(work / "should_not_exist_2.json"),
            expect_success=False,
        )

        run(
            str(AUTHORIZE),
            str(result_path),
            "--expected-sha256",
            "0" * 64,
            "--output",
            str(work / "should_not_exist_3.json"),
            expect_success=False,
        )

        tampered_authorization = json.loads(authorization_path.read_text())
        tampered_authorization["development_result_sha256"] = "f" * 64
        tampered_path = work / "tampered_authorization.json"
        write_json(tampered_path, tampered_authorization)
        run(
            str(FREEZE),
            str(result_path),
            str(tampered_path),
            "--output",
            str(work / "should_not_exist_4.json"),
            expect_success=False,
        )

    print("PASS_POSTPASS_GUARDS_SYNTHETIC_ONLY")


if __name__ == "__main__":
    main()
