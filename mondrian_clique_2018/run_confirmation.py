from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "mondrian_clique_2018"
PROTOCOL = WORK_ROOT / "PROTOCOL.md"
WRAPPER = WORK_ROOT / "run_exact_2018_wrapper.py"
SOURCE_ROOT = ROOT / "mondrian_clique_development" / "source_parts_v2"
BASELINE_PAYLOAD = ROOT / "real_shower_meta_stage0" / "run_baseline_ceiling.py.gz.b64"
EXPECTED_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
EXPECTED_WRAPPER_SHA256 = "bc11723aab6c1a80e9c70515e77a559a64babd477c7cbcc6295b5663a5e803d5"
EXPECTED_BASELINE_PAYLOAD_SHA256 = "2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2"
EXPECTED_BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
EXPECTED_PARTS = ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]
EXPECTED_ENCODED_LENGTH = 9000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_candidate_source() -> bytes:
    parts = sorted(SOURCE_ROOT.glob("part*.b64"))
    names = [part.name for part in parts]
    if names != EXPECTED_PARTS:
        raise RuntimeError(f"Unexpected candidate source parts: {names}")
    encoded = "".join("".join(part.read_text().split()) for part in parts)
    if len(encoded) != EXPECTED_ENCODED_LENGTH:
        raise RuntimeError(f"Unexpected encoded source length: {len(encoded)}")
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    actual = sha256_bytes(source)
    if actual != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Exact candidate source mismatch: {actual}")
    return source


