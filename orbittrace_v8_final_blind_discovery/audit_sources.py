#!/usr/bin/env python3
"""Source-only audit for the final v8 blind discovery firewall. Never accesses a catalogue."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

EXPECTED = {
    "orbittrace_pooled_year_centroid_v8/PROTOCOL.md": "ff906238ab80453c4e7d78153fafeeaeb7e948e9be133b1f25f9e2f0de3bee30",
    "orbittrace_pooled_year_centroid_v8/run_development.py": "0632e728f9c237ce9beac3c5804bc8fde6525203470853395716944b17bd4a8a",
    "orbittrace_label_free_sparse_support_v6/run_development.py": "5c1ed5606c9a5351b93f9475a1bfc82bed90c2d9dcfc384ea580dd6d344e9a48",
    "orbittrace_sparse_support_multiplicity_v5/run_holdout.py": "fd9526ecb75751b6fb0e936fe5dd237a77c406b729c96ecd9b24aba634b0f43f",
    "orbittrace_wavelet_catalogue_v3/wavelet_episode_comparator.py": "5ef0f7b33a1c3ed87885ee70be0cdd184055d819eb1196c65eebc7e867f747e2",
}
FREEZE_PATHS = (
    "orbittrace_v8_final_blind_discovery/PROTOCOL.md",
    "orbittrace_v8_final_blind_discovery/SOURCE_AND_BRANCH_AUDIT.md",
    "orbittrace_v8_final_blind_discovery/audit_sources.py",
    "orbittrace_v8_final_blind_discovery/authorize_stage_a.py",
    "orbittrace_v8_final_blind_discovery/run_stage_a.py",
    "orbittrace_v8_final_blind_discovery/run_stage_b.py",
    ".github/workflows/orbittrace_v8_final_blind_stage_a.yml",
    ".github/workflows/orbittrace_v8_final_blind_stage_b.yml",
)
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
WAVELET_RUNTIME_SHA256 = "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51"
V8_PARENT_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
V8_DEVELOPMENT_ARTIFACT_SHA256 = "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def imported_modules(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def called_attributes(tree: ast.AST) -> set[str]:
    return {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}


def main() -> int:
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for name, expected in EXPECTED.items():
        actual = sha(Path(name))
        require(actual == expected, f"frozen upstream source changed: {name} {actual}")
        hashes[name] = actual

    upstream = json.loads(Path("output/wavelet_catalogue_v3_source_audit.json").read_text())
    require(upstream.get("verdict") == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "upstream source audit did not pass")
    require(upstream.get("development_source_sha256") == WAVELET_RUNTIME_SHA256, "wavelet runtime changed")
    require(upstream.get("support_source_sha256") == SUPPORT_SOURCE_SHA256, "support source changed")
    require(upstream.get("target_information_present") is False, "upstream source contains target information")
    require(upstream.get("labels_enter_candidate_generation") is False, "upstream proposal label boundary changed")

    stage_a_path = Path("orbittrace_v8_final_blind_discovery/run_stage_a.py")
    stage_b_path = Path("orbittrace_v8_final_blind_discovery/run_stage_b.py")
    auth_path = Path("orbittrace_v8_final_blind_discovery/authorize_stage_a.py")
    protocol_path = Path("orbittrace_v8_final_blind_discovery/PROTOCOL.md")
    stage_a_text = stage_a_path.read_text()
    stage_b_text = stage_b_path.read_text()
    auth_text = auth_path.read_text()
    protocol_text = protocol_path.read_text()
    stage_a_tree = ast.parse(stage_a_text)
    stage_b_tree = ast.parse(stage_b_text)

    imports_a = imported_modules(stage_a_tree)
    imports_b = imported_modules(stage_b_tree)
    attrs_a = called_attributes(stage_a_tree)
    require(not any("support_overlap_family_v9" in name for name in imports_a), "v9 entered Stage A imports")
    require(not any("postpass" in name for name in imports_a), "postpass branch code entered Stage A imports")
    require("parse_catalogue" not in attrs_a, "Stage A calls inherited label-aware parser")
    require("normalize_label" not in attrs_a, "Stage A normalizes source labels")
    require("hidden_labels" not in stage_a_text, "Stage A contains hidden-label interface")
    require("withheld_reference_artifact_id" not in stage_a_text, "Stage A contains a withheld-reference locator")
    require("F0059" not in stage_a_text + auth_text + protocol_text, "old revealed family identifier entered the final freeze")

    forbidden_stage_b_import_roots = {
        "numpy", "pandas", "sklearn", "scipy", "gmn_python_api",
        "orbittrace_label_free_sparse_support_v6", "orbittrace_pooled_year_centroid_v8",
        "orbittrace_sparse_support_multiplicity_v5", "orbittrace_wavelet_catalogue_v3",
    }
    require(not (imports_b & forbidden_stage_b_import_roots), f"Stage B imports scientific detector modules: {imports_b & forbidden_stage_b_import_roots}")
    require("get_monthly_file_content_by_date" not in stage_b_text, "Stage B can access GMN catalogue")
    require("exact stable GMN event-ID equality; zero tolerance" in stage_b_text, "Stage B exact-ID rule missing")
    require("FULL_BLIND_INDEPENDENT_RECOVERY" in stage_b_text and "PARTIAL_BLIND_INDEPENDENT_RECOVERY" in stage_b_text and "NO_BLIND_INDEPENDENT_RECOVERY" in stage_b_text, "Stage B verdict classes missing")

    required_protocol = [
        "rank <=25", "rank <=100", "M_year = (v3 / Brown)^2", "<= 1.5",
        "exact stable GMN trajectory/event-ID equality", "STAGE A — BLIND DISCOVERY", "STAGE B — REVEAL",
    ]
    require(all(fragment in protocol_text for fragment in required_protocol), "protocol lost a frozen rule")
    for path in FREEZE_PATHS:
        require(Path(path).is_file(), f"freeze file missing: {path}")

    freeze_hashes = {path: sha(Path(path)) for path in FREEZE_PATHS}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    require(len(commit) == 40, "cannot resolve execution commit")
    manifest = {
        "schema": "orbittrace-v8-final-blind-freeze-v1",
        "freeze_commit": commit,
        "v8_parent_commit": V8_PARENT_COMMIT,
        "v8_development_artifact_sha256": V8_DEVELOPMENT_ARTIFACT_SHA256,
        "support_source_sha256": SUPPORT_SOURCE_SHA256,
        "wavelet_runtime_sha256": WAVELET_RUNTIME_SHA256,
        "upstream_file_sha256": hashes,
        "freeze_file_sha256": freeze_hashes,
        "target_region_data_access": False,
        "withheld_reference_access": False,
        "catalogue_access": False,
    }
    manifest_path = output / "FREEZE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = {
        "schema": "orbittrace-v8-final-blind-source-audit-v1",
        "verdict": "PASS_V8_FINAL_BLIND_SOURCE_AUDIT",
        "v8_parent_commit": V8_PARENT_COMMIT,
        "freeze_commit": commit,
        "freeze_manifest_sha256": sha(manifest_path),
        "upstream_hashes": hashes,
        "freeze_file_sha256": freeze_hashes,
        "support_source_sha256": SUPPORT_SOURCE_SHA256,
        "wavelet_runtime_sha256": WAVELET_RUNTIME_SHA256,
        "stage_a_imports_v9": False,
        "stage_a_imports_postpass": False,
        "stage_a_calls_label_aware_parser": False,
        "stage_a_has_withheld_reference_locator": False,
        "stage_b_detector_imports": False,
        "target_region_data_access": False,
        "withheld_reference_access": False,
        "catalogue_access": False,
    }
    (output / "v8_final_blind_source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
