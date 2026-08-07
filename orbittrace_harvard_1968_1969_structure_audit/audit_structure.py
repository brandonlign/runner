#!/usr/bin/env python3
"""Pre-scientific structure audit for PDS Steel har6869.tab.

The scientific table member is never opened. Only ZIP directory metadata and official
PDS label/metadata members are inspected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath

URL = "https://sbnarchive.psi.edu/pds4/non_mission/meteoroid.steel.orbits.zip"
TARGET_BASENAME = "har6869.tab"
EXPECTED_PUBLIC_RECORDS = 19_818
LABEL_EXTS = {".xml", ".lbl"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_texts(node: ET.Element) -> dict[str, str]:
    out: dict[str, str] = {}
    for ch in node.iter():
        if ch is node or ch.text is None:
            continue
        key = local(ch.tag)
        value = ch.text.strip()
        if value and key not in out:
            out[key] = value
    return out


def parse_xml_label(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    fields = []
    records = []
    table_types = []
    for node in root.iter():
        tag = local(node.tag)
        if tag.startswith("Table_"):
            table_types.append(tag)
        if tag == "records" and node.text and node.text.strip().isdigit():
            records.append(int(node.text.strip()))
        if tag.startswith("Field_"):
            vals = child_texts(node)
            fields.append({
                key: vals[key]
                for key in (
                    "name", "field_number", "field_location", "field_length",
                    "data_type", "unit", "description", "field_format"
                )
                if key in vals
            })
    return {
        "xml": True,
        "table_types": sorted(set(table_types)),
        "declared_record_counts": sorted(set(records)),
        "fields": fields,
    }


def parse_pds3_label(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="replace")
    names = []
    records = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("ROWS") and "=" in s:
            rhs = s.split("=", 1)[1].strip().strip('"')
            if rhs.isdigit():
                records.append(int(rhs))
        if s.startswith("NAME") and "=" in s:
            names.append(s.split("=", 1)[1].strip().strip('"'))
    return {
        "xml": False,
        "table_types": ["PDS3_LABEL"],
        "declared_record_counts": sorted(set(records)),
        "fields": [{"name": x} for x in names],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freshness-json", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    fresh = json.loads(args.freshness_json.read_text())
    assert fresh["verdict"] == "PASS_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    assert fresh["potential_exposure_hit_count"] == 0
    assert fresh["catalogue_contacted"] is False
    assert fresh["scientific_record_access"] is False
    assert fresh["orbittrace_target_information_access"] is False

    archive = args.output / "meteoroid.steel.orbits.zip"
    req = urllib.request.Request(URL, headers={"User-Agent": "OrbitTrace-Harvard-structure-audit/1.0"})
    with urllib.request.urlopen(req, timeout=180) as response, archive.open("wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)

    if not zipfile.is_zipfile(archive):
        raise RuntimeError("downloaded PDS bundle is not a ZIP")

    opened_members: list[str] = []
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        targets = [i for i in infos if PurePosixPath(i.filename).name.lower() == TARGET_BASENAME]
        if len(targets) != 1:
            raise RuntimeError(f"expected exactly one {TARGET_BASENAME}; found {len(targets)}")
        target = targets[0]

        candidate_labels = [
            i for i in infos
            if PurePosixPath(i.filename).suffix.lower() in LABEL_EXTS
            and PurePosixPath(i.filename).stem.lower() == "har6869"
        ]
        label_info = candidate_labels[0] if len(candidate_labels) == 1 else None

        # If the companion label is not named har6869.*, search metadata members only.
        # The scientific .tab member remains unopened.
        if label_info is None:
            referencing = []
            for info in infos:
                if PurePosixPath(info.filename).suffix.lower() not in LABEL_EXTS:
                    continue
                raw = zf.read(info.filename)
                opened_members.append(info.filename)
                if TARGET_BASENAME.encode("ascii") in raw.lower():
                    referencing.append((info, raw))
            if len(referencing) != 1:
                raise RuntimeError(f"could not identify unique official label for {TARGET_BASENAME}")
            label_info, label_raw = referencing[0]
        else:
            label_raw = zf.read(label_info.filename)
            opened_members.append(label_info.filename)

        if PurePosixPath(label_info.filename).suffix.lower() == ".xml":
            schema = parse_xml_label(label_raw)
        else:
            schema = parse_pds3_label(label_raw)

        label_references_target = TARGET_BASENAME.encode("ascii") in label_raw.lower()
        declared = schema["declared_record_counts"]
        declared_record_gate = (not declared) or (EXPECTED_PUBLIC_RECORDS in declared)
        fields = schema["fields"]
        named_fields = [f for f in fields if f.get("name")]
        structural_schema_gate = len(named_fields) >= 10
        target_never_opened = target.filename not in opened_members

        result = {
            "verdict": "PASS_HARVARD_1968_1969_STRUCTURE_AUDIT" if all((
                label_references_target,
                declared_record_gate,
                structural_schema_gate,
                target_never_opened,
            )) else "FAIL_HARVARD_1968_1969_STRUCTURE_AUDIT",
            "source_url": URL,
            "bundle_sha256": sha256_file(archive),
            "bundle_member_count": len(infos),
            "target_member": {
                "path": target.filename,
                "compressed_size": target.compress_size,
                "uncompressed_size": target.file_size,
                "opened": False,
            },
            "label_member": label_info.filename,
            "label_references_target": label_references_target,
            "declared_record_counts": declared,
            "expected_public_record_count": EXPECTED_PUBLIC_RECORDS,
            "declared_record_gate": declared_record_gate,
            "table_types": schema["table_types"],
            "schema_field_count": len(fields),
            "schema_fields": fields,
            "structural_schema_gate": structural_schema_gate,
            "opened_metadata_members": opened_members,
            "target_table_member_opened": not target_never_opened,
            "scientific_event_values_inspected": False,
            "scientific_event_values_persisted": False,
            "source_or_shower_labels_inspected": False,
            "method_evaluation_performed": False,
            "orbittrace_target_information_access": False,
            "claim_boundary": (
                "PDS bundle structure and official label metadata only. The har6869.tab member was located via the ZIP central directory but never opened or decompressed. "
                "No event value was interpreted. This result may only be used to freeze the later scientific parser/protocol."
            ),
        }

    # Remove the downloaded scientific bundle before artifact upload so no event data leave this job.
    archive.unlink()
    out = args.output / "harvard_1968_1969_structure_audit.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"].startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
