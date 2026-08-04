#!/usr/bin/env python3
"""Gate-only adjudication of the preserved local-contrast development result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_PROTOCOL_SHA256 = "1cbc95994afbe7121282f3e0ef98ec87323571d239695031c560130b71f1b96d"
EXPECTED_RESULT_SHA256 = "6eae2e4d5d9afa5778efda2cb134806a3d0fb4e9fcd2dc455f885c01a13e7c91"
EXPECTED_DERIVED_SOURCE_SHA256 = "b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071"
TOL = 1e-12


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--source-sha-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    protocol_sha = sha256(args.protocol)
    result_sha = sha256(args.result)
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(f"protocol hash mismatch: {protocol_sha}")
    if result_sha != EXPECTED_RESULT_SHA256:
        raise RuntimeError(f"result hash mismatch: {result_sha}")

    source_hash_lines = [line.split()[0] for line in args.source_sha_file.read_text().splitlines() if line.strip()]
    if EXPECTED_DERIVED_SOURCE_SHA256 not in source_hash_lines:
        raise RuntimeError("pinned derived source hash absent from artifact provenance")

    result = json.loads(args.result.read_text(encoding="utf-8"))
    metrics = result["metrics"]
    ideal_fwer = float(result["ideal_null"]["local_contrast"]["probability_any_detection"])
    shared_fwer = float(result["shared_structure_null"]["local_contrast"]["probability_any_detection"])

    gates = {
        "ideal_null_fwer_at_most_0_20": ideal_fwer <= 0.20 + TOL,
        "shared_structure_null_fwer_at_most_0_20": shared_fwer <= 0.20 + TOL,
        "weak_one_year_artifact_detection_at_most_0_20": (
            float(metrics["local_contrast_weak_transient_detection"]) <= 0.20 + TOL
        ),
        "weak_recurrent_power_loss_vs_best_baseline_at_most_0_05": (
            float(metrics["local_contrast_weak_recovery_difference_vs_best_baseline"]) >= -0.05 - TOL
        ),
        "recurrence_margin_gain_vs_best_baseline_at_least_0_05": (
            float(metrics["local_contrast_margin_gain_vs_best_baseline"]) >= 0.05 - TOL
        ),
        "strong_recurrent_power_no_material_collapse_vs_best_baseline": (
            float(metrics["local_contrast_strong_recovery_difference_vs_best_baseline"]) >= -0.05 - TOL
        ),
    }

    adjudication = {
        "pinned_evidence": {
            "protocol_sha256": protocol_sha,
            "result_sha256": result_sha,
            "derived_source_sha256": EXPECTED_DERIVED_SOURCE_SHA256,
            "original_source_emitted_verdict": result["verdict"],
        },
        "observed": {
            "ideal_null_fwer": ideal_fwer,
            "shared_structure_null_fwer": shared_fwer,
            "weak_transient_detection": metrics["local_contrast_weak_transient_detection"],
            "weak_recurrent_recovery": metrics["local_contrast_weak_recurrent_recovery"],
            "best_baseline_weak_recurrent_recovery": metrics["best_baseline_weak_recurrent_recovery"],
            "weak_recurrence_margin": metrics["local_contrast_weak_recurrence_margin"],
            "best_baseline_weak_recurrence_margin": metrics["best_baseline_weak_recurrence_margin"],
            "margin_gain": metrics["local_contrast_margin_gain_vs_best_baseline"],
            "strong_recurrent_recovery": metrics["local_contrast_strong_recurrent_recovery"],
            "best_baseline_strong_recurrent_recovery": metrics["best_baseline_strong_recurrent_recovery"],
        },
        "written_protocol_gates": gates,
        "verdict": (
            "AUTHORIZE_LOCAL_CONTRAST_FULL_STAGE0_FROM_PROTOCOL"
            if all(gates.values())
            else "KILL_LOCAL_CONTRAST_FROM_PROTOCOL"
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "local_contrast_gate_adjudication.json").write_text(
        json.dumps(adjudication, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Local-contrast recurrence gate-only adjudication",
        "",
        f"Verdict: **`{adjudication['verdict']}`**",
        "",
        f"Original source-emitted verdict: `{result['verdict']}`",
        f"Ideal/shared FWER: **{ideal_fwer:.6f} / {shared_fwer:.6f}**",
        f"Weak recurrence margin gain: **{metrics['local_contrast_margin_gain_vs_best_baseline']:+.6f}**",
        f"Strong recovery difference: **{metrics['local_contrast_strong_recovery_difference_vs_best_baseline']:+.6f}**",
        "",
        "## Written protocol gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if value else 'FAIL'} — `{name}`"
        for name, value in gates.items()
    )
    (args.output / "ADJUDICATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(adjudication, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("written-protocol adjudication failed")


if __name__ == "__main__":
    main()
