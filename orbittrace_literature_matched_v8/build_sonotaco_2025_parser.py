#!/usr/bin/env python3
"""Source-only transport of the validated 2023 SonotaCo parser to 2025.

Only year/provenance literals and the unknowable ancestor row-count assertion change.
No meteor archive is opened by this script.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import py_compile
from pathlib import Path

ANCESTOR_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"
ANCESTOR_ARCHIVE_SHA = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"
ANCESTOR_MEMBER_SHA = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"
TARGET_ARCHIVE_SHA = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
TARGET_MEMBER_SHA = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
TARGET_MEMBER = "025a/_U2_20250101_S.csv"
AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one occurrence of {old!r}, found {count}")
    return text.replace(old, new, 1)


def literal_constants(text: str) -> dict[str, object]:
    tree = ast.parse(text)
    out: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            continue
        if isinstance(value, (set, frozenset)):
            value = sorted(value)
        out[node.targets[0].id] = value
    return out


def function_source(text: str, name: str) -> str:
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            segment = ast.get_source_segment(text, node)
            if segment is None:
                raise RuntimeError(name)
            return segment
    raise RuntimeError(f"missing function {name}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-2023", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    payload = args.source_2023.read_bytes()
    if hashlib.sha256(payload).hexdigest() != ANCESTOR_SHA256:
        raise RuntimeError("validated 2023 parser source hash changed")
    text = payload.decode("utf-8")

    text = replace_once(text, f'ARCHIVE_SHA256 = "{ANCESTOR_ARCHIVE_SHA}"', f'ARCHIVE_SHA256 = "{TARGET_ARCHIVE_SHA}"')
    text = replace_once(text, f'MEMBER_SHA256 = "{ANCESTOR_MEMBER_SHA}"', f'MEMBER_SHA256 = "{TARGET_MEMBER_SHA}"')
    text = replace_once(text, 'MEMBER = "023a/_U2_20230101_S.csv"', f'MEMBER = "{TARGET_MEMBER}"')
    text = replace_once(text, "EXPECTED_ROWS = 47_087", "EXPECTED_ROWS = None")
    text = replace_once(
        text,
        '"exact_record_count_and_zero_malformed": total_rows == EXPECTED_ROWS and malformed_rows == 0,',
        '"nonempty_record_count_and_zero_malformed": total_rows > 0 and malformed_rows == 0,',
    )
    text = text.replace("2023", "2025")

    constants = literal_constants(text)
    if constants.get("YEAR") != 2025:
        raise RuntimeError("YEAR transport failed")
    if constants.get("MEMBER") != TARGET_MEMBER:
        raise RuntimeError("MEMBER transport failed")
    if constants.get("ARCHIVE_SHA256") != TARGET_ARCHIVE_SHA or constants.get("MEMBER_SHA256") != TARGET_MEMBER_SHA:
        raise RuntimeError("2025 provenance transport failed")
    if constants.get("EXPECTED_ROWS") is not None:
        raise RuntimeError("2025 row-count transport failed")
    if constants.get("AUDIT_SHA256") != AUDIT_SHA256:
        raise RuntimeError("mapping audit hash changed")
    if constants.get("BLIND_SOLAR_MIN") != 20.0 or constants.get("BLIND_SOLAR_MAX") != 55.0:
        raise RuntimeError("blind interval changed")

    parser = function_source(text, "parse_sonotaco_2025_events")
    blind = parser.find("if BLIND_SOLAR_MIN <= sol <= BLIND_SOLAR_MAX:")
    label = parser.find('token = row[index["shower"]].strip().upper()')
    if blind < 0 or label < 0 or blind >= label:
        raise RuntimeError("blind exclusion no longer precedes label access")
    required = (
        'ecl_lon, ecl_lat = base.equatorial_to_ecliptic(ra, dec)',
        '"sun_lon": float(base.wrap180(ecl_lon - sol))',
        '"nonempty_record_count_and_zero_malformed": total_rows > 0 and malformed_rows == 0,',
    )
    if any(fragment not in parser for fragment in required):
        raise RuntimeError("scientific parser body changed during transport")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    py_compile.compile(str(args.output), doraise=True)
    print("PASS_SONOTACO_2025_SOURCE_ONLY_PARSER_TRANSPORT")
    print("source_sha256", hashlib.sha256(text.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