def verify_baseline() -> str:
    payload_hash = sha256_path(BASELINE_PAYLOAD)
    if payload_hash != EXPECTED_BASELINE_PAYLOAD_SHA256:
        raise RuntimeError(f"Baseline payload mismatch: {payload_hash}")
    encoded = "".join(BASELINE_PAYLOAD.read_text().split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    source_hash = sha256_bytes(source)
    if source_hash != EXPECTED_BASELINE_SOURCE_SHA256:
        raise RuntimeError(f"Baseline source mismatch: {source_hash}")
    return source_hash


def verify_data_gate(input_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    audit = json.loads((input_dir / "audit.json").read_text())
    coverage = json.loads((input_dir / "coverage.json").read_text())
    gate_result = json.loads((input_dir / "data_gate_result.json").read_text())
    if tuple(audit["configuration"]["years"]) != (2018,):
        raise RuntimeError(f"Unexpected confirmation year: {audit['configuration']['years']}")
    if gate_result.get("verdict") != "PASS_2018_DATA_GATE":
        raise RuntimeError(f"Data gate did not pass: {gate_result.get('verdict')}")
    if not all(bool(value) for value in gate_result.get("combined_gates", {}).values()):
        raise RuntimeError("At least one frozen 2018 data gate is false")
    if int(coverage.get("supported_bin_count", 0)) < 30:
        raise RuntimeError("Frozen complete-year coverage gate did not pass")
    return audit, coverage, gate_result


def independently_evaluate_gates(result: dict[str, Any]) -> dict[str, bool]:
    false_positive = result["false_positive"]
    recall = result["recall"]
    folds = [float(item["candidate_auc"]) for item in result["fold_results"]]
    comparators = [float(value) for value in result["fixed_comparator_weak_auc"].values()]
    candidate_auc = float(result["candidate_weak_auc"])

    def monotonic(values: dict[str, Any]) -> bool:
        sequence = [float(values[str(k)]) for k in (4, 6, 8, 12)]
        return all(left <= right for left, right in zip(sequence, sequence[1:]))

    return {
        "pooled_fpr_005_le_006": float(false_positive["0.05"]) <= 0.060,
        "pooled_fpr_001_le_002": float(false_positive["0.01"]) <= 0.020,
        "worst_reporting_sector_fpr_005_le_012": float(result["worst_reporting_sector_0.05"]) <= 0.120,
        "candidate_weak_auc_ge_075": candidate_auc >= 0.750,
        "candidate_auc_within_003_of_strongest_comparator": candidate_auc >= max(comparators) - 0.030,
        "four_of_five_folds_auc_ge_070": sum(value >= 0.700 for value in folds) >= 4,
        "no_fold_auc_below_065": min(folds) >= 0.650,
        "recall_005_k4_ge_015": float(recall["0.05"]["4"]) >= 0.150,
        "recall_005_k6_ge_030": float(recall["0.05"]["6"]) >= 0.300,
        "recall_005_k8_ge_045": float(recall["0.05"]["8"]) >= 0.450,
        "recall_001_k4_ge_005": float(recall["0.01"]["4"]) >= 0.050,
        "recall_001_k6_ge_015": float(recall["0.01"]["6"]) >= 0.150,
        "recall_001_k8_ge_025": float(recall["0.01"]["8"]) >= 0.250,
        "recall_monotonic_at_005": monotonic(recall["0.05"]),
        "recall_monotonic_at_001": monotonic(recall["0.01"]),
    }


def write_report(
    output: Path,
    result: dict[str, Any],
    independent_gates: dict[str, bool],
    provenance: dict[str, Any],
) -> str:
    pass_all = all(independent_gates.values())
    verdict = (
        "PASS_MONDRIAN_CLIQUE_2018_CONFIRMATION"
        if pass_all
        else "KILL_MONDRIAN_CLIQUE_2018_CONFIRMATION"
    )
    confirmation = {
        "verdict": verdict,
        "independent_confirmation_gates": independent_gates,
        "source_gate_agreement": result.get("gates") == independent_gates,
        "source_result": result,
        "provenance": provenance,
    }
    (output / "confirmation_verdict.json").write_text(
        json.dumps(confirmation, indent=2, sort_keys=True) + "\n"
    )

    recall = result["recall"]
    fold_values = [float(item["candidate_auc"]) for item in result["fold_results"]]
    lines = [
        "# Coverage-normalized Mondrian four-clique: untouched 2018 confirmation",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- supported fixed 10° bins: **{result['counts']['supported_bins']}**",
        f"- eligible showers: **{result['counts']['eligible_showers']}**",
        f"- candidate weak AUROC: **{float(result['candidate_weak_auc']):.5f}**",
        f"- pooled FPR at 0.05 / 0.01: **{float(result['false_positive']['0.05']):.5f} / {float(result['false_positive']['0.01']):.5f}**",
        f"- worst 60° reporting-sector FPR at 0.05: **{float(result['worst_reporting_sector_0.05']):.5f}**",
        f"- five fold AUROCs: **{', '.join(f'{value:.5f}' for value in fold_values)}**",
        "",
        "## Recall",
        "",
        "| Members | p ≤ 0.05 | p ≤ 0.01 |",
        "|---:|---:|---:|",
    ]
    for k in (4, 6, 8, 12):
        lines.append(
            f"| {k} | {float(recall['0.05'][str(k)]):.5f} | {float(recall['0.01'][str(k)]):.5f} |"
        )
    lines.extend(["", "## Gates", ""])
    lines.extend(f"- `{name}`: **{passed}**" for name, passed in independent_gates.items())
    (output / "CONFIRMATION_REPORT.md").write_text("\n".join(lines) + "\n")
    return verdict


def write_environment(output: Path) -> None:
    (output / "python_version.txt").write_text(sys.version + "\n")
    freeze = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (output / "environment.txt").write_text(freeze)


def main() -> None:
    args = parse_args()
    input_dir = args.input.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    audit, coverage, gate_result = verify_data_gate(input_dir)
    wrapper_hash = sha256_path(WRAPPER)
    if wrapper_hash != EXPECTED_WRAPPER_SHA256:
        raise RuntimeError(f"Interface wrapper mismatch: {wrapper_hash}")
    source = decode_candidate_source()
    baseline_source_hash = verify_baseline()

    with tempfile.TemporaryDirectory(prefix="mondrian-2018-") as temporary:
        source_path = Path(temporary) / "run_mondrian_clique_2018.py"
        source_path.write_bytes(source)
        subprocess.run([sys.executable, "-m", "py_compile", str(source_path), str(WRAPPER)], check=True)
        command = [
            sys.executable,
            str(WRAPPER),
            "--source",
            str(source_path),
            "--",
            "--events",
            str(input_dir / "selected_events.jsonl.gz"),
            "--year",
            "2018",
            "--corpus",
            "complete-year-2018-confirmation",
            "--workers",
            "4",
            "--baseline-payload",
            str(BASELINE_PAYLOAD),
            "--output",
            str(output),
        ]
        try:
            subprocess.run(command, check=True, cwd=ROOT)
        except subprocess.CalledProcessError as error:
            (output / "technical_failure.json").write_text(
                json.dumps(
                    {
                        "verdict": "TECHNICAL_EXECUTION_FAILURE",
                        "returncode": error.returncode,
                        "command": command,
                    },
                    indent=2,
                )
                + "\n"
            )
            raise

    result_path = output / "mondrian_clique_development_2018.json"
    result = json.loads(result_path.read_text())
    if int(result["counts"]["minimum_supported_bins"]) != 20:
        raise RuntimeError(
            f"Unexpected complete-year support rule: {result['counts']['minimum_supported_bins']}"
        )

    independent_gates = independently_evaluate_gates(result)
    source_gates = {str(name): bool(value) for name, value in result.get("gates", {}).items()}
    if source_gates != independent_gates:
        raise RuntimeError(
            "Exact-source gate results disagree with the independent frozen confirmation calculation"
        )

    provenance = {
        "protocol_sha256": sha256_path(PROTOCOL),
        "data_gate_result_sha256": sha256_path(input_dir / "data_gate_result.json"),
        "selected_events_sha256": sha256_path(input_dir / "selected_events.jsonl.gz"),
        "audit_sha256": sha256_path(input_dir / "audit.json"),
        "coverage_sha256": sha256_path(input_dir / "coverage.json"),
        "candidate_source_sha256": sha256_bytes(source),
        "wrapper_sha256": wrapper_hash,
        "baseline_payload_sha256": sha256_path(BASELINE_PAYLOAD),
        "baseline_source_sha256": baseline_source_hash,
        "audit_counts": {
            "eligible_count": audit.get("eligible_count"),
            "strong_count": audit.get("strong_count"),
            "eligible_complex_units": audit.get("eligible_complex_units"),
            "total_quality_sporadics": audit.get("total_quality_sporadics"),
        },
        "supported_bin_count": coverage.get("supported_bin_count"),
        "data_gate_verdict": gate_result.get("verdict"),
    }
    verdict = write_report(output, result, independent_gates, provenance)
    write_environment(output)

    tracked = [
        PROTOCOL,
        WRAPPER,
        *sorted(SOURCE_ROOT.glob("part*.b64")),
        input_dir / "selected_events.jsonl.gz",
        input_dir / "audit.json",
        input_dir / "coverage.json",
        input_dir / "data_gate_result.json",
        BASELINE_PAYLOAD,
        result_path,
        output / "confirmation_verdict.json",
    ]
    (output / "source_and_input_sha256.txt").write_text(
        "\n".join(f"{sha256_path(path)}  {path}" for path in tracked) + "\n"
    )
    print((output / "CONFIRMATION_REPORT.md").read_text())

    if verdict != "PASS_MONDRIAN_CLIQUE_2018_CONFIRMATION":
        raise SystemExit("Frozen untouched-2018 scientific confirmation gate failed")


if __name__ == "__main__":
    main()
