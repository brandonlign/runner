from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

INPUT = Path("input")
OUTPUT = Path("output")

OLD_ARCHIVE = "409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f"
NEW_ARCHIVE = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"
OLD_MEMBER = "0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00"
NEW_MEMBER = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"
OLD_PARSER = "d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b"
NEW_PARSER = "9619dfc0b339b39d287833778769f12a643e2b0157fdcd6115cd9c40be528322"
UNREPAIRED_SOURCE = "1c119e0dfc154f34da06097da6c4a4cb2f7c6b11b7a1e6a9a9330baf25f1567e"
REPAIRED_SOURCE = "32d199a652a9469c10ac3b2d9496177c11bb12901ccf2c3c9b24bbfd86ff4cb7"
PY312_PAYLOAD = "51e6d94d81e4154c1812b1f0d3b3ccdb158162a33f452cabbebe9f4526df2bdd"
PINNED_2024_CONFIRMATION = "94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7"
PINNED_2024_PARSER = "d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    parser_bytes = (INPUT / "audit_sonotaco_2023_v2.py").read_bytes()
    source_bytes = (INPUT / "run_sonotaco_2023_fixed4_confirmation.py").read_bytes()
    parser_text = parser_bytes.decode("utf-8")
    repaired = source_bytes.decode("utf-8")

    substitutions = [
        (OLD_ARCHIVE, NEW_ARCHIVE, "archive_sha256"),
        (OLD_MEMBER, NEW_MEMBER, "member_sha256"),
        (OLD_PARSER, NEW_PARSER, "parser_source_sha256"),
    ]
    counts: dict[str, dict[str, int]] = {}
    for old, new, name in substitutions:
        counts[name] = {"old_before": repaired.count(old), "new_before": repaired.count(new)}
        if counts[name] != {"old_before": 1, "new_before": 0}:
            raise RuntimeError(f"unauthorized multiplicity before {name} repair: {counts[name]}")
        repaired = repaired.replace(old, new, 1)
        counts[name].update({"old_after": repaired.count(old), "new_after": repaired.count(new)})

    repaired_bytes = repaired.encode("utf-8")
    if len(repaired_bytes) != 30395 or sha256(repaired_bytes) != REPAIRED_SOURCE:
        raise RuntimeError(f"repaired source mismatch: {len(repaired_bytes)} bytes, {sha256(repaired_bytes)}")
    compile(repaired_bytes, "run_sonotaco_2023_fixed4_confirmation.py", "exec")
    tree = ast.parse(repaired, filename="run_sonotaco_2023_fixed4_confirmation.py")

    constants: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass

    payload = base64.b64encode(gzip.compress(repaired_bytes, compresslevel=9, mtime=0)).decode("ascii") + "\n"
    payload_bytes = payload.encode("ascii")
    payload_sha = sha256(payload_bytes)
    roundtrip = gzip.decompress(base64.b64decode("".join(payload.split()), validate=True))

    reversed_confirmation = repaired
    for old, new, _ in reversed(substitutions):
        if reversed_confirmation.count(new) != 1:
            raise RuntimeError("confirmation reversal multiplicity mismatch")
        reversed_confirmation = reversed_confirmation.replace(new, old, 1)
    reversed_confirmation = reversed_confirmation.replace("023a", "024a").replace("2023", "2024")
    reverse_confirmation_sha = sha256(reversed_confirmation.encode("utf-8"))

    reversed_parser = parser_text.replace(NEW_MEMBER, OLD_MEMBER)
    reversed_parser = reversed_parser.replace(NEW_ARCHIVE, OLD_ARCHIVE)
    reversed_parser = reversed_parser.replace("023a.zip", "024a.zip").replace("2023", "2024")
    reverse_parser_sha = sha256(reversed_parser.encode("utf-8"))

    required_gates = {
        "at_least_20_supported_bins",
        "at_least_30_eligible_showers",
        "pooled_fpr_005_le_006",
        "pooled_fpr_001_le_002",
        "worst_reporting_sector_fpr_005_le_012",
        "candidate_weak_auc_ge_075",
        "candidate_auc_within_003_of_strongest_comparator",
        "candidate_auc_exceeds_density",
        "candidate_auc_exceeds_dbscan",
        "four_of_five_folds_auc_ge_070",
        "no_fold_auc_below_065",
        "recall_005_k4_ge_015",
        "recall_001_k4_ge_005",
        "recall_005_k6_ge_030",
        "recall_001_k6_ge_015",
        "recall_005_k8_ge_045",
        "recall_001_k8_ge_025",
        "recall_monotonic_at_005",
        "recall_monotonic_at_001",
    }
    string_literals = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    gates = {
        "exact_input_parser_hash": sha256(parser_bytes) == NEW_PARSER,
        "exact_unrepaired_source_hash": sha256(source_bytes) == UNREPAIRED_SOURCE,
        "exact_three_one_occurrence_substitutions": all(
            values == {"old_before": 1, "new_before": 0, "old_after": 0, "new_after": 1}
            for values in counts.values()
        ),
        "repaired_source_bytes_exact": len(repaired_bytes) == 30395,
        "repaired_source_hash_exact": sha256(repaired_bytes) == REPAIRED_SOURCE,
        "python312_payload_hash_exact": payload_sha == PY312_PAYLOAD,
        "payload_roundtrip_exact_source": roundtrip == repaired_bytes,
        "source_compiles_and_parses": True,
        "year_exact_2023": constants.get("YEAR") == 2023,
        "archive_hash_exact_2023": constants.get("ARCHIVE_SHA256") == NEW_ARCHIVE,
        "member_exact_2023": constants.get("MEMBER") == "023a/_U2_20230101_S.csv",
        "member_hash_exact_2023": constants.get("MEMBER_SHA256") == NEW_MEMBER,
        "parser_hash_exact_2023": constants.get("PARSER_V2_SOURCE_SHA256") == NEW_PARSER,
        "fixed_solar_scale_exact_4": constants.get("FIXED_SOLAR_SCALE") == 4.0,
        "blind_interval_exact_20_55": constants.get("BLIND_SOLAR_MIN") == 20.0 and constants.get("BLIND_SOLAR_MAX") == 55.0,
        "all_scientific_gates_present": required_gates <= string_literals,
        "confirmation_reverse_exact_2024": reverse_confirmation_sha == PINNED_2024_CONFIRMATION,
        "parser_reverse_exact_2024": reverse_parser_sha == PINNED_2024_PARSER,
        "sonotaco_2024_archive_not_accessed": True,
        "no_archive_or_mapping_download": True,
        "no_detector_execution": True,
        "no_scientific_endpoint": True,
    }
    verdict = (
        "PASS_SONOTACO_2023_CONFIRMATION_HASH_REPAIR_AUDIT"
        if all(gates.values())
        else "KILL_SONOTACO_2023_CONFIRMATION_HASH_REPAIR_AUDIT"
    )

    (OUTPUT / "audit_sonotaco_2023_v2.py").write_bytes(parser_bytes)
    (OUTPUT / "run_sonotaco_2023_fixed4_confirmation.py").write_bytes(repaired_bytes)
    (OUTPUT / "sonotaco_2023_confirmation.py.gz.b64").write_bytes(payload_bytes)
    result = {
        "input": {
            "schema_source_run": 30920089789,
            "parser_sha256": sha256(parser_bytes),
            "unrepaired_confirmation_sha256": sha256(source_bytes),
        },
        "substitution_counts": counts,
        "output": {
            "repaired_source_bytes": len(repaired_bytes),
            "repaired_source_sha256": sha256(repaired_bytes),
            "repaired_payload_sha256": payload_sha,
            "payload_roundtrip_sha256": sha256(roundtrip),
            "reverse_confirmation_sha256": reverse_confirmation_sha,
            "reverse_parser_sha256": reverse_parser_sha,
        },
        "constants": {
            key: constants.get(key)
            for key in [
                "YEAR", "CORPUS", "ARCHIVE_SHA256", "MEMBER", "MEMBER_SHA256",
                "PARSER_V2_SOURCE_SHA256", "FIXED_SOLAR_SCALE", "BLIND_SOLAR_MIN", "BLIND_SOLAR_MAX",
            ]
        },
        "gates": gates,
        "verdict": verdict,
    }
    (OUTPUT / "sonotaco_2023_confirmation_hash_repair_audit.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    lines = [
        "# SonotaCo 2023 confirmation hash repair audit",
        "",
        f"Verdict: **{verdict}**",
        "",
        f"- repaired source SHA-256: `{sha256(repaired_bytes)}`",
        f"- Python-3.12 payload SHA-256: `{payload_sha}`",
        f"- reverse 2024 confirmation SHA-256: `{reverse_confirmation_sha}`",
        f"- reverse 2024 parser SHA-256: `{reverse_parser_sha}`",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    (OUTPUT / "SONOTACO_2023_CONFIRMATION_HASH_REPAIR_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit("Frozen 2023 confirmation hash repair audit failed")


if __name__ == "__main__":
    main()
