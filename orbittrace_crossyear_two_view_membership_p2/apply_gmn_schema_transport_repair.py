#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_INPUT_SHA256 = "f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb"

BEFORE = '''def exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    schema_lines = [line for line in text.splitlines() if line.startswith("# Unique trajectory;")]
    require(len(schema_lines) == 1, f"raw schema header not unique: {len(schema_lines)}")
    fields = [field.strip() for field in schema_lines[0][1:].split(";")]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f"raw schema field {name!r} not unique: {hits}")
        return hits[0]

    positions = {
        "id": exact("Unique trajectory"),
        "sol": exact("Sol lon"),
        "q": exact("q"),
        "e": exact("e"),
        "i": exact("i"),
        "peri": exact("peri"),
        "node": exact("node"),
    }
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == "Q"]
    require(len(q_upper) == 1 and q_upper[0] != positions["q"], "q/Q schema identity changed")
    return fields, positions
'''

AFTER = '''def exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    schema_lines = [line for line in text.splitlines() if line.startswith("# Unique trajectory;")]
    if not schema_lines:
        # gmn-python-api==0.0.13 may return monthly data without the two raw
        # schema header rows. Recover ONLY the column identities from the exact
        # package-local model fixture used by that pinned parser; do not infer
        # positions from live scientific values or from shower labels.
        from gmn_python_api import meteor_trajectory_schema as gmn_schema
        model_text = gmn_schema._MODEL_METEOR_TRAJECTORY_FILE_ONE_ROW_PATH.read_text()
        schema_lines = [line for line in model_text.splitlines() if line.startswith("#  Unique trajectory;")]
        require(len(schema_lines) == 1, f"pinned package schema header not unique: {len(schema_lines)}")
        schema_line = schema_lines[0]
    else:
        require(len(schema_lines) == 1, f"raw schema header not unique: {len(schema_lines)}")
        schema_line = schema_lines[0]
    fields = [field.strip() for field in schema_line[1:].split(";")]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f"raw schema field {name!r} not unique: {hits}")
        return hits[0]

    positions = {
        "id": exact("Unique trajectory"),
        "sol": exact("Sol lon"),
        "q": exact("q"),
        "e": exact("e"),
        "i": exact("i"),
        "peri": exact("peri"),
        "node": exact("node"),
    }
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == "Q"]
    require(len(q_upper) == 1 and q_upper[0] != positions["q"], "q/Q schema identity changed")
    return fields, positions
'''


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_gmn_schema_transport_repair.py INPUT OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"unexpected canonical P2 input SHA256: {actual}")
    text = raw.decode("utf-8")
    if text.count(BEFORE) != 1:
        raise RuntimeError("GMN schema transport repair anchor not unique")
    patched = text.replace(BEFORE, AFTER, 1)
    if patched.replace(AFTER, BEFORE, 1) != text:
        raise RuntimeError("GMN schema transport repair is not exactly reversible")
    output.write_text(patched, encoding="utf-8")
    print(f"P2_GMN_SCHEMA_REPAIR_INPUT_SHA256={EXPECTED_INPUT_SHA256}")
    print(f"P2_GMN_SCHEMA_REPAIR_OUTPUT_SHA256={digest(patched.encode('utf-8'))}")
    print("P2_GMN_SCHEMA_REPAIR_SCOPE=package-pinned raw column metadata fallback only; no scientific parameter or event value changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
