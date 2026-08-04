#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_records(manifest: dict[str, Any]) -> list[tuple[str, int, str]]:
    classification = manifest["classification_audit"]
    return [
        (
            "canonical_discovery",
            int(manifest["canonical_discovery"]["artifact_id"]),
            str(manifest["canonical_discovery"]["artifact_zip_sha256"]),
        ),
        (
            "independent_method_recovery",
            int(manifest["independent_method_recovery"]["artifact_id"]),
            str(manifest["independent_method_recovery"]["artifact_zip_sha256"]),
        ),
        (
            "classification_real_member_gate",
            int(classification["real_member_gate"]["artifact_id"]),
            str(classification["real_member_gate"]["artifact_zip_sha256"]),
        ),
        (
            "classification_solution004_provenance",
            int(classification["solution004_provenance"]["artifact_id"]),
            str(classification["solution004_provenance"]["artifact_zip_sha256"]),
        ),
        (
            "classification_multisource_orbit_recovery",
            int(classification["multisource_orbit_recovery"]["artifact_id"]),
            str(classification["multisource_orbit_recovery"]["artifact_zip_sha256"]),
        ),
        (
            "classification_static_population_calibration",
            int(classification["static_population_calibration"]["artifact_id"]),
            str(classification["static_population_calibration"]["artifact_zip_sha256"]),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)

    gates: dict[str, bool] = {
        "schema_exact": manifest.get("schema") == "ghoststream-final-scientific-synthesis-v1",
        "canonical_151_of_151": manifest["canonical_discovery"].get("package_checks") == "151/151",
        "method_full_frozen_recovery": manifest["independent_method_recovery"].get("verdict")
        == "FULL_FROZEN_GHOSTSTREAM_RECOVERY",
        "method_all_14_gates": bool(manifest["independent_method_recovery"].get("all_frozen_gates_passed"))
        and int(manifest["independent_method_recovery"].get("gate_count", 0)) == 14,
        "method_calibration_recorded": manifest["independent_method_recovery"].get("fpr_alpha_005")
        == 0.0515625
        and manifest["independent_method_recovery"].get("fpr_alpha_001") == 0.00703125,
        "classification_real_member_gate_preserved": manifest["classification_audit"]["real_member_gate"].get(
            "verdict"
        )
        == "KILL_DYNAMICAL_BRANCH_CLASSIFICATION_DATA_GATE",
        "classification_solution004_provenance_preserved": manifest["classification_audit"][
            "solution004_provenance"
        ].get("verdict")
        == "SOLUTION004_OBSERVATIONALLY_COHERENT_BUT_NO_ORBIT_CLONES",
        "classification_recovery_failure_preserved": manifest["classification_audit"][
            "multisource_orbit_recovery"
        ].get("verdict")
        == "KILL_MULTISOURCE_RECOVERY_INSUFFICIENT",
        "classification_static_failure_preserved": manifest["classification_audit"][
            "static_population_calibration"
        ].get("verdict")
        == "STATIC_CLASSIFIER_NOT_VALID",
        "distinct_status_unresolved": manifest["final_position"].get("distinct_vs_nop_solution004")
        == "unresolved from available public member-level orbit data",
    }

    artifact_checks: list[dict[str, Any]] = []
    for name, artifact_id, expected in artifact_records(manifest):
        path = args.input / f"{artifact_id}.zip"
        actual = sha256(path) if path.exists() else None
        passed = actual == expected
        gates[f"artifact_{artifact_id}_sha_exact"] = passed
        artifact_checks.append(
            {
                "name": name,
                "artifact_id": artifact_id,
                "path": str(path),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "passed": passed,
            }
        )

    verdict = (
        "PASS_GHOSTSTREAM_FINAL_SCIENTIFIC_SYNTHESIS"
        if all(gates.values())
        else "FAIL_GHOSTSTREAM_FINAL_SCIENTIFIC_SYNTHESIS"
    )
    result = {
        "verdict": verdict,
        "gates": gates,
        "artifacts": artifact_checks,
        "final_position": manifest["final_position"],
    }
    (args.output / "ghoststream_final_scientific_synthesis.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# GhostStream final scientific synthesis audit",
        "",
        f"Verdict: `{verdict}`",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} `{name}`" for name, passed in gates.items())
    lines.extend(
        [
            "",
            "## Frozen scientific position",
            "",
            "- Canonical discovery package: validated.",
            "- Independent fixed4 connection: full frozen targeted recovery.",
            "- Structured antihelion explanation: rejected by the preserved source-matched evidence.",
            "- Distinct stream versus NOP solution-004 branch: unresolved from public member-level orbit data.",
            "- Further internal classifier tuning or relaxed recovery gates: not authorized.",
            "",
        ]
    )
    (args.output / "GHOSTSTREAM_FINAL_SCIENTIFIC_SYNTHESIS.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
