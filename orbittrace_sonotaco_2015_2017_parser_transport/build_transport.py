#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import py_compile
from pathlib import Path

ANCESTOR_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"
ANCESTOR_ARCHIVE_SHA = "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430"
ANCESTOR_MEMBER_SHA = "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685"
ANCESTOR_ROWS_LITERAL = "47_087"
AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
YEARS = (2015, 2017)
MEMBERS = {
    2015: "015a/_U2_20150101_S.csv",
    2017: "017a/_U2_20170101_S.csv",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one occurrence of {old!r}, found {count}")
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
                raise RuntimeError(f"could not recover {name}")
            return segment
    raise RuntimeError(f"function missing: {name}")


def build(source: str, year: int) -> str:
    if year not in YEARS:
        raise ValueError(year)
    text = source
    text = replace_once(
        text,
        f'ARCHIVE_SHA256 = "{ANCESTOR_ARCHIVE_SHA}"',
        "ARCHIVE_SHA256 = None",
    )
    text = replace_once(
        text,
        f'MEMBER_SHA256 = "{ANCESTOR_MEMBER_SHA}"',
        "MEMBER_SHA256 = None",
    )
    text = replace_once(text, f"EXPECTED_ROWS = {ANCESTOR_ROWS_LITERAL}", "EXPECTED_ROWS = None")
    text = replace_once(text, 'MEMBER = "023a/_U2_20230101_S.csv"', f'MEMBER = "{MEMBERS[year]}"')
    text = replace_once(
        text,
        '"exact_archive_hash": archive_hash == ARCHIVE_SHA256,',
        '"archive_hash_recorded": len(archive_hash) == 64,',
    )
    text = replace_once(
        text,
        '"exact_member_hash": member_hash == MEMBER_SHA256,',
        '"member_hash_recorded": len(member_hash) == 64,',
    )
    text = replace_once(
        text,
        '"exact_record_count_and_zero_malformed": total_rows == EXPECTED_ROWS and malformed_rows == 0,',
        '"nonempty_record_count_and_zero_malformed": total_rows > 0 and malformed_rows == 0,',
    )
    # All remaining literal/function/result references to the ancestor year are
    # purely transport naming. This changes no formula, threshold, header, or cut.
    text = text.replace("2023", str(year))
    return text


def audit_generated(text: str, year: int) -> dict[str, object]:
    constants = literal_constants(text)
    parse_name = f"parse_sonotaco_{year}_events"
    parser = function_source(text, parse_name)
    blind_fragment = "if BLIND_SOLAR_MIN <= sol <= BLIND_SOLAR_MAX:"
    label_fragment = 'token = row[index["shower"]].strip().upper()'
    blind_pos = parser.find(blind_fragment)
    label_pos = parser.find(label_fragment)
    if blind_pos < 0 or label_pos < 0 or blind_pos >= label_pos:
        raise RuntimeError(f"blindness ordering changed for {year}")

    required_parser_fragments = (
        'reader = csv.reader(io.StringIO(text, newline=""), delimiter=",")',
        "if len(raw_header) != RAW_HEADER_WIDTH or normalized_raw[-1] != \"\":",
        'if len(set(header)) != len(header) or not REQUIRED_HEADERS.issubset(set(header)):',
        "sol %= 360.0",
        "and ncam is not None and ncam >= 2.0",
        'ecl_lon, ecl_lat = base.equatorial_to_ecliptic(ra, dec)',
        '"sun_lon": float(base.wrap180(ecl_lon - sol))',
        "if base.is_esv(event):",
        '"native_label_syntax_fraction_ge_090": native_syntax_fraction >= 0.90,',
        '"mapped_nonbackground_fraction_ge_090": mapped_fraction >= 0.90,',
        '"at_least_30_supported_native_codes": len(supported_codes) >= 30,',
        '"at_least_10000_sporadic_after_esv_exclusion": len(sporadic) >= 10_000,',
        '"at_least_30_distinct_labeled_showers": distinct_showers >= 30,',
        '"archive_hash_recorded": len(archive_hash) == 64,',
        '"member_hash_recorded": len(member_hash) == 64,',
        '"nonempty_record_count_and_zero_malformed": total_rows > 0 and malformed_rows == 0,',
    )
    missing = [fragment for fragment in required_parser_fragments if fragment not in parser]
    if missing:
        raise RuntimeError(f"generated {year} parser missing frozen fragments: {missing}")

    required_headers = set(constants.get("REQUIRED_HEADERS", []))
    expected_headers = {
        "dd", "dedeg", "desddeg", "dr", "dv", "erdeg", "ncam",
        "radeg", "rasddeg", "shower", "soldeg", "vgkms", "vgsdkms",
    }
    gates = {
        "year_exact": constants.get("YEAR") == year,
        "member_exact": constants.get("MEMBER") == MEMBERS[year],
        "archive_hash_unset_before_first_access": constants.get("ARCHIVE_SHA256") is None,
        "member_hash_unset_before_first_access": constants.get("MEMBER_SHA256") is None,
        "row_count_unset_before_first_access": constants.get("EXPECTED_ROWS") is None,
        "mapping_audit_hash_unchanged": constants.get("AUDIT_SHA256") == AUDIT_SHA256,
        "blind_interval_exact": constants.get("BLIND_SOLAR_MIN") == 20.0 and constants.get("BLIND_SOLAR_MAX") == 55.0,
        "header_widths_exact": constants.get("RAW_HEADER_WIDTH") == 46 and constants.get("EFFECTIVE_HEADER_WIDTH") == 45,
        "required_headers_exact": required_headers == expected_headers,
        "blind_exclusion_precedes_label_access": blind_pos < label_pos,
        "ancestor_archive_hash_absent": ANCESTOR_ARCHIVE_SHA not in text,
        "ancestor_member_hash_absent": ANCESTOR_MEMBER_SHA not in text,
        "ancestor_row_literal_absent": ANCESTOR_ROWS_LITERAL not in text,
        "ancestor_year_token_absent": "2023" not in text,
    }
    if not all(gates.values()):
        raise RuntimeError(f"generated {year} parser audit failed: {gates}")
    return {
        "year": year,
        "member": MEMBERS[year],
        "gates": gates,
        "constants": {
            key: constants.get(key)
            for key in (
                "YEAR", "CORPUS", "ARCHIVE_SHA256", "MEMBER", "MEMBER_SHA256",
                "EXPECTED_ROWS", "AUDIT_SHA256", "RAW_HEADER_WIDTH", "EFFECTIVE_HEADER_WIDTH",
                "BLIND_SOLAR_MIN", "BLIND_SOLAR_MAX",
            )
        },
        "blind_fragment_offset": blind_pos,
        "label_fragment_offset": label_pos,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-2023", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    payload = args.source_2023.read_bytes()
    digest = sha256_bytes(payload)
    if digest != ANCESTOR_SHA256:
        raise RuntimeError(f"unexpected 2023 ancestor hash {digest}")
    source = payload.decode("utf-8")

    results = {}
    for year in YEARS:
        generated = build(source, year)
        path = args.output / f"run_sonotaco_{year}_transport_parser.py"
        path.write_text(generated, encoding="utf-8")
        py_compile.compile(str(path), doraise=True)
        audit = audit_generated(generated, year)
        audit["source_sha256"] = sha256_bytes(generated.encode("utf-8"))
        results[str(year)] = audit

    result = {
        "verdict": "PASS_SONOTACO_2015_2017_SOURCE_ONLY_PARSER_TRANSPORT",
        "ancestor_source_sha256": digest,
        "years": results,
        "prohibited_access": {
            "sonotaco_2015_archive": False,
            "sonotaco_2017_archive": False,
            "shower_label_rows": False,
            "scientific_scores": False,
            "excluded_interval": False,
            "orbittrace_target": False,
        },
    }
    (args.output / "sonotaco_2015_2017_parser_transport.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
