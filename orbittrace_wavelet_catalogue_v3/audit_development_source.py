#!/usr/bin/env python3
"""Source-only guard for target-free wavelet catalogue v3 development."""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

DEVELOPMENT_SOURCE_SHA256 = "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51"
DEVELOPMENT_SOURCE_BYTES = 40987
DEVELOPMENT_ENCODED_LENGTH = 13484
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
PROMOTION_ARTIFACT_SHA256 = "bbf62eca844fbf22430d096fe7b6ad8cae9cc49b3a30a0c83d5bd6f457d10cd8"


def decode_parts(root: Path, count: int = 4) -> tuple[str, bytes]:
    paths = sorted(root.glob("part*.b64"))
    expected = [f"part{i:02d}.b64" for i in range(count)]
    if [path.name for path in paths] != expected:
        raise RuntimeError(f"wrong source parts under {root}: {[path.name for path in paths]}")
    encoded = "".join("".join(path.read_text(encoding="ascii").split()) for path in paths)
    return encoded, gzip.decompress(base64.b64decode(encoded, validate=True))


def literal_assignments(tree: ast.Module) -> dict[str, object]:
    result: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            result[target.id] = ast.literal_eval(node.value)
        except Exception:
            continue
    return result


def function_arguments(tree: ast.Module) -> dict[str, list[str]]:
    return {
        node.name: [argument.arg for argument in node.args.args]
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def main() -> None:
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)

    encoded, source = decode_parts(Path("orbittrace_wavelet_catalogue_v3/source_parts"))
    if len(encoded) != DEVELOPMENT_ENCODED_LENGTH:
        raise RuntimeError(f"encoded length mismatch: {len(encoded)}")
    if len(source) != DEVELOPMENT_SOURCE_BYTES:
        raise RuntimeError(f"source byte mismatch: {len(source)}")
    digest = hashlib.sha256(source).hexdigest()
    if digest != DEVELOPMENT_SOURCE_SHA256:
        raise RuntimeError(f"development source mismatch: {digest}")

    _, support_source = decode_parts(
        Path("orbittrace_fixed4_support_wrapper_development/source_parts")
    )
    support_digest = hashlib.sha256(support_source).hexdigest()
    if support_digest != SUPPORT_SOURCE_SHA256:
        raise RuntimeError(f"support source mismatch: {support_digest}")

    text = source.decode("utf-8")
    support_text = support_source.decode("utf-8")
    protocol = Path("orbittrace_wavelet_catalogue_v3/PROTOCOL.md").read_text()
    wavelet_text = Path(
        "orbittrace_wavelet_catalogue_v3/wavelet_episode_comparator.py"
    ).read_text()
    promotion = json.loads(
        Path(
            "orbittrace_wavelet_catalogue_v3/DUAL_CHANNEL_EPISODE_PROMOTION_RESULT.json"
        ).read_text()
    )

    if promotion["verdict"] != "PASS_SONOTACO_2020_PROSPECTIVE_DUAL_CHANNEL_VALIDATION":
        raise RuntimeError("episode validation freeze did not pass")
    if promotion["decision"] != "PROMOTE_DUAL_CHANNEL_MINIMUM_RESCUE":
        raise RuntimeError("episode detector was not promoted")
    if promotion["artifact_sha256"] != PROMOTION_ARTIFACT_SHA256:
        raise RuntimeError("promotion artifact changed")
    architecture = promotion["architecture"]
    if architecture != {
        "method_id": "wavelet_rank_plus_minimum_fixed4_rescue",
        "ranking_method": "brown2010_wavelet_episode_core",
        "rescue_method": "orbittrace_fixed4",
        "base_alpha": 0.05,
        "calibration_per_bin": 128,
        "rescue_alpha": 1.0 / 129.0,
        "decision_rule": "(p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)",
    }:
        raise RuntimeError("promoted architecture changed")
    if not all(promotion["promotion_gates"].values()):
        raise RuntimeError("promotion gates are not all true")

    forbidden = [
        "247.17",
        "-14.34",
        "37.62",
        "F0059",
        "8958194010",
        "8814798136",
        "april_candidate_members.csv",
        "GhostStream_Expert_Review_Bundle",
    ]
    found = [
        value
        for value in forbidden
        if value in text or value in protocol or value in wavelet_text
    ]
    if found:
        raise RuntimeError(f"target information present: {found}")

    tree = ast.parse(text)
    constants = literal_assignments(tree)
    arguments = function_arguments(tree)
    expected_constants = {
        "YEARS": (2022, 2023),
        "WINDOW_WIDTH_DEG": 10.0,
        "WINDOW_STEP_DEG": 5.0,
        "PREFILTER_K": 32,
        "SHORTLIST_K": 256,
        "EPISODE_SIZE": 128,
        "POSITIVE_LOBE_R2": 3.0,
        "CALIBRATION_PER_BIN": 128,
        "MIN_COMPONENT_EVENTS": 4,
        "MIN_COMPONENT_ANCHORS": 2,
        "MIN_FAMILY_YEARS": 2,
        "FAMILY_LINK_RADIUS": 1.5,
        "BASE_ALPHA": 0.05,
    }
    for key, value in expected_constants.items():
        if constants.get(key) != value:
            raise RuntimeError(f"constant changed: {key}={constants.get(key)!r}")
    if "RESCUE_ALPHA = 1.0 / 129.0" not in text:
        raise RuntimeError("rescue threshold changed")
    if constants.get("MONTH_KEYS") is not None:
        raise RuntimeError("MONTH_KEYS unexpectedly became a static literal")

    required_functions = {
        "load_support_module",
        "calibrate_year",
        "stable_smallest_indices",
        "exact_rescore",
        "exact_rescore_window",
        "exact_rescore_implementation_self_test",
        "scan_year",
        "component_records",
        "build_families",
        "evaluate_families",
        "main",
    }
    if not required_functions.issubset(arguments):
        raise RuntimeError(f"missing functions: {sorted(required_functions - arguments.keys())}")
    for name in ("scan_year", "exact_rescore_window", "component_records", "build_families"):
        if "hidden_labels" in arguments[name]:
            raise RuntimeError(f"labels enter candidate generation through {name}")
    if arguments["evaluate_families"][0] != "hidden_labels":
        raise RuntimeError("label lookup is not isolated to final evaluation")

    required_fragments = [
        "MONTH_KEYS = tuple(f\"{year}-{month:02d}\" for year in YEARS",
        "p_wavelet <= BASE_ALPHA",
        "p_fixed4 <= RESCUE_ALPHA + 1e-15",
        "records_by_center",
        "exact_records = exact_rescore_window(",
        "support.exact_anchor_distances(anchor, window_events, base)",
        "scalar_grouped_scores_equal",
        "wavelet_fisher_evidence",
        '"rescue_queue": "fixed4 p <= 1/129; never inserted into wavelet ranking"',
        "PASS_WAVELET_CATALOGUE_V3_DEVELOPMENT",
        "FAIL_WAVELET_CATALOGUE_V3_DEVELOPMENT",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in text]
    if missing:
        raise RuntimeError(f"missing source fragments: {missing}")

    parse_block = support_text[
        support_text.index("def parse_catalogue") : support_text.index(
            "def circular_mean_deg"
        )
    ]
    if parse_block.index("between(BLIND_LOW, BLIND_HIGH") >= parse_block.index(
        "map(normalize_label)"
    ):
        raise RuntimeError("blind interval is not removed before label normalization")
    if 'fixed4_metrics = baseline["development"]["panel_evaluations"]["development"]' not in text:
        raise RuntimeError("wrong fixed4 comparison panel")

    wavelet_tree = ast.parse(wavelet_text)
    wavelet_constants = literal_assignments(wavelet_tree)
    expected_wavelet = {
        "ANGULAR_PROBE_DEG": 4.0,
        "SPEED_PROBE_FRACTION": 0.10,
        "TRUNCATION_RADIUS": 4.0,
        "KERNEL_DIMENSION": 3.0,
    }
    if {key: wavelet_constants.get(key) for key in expected_wavelet} != expected_wavelet:
        raise RuntimeError("wavelet parameters changed")

    Path("/tmp/run_wavelet_catalogue_v3_development.py").write_bytes(source)
    (output / "run_wavelet_catalogue_v3_development.py").write_bytes(source)
    (output / "development_source_sha256.txt").write_text(digest + "\n")
    result = {
        "verdict": "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT",
        "development_source_sha256": digest,
        "support_source_sha256": support_digest,
        "development_years": [2022, 2023],
        "held_out_catalogues_loaded": False,
        "target_information_present": False,
        "labels_enter_candidate_generation": False,
        "promoted_episode_architecture_verified": True,
        "implementation_only_exact_rescore_acceleration": True,
    }
    (output / "wavelet_catalogue_v3_source_audit.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
