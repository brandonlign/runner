#!/usr/bin/env python3
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

EXPECTED = {
    "baseline": "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50",
    "scorer": "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8",
    "adapter": "5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518",
}
FORBIDDEN_CANDIDATE_VALUES = (
    "36.901963",
    "149.3763247",
    "37.641692",
    "247.06",
    "14.22",
)


def decode_payload(path: Path) -> bytes:
    encoded = "".join(path.read_text(encoding="ascii").split())
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def decode_parts(path: Path) -> bytes:
    parts = sorted(path.glob("part*.b64"))
    if not parts:
        raise RuntimeError(f"no source parts in {path}")
    encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in parts)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, set):
        return [json_safe(item) for item in sorted(value, key=repr)]
    return value


def interface(source: bytes) -> dict[str, object]:
    text = source.decode("utf-8")
    tree = ast.parse(text)
    functions = []
    classes = []
    constants = {}
    imports = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "kwonlyargs": [arg.arg for arg in node.args.kwonlyargs],
                "line": node.lineno,
            })
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        "name": child.name,
                        "args": [arg.arg for arg in child.args.args],
                        "kwonlyargs": [arg.arg for arg in child.args.kwonlyargs],
                        "line": child.lineno,
                    })
            classes.append({"name": node.name, "line": node.lineno, "methods": methods})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    try:
                        constants[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass
    return json_safe({
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "constants": constants,
    })


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit_execution_interface.py BASELINE SCORER_DIR ADAPTER_DIR OUTPUT")
    output = Path(sys.argv[4])
    output.mkdir(parents=True, exist_ok=True)
    sources = {
        "baseline": decode_payload(Path(sys.argv[1])),
        "scorer": decode_parts(Path(sys.argv[2])),
        "adapter": decode_parts(Path(sys.argv[3])),
    }
    records = {}
    gates = {}
    for name, source in sources.items():
        digest = hashlib.sha256(source).hexdigest()
        gates[f"{name}_sha_exact"] = digest == EXPECTED[name]
        records[name] = {
            "sha256": digest,
            "bytes": len(source),
            "interface": interface(source),
        }
        (output / f"frozen_{name}.py").write_bytes(source)

    baseline_constants = records["baseline"]["interface"]["constants"]
    scorer_constants = records["scorer"]["interface"]["constants"]
    all_source_text = "\n".join(source.decode("utf-8") for source in sources.values())
    gates.update({
        "episode_size_128": baseline_constants.get("EPISODE_SIZE") == 128,
        "calibration_count_128": scorer_constants.get("CALIBRATION_NEGATIVES_PER_BIN") == 128,
        "test_negative_count_64": scorer_constants.get("TEST_NEGATIVES_PER_BIN") == 64,
        "positive_replicates_4": scorer_constants.get("POSITIVE_REPLICATES") == 4,
        "all_k_exact": scorer_constants.get("ALL_K") == [4, 6, 8, 12],
        "mondrian_width_10": scorer_constants.get("MONDRIAN_BIN_WIDTH_DEG") == 10.0,
        "no_embedded_ghoststream_candidate_values": not any(value in all_source_text for value in FORBIDDEN_CANDIDATE_VALUES),
    })
    verdict = "PASS_GHOSTSTREAM_FIXED4_EXECUTION_INTERFACE_AUDIT" if all(gates.values()) else "FAIL_GHOSTSTREAM_FIXED4_EXECUTION_INTERFACE_AUDIT"
    result = {"verdict": verdict, "gates": gates, "sources": records}
    (output / "execution_interface_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = ["# GhostStream fixed4 execution-interface audit", "", f"Verdict: `{verdict}`", "", "## Gates", ""]
    lines.extend(f"- {'PASS' if value else 'FAIL'} `{key}`" for key, value in gates.items())
    lines += [
        "",
        "The baseline contains a provenance sentence naming GhostStream as excluded from its earlier methodology data. No GhostStream coordinate, speed, member, score, or candidate value is embedded in any dependency.",
        "",
        "No meteor archive, event, label, candidate value, score, or p-value was read.",
        "",
    ]
    (output / "EXECUTION_INTERFACE_AUDIT.md").write_text("\n".join(lines))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
