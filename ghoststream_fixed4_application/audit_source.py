#!/usr/bin/env python3
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path

EXPECTED_SOURCE_SHA = "747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301"
EXPECTED_SOURCE_BYTES = 19652
EXPECTED_ENCODED_LENGTH = 7616
EXPECTED_ARTIFACT_SHA = "716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5"
FORBIDDEN_TOKENS = (
    "GhostStream",
    "GHOSTSTREAM",
    "36.901963",
    "149.3763247",
    "37.641692",
    "247.06",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit_source.py CANDIDATE_B64 CANONICAL_ZIP OUTPUT_DIR")
    payload_path = Path(sys.argv[1])
    artifact_path = Path(sys.argv[2])
    output = Path(sys.argv[3])
    output.mkdir(parents=True, exist_ok=True)

    encoded = "".join(payload_path.read_text(encoding="ascii").split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    source_sha = hashlib.sha256(source).hexdigest()
    text = source.decode("utf-8")
    tree = ast.parse(text)

    artifact_sha = sha256(artifact_path)
    with zipfile.ZipFile(artifact_path) as archive:
        artifact_members = sorted(archive.namelist())
        unsafe = [name for name in artifact_members if name.startswith("/") or ".." in Path(name).parts]

    constants: dict[str, object] = {}
    functions: list[dict[str, object]] = []
    classes: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if isinstance(target, ast.Name):
                    try:
                        constants[target.id] = ast.literal_eval(value)
                    except Exception:
                        pass
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "kwonlyargs": [arg.arg for arg in node.args.kwonlyargs],
                "line": node.lineno,
            })
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    gates = {
        "encoded_length_exact": len(encoded) == EXPECTED_ENCODED_LENGTH,
        "source_bytes_exact": len(source) == EXPECTED_SOURCE_BYTES,
        "source_sha_exact": source_sha == EXPECTED_SOURCE_SHA,
        "candidate_scale_exact_4": constants.get("CANDIDATE_SCALE") == 4.0,
        "solar_scale_family_preserved": constants.get("SOLAR_SCALES") == (2.0, 4.0),
        "no_scale_selection_state": "selected_scales" not in text and "consensus_key" not in text,
        "no_ghoststream_value_in_detector": not any(token in text for token in FORBIDDEN_TOKENS),
        "canonical_artifact_sha_exact": artifact_sha == EXPECTED_ARTIFACT_SHA,
        "canonical_artifact_nonempty": len(artifact_members) > 0,
        "canonical_artifact_safe_paths": not unsafe,
        "protocol_present": Path("ghoststream_fixed4_application/AUDIT_PROTOCOL.md").is_file(),
    }

    verdict = "PASS_GHOSTSTREAM_FIXED4_APPLICATION_SOURCE_AUDIT" if all(gates.values()) else "FAIL_GHOSTSTREAM_FIXED4_APPLICATION_SOURCE_AUDIT"
    result = {
        "verdict": verdict,
        "gates": gates,
        "detector": {
            "source_sha256": source_sha,
            "source_bytes": len(source),
            "encoded_length": len(encoded),
            "constants": constants,
            "functions": functions,
            "classes": classes,
        },
        "canonical_artifact": {
            "artifact_id": 8814798136,
            "zip_sha256": artifact_sha,
            "member_count": len(artifact_members),
            "members": artifact_members,
        },
        "scientific_boundary": "No GhostStream scientific value was read and no GhostStream score was computed.",
    }
    (output / "source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "frozen_candidate.py").write_bytes(source)

    lines = [
        "# GhostStream fixed-4° application source audit",
        "",
        f"Verdict: `{verdict}`",
        "",
        f"- detector SHA-256: `{source_sha}`",
        f"- detector bytes: **{len(source)}**",
        f"- fixed candidate scale: **{constants.get('CANDIDATE_SCALE')}°**",
        f"- canonical artifact SHA-256: `{artifact_sha}`",
        f"- decoded top-level functions: **{len(functions)}**",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} `{name}`" for name, passed in gates.items())
    lines += ["", "No GhostStream scientific value was read and no GhostStream score was computed.", ""]
    (output / "SOURCE_AUDIT.md").write_text("\n".join(lines))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
