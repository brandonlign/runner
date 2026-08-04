#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import requests
from pypdf import PdfReader

URL = "https://www.astro.sk/~ne/IAUMDC/PhV2016/formats.pdf"
EXPECTED_BYTES = 62_530
EXPECTED_SHA256 = "2cb0f754a81fe62c41f2b106c1e82750a38f38725a459591111d084f210e1924"
START_HEADING = "reduced data: meteor in a single line"
END_HEADING = "old iau mdc format"
PARAMETER_ORDER = ("IC", "yr", "mn", "day", "q", "e", "i", "arg", "nod", "RA", "DEC", "Vg", "Vh")


def exact_token(section: str, token: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])",
        section,
        flags=re.IGNORECASE,
    ) is not None


def build_result() -> dict:
    response = requests.get(URL, timeout=300)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise RuntimeError(
            f"source mismatch: bytes={len(raw)} sha256={digest}"
        )

    reader = PdfReader(io.BytesIO(raw))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    all_text = "\n".join(page_texts)
    lower = all_text.casefold()
    start = lower.rfind(START_HEADING)
    if start < 0:
        raise RuntimeError("actual reduced-format heading not found")
    end = lower.find(END_HEADING, start + len(START_HEADING))
    if end < 0:
        raise RuntimeError("next Old IAU MDC format heading not found")
    section = all_text[start:end]
    if len(section.strip()) < 100:
        raise RuntimeError(
            f"actual reduced-format section unexpectedly short: {len(section.strip())}"
        )

    codes = [token for token in PARAMETER_ORDER if exact_token(section, token)]
    required = {
        "LS": exact_token(section, "LS")
        or re.search(r"solar\s+longitude", section, re.IGNORECASE) is not None,
        "RA": exact_token(section, "RA")
        or re.search(r"right\s+ascension", section, re.IGNORECASE) is not None,
        "DEC": exact_token(section, "DEC")
        or re.search(r"declination", section, re.IGNORECASE) is not None,
        "Vg": exact_token(section, "Vg")
        or re.search(r"geocentric\s+(?:speed|velocity)", section, re.IGNORECASE)
        is not None,
        "Sh": exact_token(section, "Sh")
        or re.search(r"shower\s+number", section, re.IGNORECASE) is not None,
    }
    heading_occurrences = lower.count(START_HEADING)
    gates = {
        "exact_document_hash_and_size": True,
        "multiple_heading_occurrences_disambiguated": heading_occurrences >= 2,
        "actual_reduced_section_identified": True,
        "actual_section_nontrivial": len(section.strip()) >= 100,
        "required_fields_all_explicit": all(required.values()),
        "no_data_resource_requested": True,
        "reserved_panels_untouched": True,
    }
    verdict = (
        "PASS_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA_V2"
        if all(gates.values())
        else "KILL_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA_V2"
    )
    return {
        "method": "Historical CAMS Database 2.0 single-line schema audit parser v2",
        "sole_parser_change": "last reduced-format heading occurrence before Old IAU MDC format",
        "source": {
            "url": URL,
            "bytes": len(raw),
            "sha256": digest,
            "pages": len(reader.pages),
        },
        "heading_occurrences": heading_occurrences,
        "selected_section_characters": len(section),
        "reduced_parameter_codes": codes,
        "required_field_presence": required,
        "single_line_records_read": 0,
        "meteor_values_read": False,
        "label_values_read": False,
        "later_california_records_read": False,
        "benelux_data_requested": False,
        "sonotaco_2024_read": False,
        "camsv3_2016_values_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def write_outputs(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "single_line_schema_audit_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# Historical CAMS Database 2.0 single-line schema audit parser v2",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
        f"- heading occurrences: {result.get('heading_occurrences')}",
        f"- selected section characters: {result.get('selected_section_characters')}",
        f"- reduced parameter codes: `{result.get('reduced_parameter_codes')}`",
        f"- required fields: `{result.get('required_field_presence')}`",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(
        f"- {name}: {passed}" for name, passed in result.get("gates", {}).items()
    )
    if result.get("error"):
        lines.extend(["", "## Execution error", "", f"`{result['error']}`"])
    lines.extend(
        [
            "",
            "No `.1l`, `.xlsx`, or `.d15` meteor record was requested or read.",
        ]
    )
    (out / "RESULT.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    try:
        result = build_result()
    except Exception as exc:
        result = {
            "method": "Historical CAMS Database 2.0 single-line schema audit parser v2",
            "sole_parser_change": "last reduced-format heading occurrence before Old IAU MDC format",
            "error": f"{type(exc).__name__}: {exc}",
            "single_line_records_read": 0,
            "meteor_values_read": False,
            "label_values_read": False,
            "later_california_records_read": False,
            "benelux_data_requested": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA_V2",
        }
    write_outputs(out, result)
    print(
        json.dumps(
            {
                "verdict": result["verdict"],
                "codes": result.get("reduced_parameter_codes"),
                "required": result.get("required_field_presence"),
                "gates": result.get("gates"),
                "error": result.get("error"),
            },
            indent=2,
        )
    )
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA_V2":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
